"""
This module contains functions to get the timing attributes for multiple pieces
by averaging the timing attributes for each beat of a meter.

@Author: Joris Monnet
@Date: 2024-03-26
"""
import os

import matplotlib.pyplot as plt
import music21

from src.timing_for_one_piece import get_average_timing_one_piece


def get_tempo_map_db(symbolic_to_performed_times: dict) -> dict and list[int]:
    """
    Get the tempo map from the symbolic to the performed times
    Compute the tempo ratio for each beat
    :param symbolic_to_performed_times:
    :return: dict
    """
    result = {}
    indexes = []
    for i in range(len(symbolic_to_performed_times) - 1):
        beat_type = symbolic_to_performed_times[i]["performed"]["beat_type"]
        if beat_type == "db":
            indexes.append(i)
        onset = symbolic_to_performed_times[i]["performed"]["onset"]
        next_onset = symbolic_to_performed_times[i + 1]["performed"]["onset"]
        duration_performed = float(next_onset) - float(onset)
        onset_symbolic = symbolic_to_performed_times[i]["symbolic"]["onset"]
        next_onset_symbolic = symbolic_to_performed_times[i + 1]["symbolic"]["onset"]
        duration_symbolic = float(next_onset_symbolic) - float(onset_symbolic)
        result[i] = duration_symbolic / duration_performed
    if symbolic_to_performed_times[len(symbolic_to_performed_times) - 1]["performed"]["beat_type"] == "db":
        indexes.append(len(symbolic_to_performed_times) - 1)
    return result, indexes


def get_phrase_boundaries(path: str):
    """
    Get the phrase boundaries from the tempo map
    :param path:
    :return:
    """
    average = get_average_timing_one_piece(path)
    tempo_map, indexes_db = get_tempo_map_db(average)

    phrase_boundaries = []
    for i in range(len(tempo_map)):
        if i in indexes_db:
            current_index = indexes_db.index(i)
            if current_index == 0:
                phrase_boundaries.append(i)
                continue
            last_db = indexes_db[current_index - 1]
            if current_index == len(indexes_db) - 1:
                phrase_boundaries.append(i)
                continue
            next_db = indexes_db[current_index + 1]
            last_measure = list(tempo_map.values())[last_db:i]
            next_measure = list(tempo_map.values())[i:next_db]
            # -1 if the tempo is decreasing, 1 if the tempo is increasing inside the measure
            last_measure_change = 0
            for j in range(len(last_measure) - 1):
                last_measure_change += last_measure[j + 1] - last_measure[j]
            last_measure_change = last_measure_change / len(last_measure)
            next_measure_change = 0
            for j in range(len(next_measure) - 1):
                next_measure_change += next_measure[j + 1] - next_measure[j]
            next_measure_change = next_measure_change / len(next_measure)
            # Check if sign of tempo change is different
            if last_measure_change * next_measure_change < 0:
                # Phrase boundary if the tempo is increasing inside the new measure
                if next_measure_change > 0:
                    phrase_boundaries.append(i)
    boundaries_time = get_time_of_phrase_boundaries(phrase_boundaries, average)
    return phrase_boundaries, boundaries_time


def get_time_of_phrase_boundaries(phrase_boundaries: list[int], average: dict):
    """
    Get the time of the phrase boundaries
    :param phrase_boundaries:
    :param average:
    :return:
    """
    boundaries_time = []
    for boundary in phrase_boundaries:
        boundaries_time.append(float(average[boundary]["performed"]["onset"]))
    return boundaries_time


def get_times_volumes_measures(midi_file_path: str) -> tuple:
    """
    Extracts the start times, velocity values (volume), and measure numbers of each note from a MIDI file.

    Parameters:
    midi_file_path (str): The path to the input MIDI file.
    
    Returns:
    times (list of float): A list containing the start times of all the notes in the MIDI file.
    volumes (list of int): A list containing the velocity values of all the notes in the MIDI file.
    measures (list of int): A list containing the measure numbers of all the notes in the MIDI file.
    """
    midi_data = music21.converter.parse(midi_file_path)

    times = []
    volumes = []
    measures = []

    for part in midi_data.parts:
        for element in part.flatten().notesAndRests:
            if isinstance(element, music21.note.Note):
                start_time = element.offset
                velocity = element.volume.velocity
                measure_number = element.measureNumber
                times.append(start_time)
                volumes.append(velocity)
                measures.append(measure_number)
            elif isinstance(element, music21.chord.Chord):
                start_time = element.offset
                velocity = element.volume.velocity
                measure_number = element.measureNumber
                times.append(start_time)
                volumes.append(velocity)
                measures.append(measure_number)

    return times, volumes, measures


def get_scaled_differences_in_volumes(list_volume_performed: list) -> list:
    """
    Calculates the squared differences in volume between consecutive elements
    in the input list, and scales these differences to the range [0, 1].

    Parameters:
    list_volume_performed (list of int or float): A list of volume values.

    Returns:
    list_volume_differences_scaled (list of float): A list of scaled squared differences in volume, 
                                                     where the values are normalized to the range [0, 1].
    """
    list_volume_differences = [abs(list_volume_performed[i] - list_volume_performed[i + 1]) ** 2
                               for i in range(len(list_volume_performed) - 1)]
    max_difference = max(list_volume_differences)
    list_volume_differences_scaled = [x / max_difference for x in list_volume_differences]
    return list_volume_differences_scaled


def get_times_threshold(list_time: list, list_volume_differences_scaled: list, threshold: float) -> list:
    """
    Function to return the times when volume changes exceed a specified threshold.

    Args:
    list_time (list of float): List of times.
    list_volume_differences_scaled (list of float): List of scaled volume differences.
    threshold (float): The threshold value.

    Returns:
    list of float: List of times when volume changes exceed the threshold.
    """

    # List to store indices where the volume difference exceeds the threshold
    indices_above_threshold = [index for index, value in enumerate(list_volume_differences_scaled) if value > threshold]

    # List to store times corresponding to the indices above threshold
    times_above_threshold = [list_time[index] for index in indices_above_threshold]

    # Return the list of times when volume changes exceed the threshold
    return times_above_threshold


def offset_to_seconds(offset: float, tempo: float) -> float:
    """
    Converts a musical offset to seconds based on the given tempo.

    Args:
    offset (float): The musical offset in terms of quarter notes.
    tempo (float): The tempo in beats per minute (BPM).

    Returns:
    float: The equivalent time in seconds.
    """

    # Calculate the duration of one quarter note in seconds
    quarter_note_duration = 60 / tempo
    # Calculate and return the time in seconds for the given offset
    return offset * quarter_note_duration


def plot_volume(list_volume_performed: list[float], filtered_data: list[float], list_time: list[float], tempo: float):
    """
    Plots the scaled volume differences and highlights certain points with vertical lines.

    Args:
    list_volume_performed (list of float): List of performed volume values.
    filtered_data (list of float): List of offsets that need to be highlighted.
    list_time (list of float): List of time offsets.
    tempo (float): The tempo in beats per minute (BPM).
    """
    list_time_second = [offset_to_seconds(x, tempo) for x in list_time]
    list_filtered_second = [offset_to_seconds(x, tempo) for x in filtered_data]
    list_volume_differences_scaled = get_scaled_differences_in_volumes(list_volume_performed)
    plt.figure(figsize=(10, 6))
    plt.plot(list_time_second[:-2], list_volume_differences_scaled, linestyle='-', color='b')
    for x in list_filtered_second:
        plt.axvline(x=x, color='y', linestyle='--')
    plt.xlabel('Time[s]')
    plt.ylabel('Volume Differences Scaled ')
    plt.title('Volume Differences Scaled')
    plt.show()


def get_number_of_phrases_detected(path: str) -> int:
    """
    Merged model_p
    :param path:
    :return: number of phrases detected
    """
    boundaries, boundaries_times = get_phrase_boundaries(path)
    midi_path = ""
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".mid") and file != "midi_score.mid":
                midi_path = root + "/" + file
                break
    if midi_path == "":
        return 0
    midi_data = music21.converter.parse(midi_path)
    tempo = midi_data.metronomeMarkBoundaries()[0][2].number
    list_time, list_volumes, list_measures = get_times_volumes_measures(midi_path)
    list_volume_differences_scaled = get_scaled_differences_in_volumes(list_volumes)
    times_above_threshold_ = get_times_threshold(list_time, list_volume_differences_scaled, 0.15)
    times_above_threshold = [float(x) for x in times_above_threshold_]
    threshold_closest = 2

    filtered_data = [times_above_threshold[0]]
    for i in range(1, len(times_above_threshold)):
        if times_above_threshold[i] - filtered_data[-1] > threshold_closest:
            filtered_data.append(times_above_threshold[i])

    split_point = [offset_to_seconds(x, tempo) for x in filtered_data]

    potential_split_point = [split_point[0]]
    for point in split_point:
        for p in potential_split_point:
            if abs(p - point) < 5:
                break
        else:
            potential_split_point.append(point)

    result_boundaries = []
    boundaries_to_times = {}
    for i in range(len(boundaries)):
        boundaries_to_times[boundaries_times[i]] = boundaries[i]

    threshold_similarity = 5
    min_velocity = min(split_point) - threshold_similarity
    max_velocity = max(split_point) + threshold_similarity

    for point in split_point:
        for boundaries_time in boundaries_times:
            if abs(boundaries_time - point) < threshold_similarity and boundaries_time not in result_boundaries:
                result_boundaries.append(boundaries_time)
                break
            elif boundaries_time < min_velocity and boundaries_time not in result_boundaries:
                result_boundaries.append(boundaries_time)
                break
            elif boundaries_time > max_velocity and boundaries_time not in result_boundaries:
                result_boundaries.append(boundaries_time)
                break

    return len(result_boundaries)
