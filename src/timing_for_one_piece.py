"""
This module contains functions to get the timing attributes for a single piece.
From ASSIGNMENT 1 - Task A

@Author: Joris Monnet
@Date: 2024-03-26
"""

import os


def get_performed_attributes(performed_path: str) -> dict:
    """
    Get the performed attributes for each beat
    :param performed_path: path to the annotation file with the performed times
    :return: dict of the performed attributes for each beat
    """
    result_performed = {}
    with open(performed_path, "r") as f:
        performed_data = f.readlines()
        current_key = None
        current_meter = None
        current_beat = 0
        for line in performed_data:
            line_data = line.split()
            beat_key_meter = line_data[2].split(',')
            beat_type = beat_key_meter[0]
            if len(beat_key_meter) == 3:
                current_meter = beat_key_meter[1]
                current_key = beat_key_meter[2]
            elif len(beat_key_meter) == 2:
                current_meter = beat_key_meter[1]

            result_performed[current_beat] = {
                "key": current_key,
                "meter": current_meter,
                "onset": line_data[0],
                "beat_type": beat_type
            }
            current_beat += 1
    return result_performed


def get_symbolic_attributes(symbolic_path: str) -> dict:
    """
    Get the symbolic attributes for each beat
    :param symbolic_path: path to the annotation file with the symbolic times
    :return: dict of the symbolic attributes for each beat
    """
    result_symbolic = {}
    with open(symbolic_path, "r") as f:
        unperformed_data = f.readlines()
        current_beat = 0
        for line in unperformed_data:
            line_data = line.split()
            result_symbolic[current_beat] = {
                "onset": line_data[0],
            }
            current_beat += 1
    return result_symbolic


def get_piece_symbolic_to_performed_times(symbolic_path: str, performed_path: str) -> dict:
    """
    Get the symbolic and performed times for a piece
    :param symbolic_path:  path to the annotation file with the symbolic times
    :param performed_path: path to the annotation file with the performed times
    :return: a dict containing the symbolic and performed times for each beat, with their meter, key and beat type
    """
    result_performed = get_performed_attributes(performed_path)
    result_symbolic = get_symbolic_attributes(symbolic_path)
    result = {}
    for key in result_performed:
        result[key] = {
            "symbolic": result_symbolic[key],
            "performed": result_performed[key]
        }
    return result


def get_tempo_map(symbolic_to_performed_times: dict) -> dict:
    """
    Get the tempo map from the symbolic to the performed times
    Compute the tempo ratio for each beat
    :param symbolic_to_performed_times:
    :return: dict
    """
    result = {}
    for i in range(len(symbolic_to_performed_times) - 2):
        onset = symbolic_to_performed_times[i]["performed"]["onset"]
        next_onset = symbolic_to_performed_times[i + 1]["performed"]["onset"]
        duration_performed = float(next_onset) - float(onset)
        onset_symbolic = symbolic_to_performed_times[i]["symbolic"]["onset"]
        next_onset_symbolic = symbolic_to_performed_times[i + 1]["symbolic"]["onset"]
        duration_symbolic = float(next_onset_symbolic) - float(onset_symbolic)
        tempo_performed = 1 / duration_performed
        tempo_symbolic = 1 / duration_symbolic
        result[i] = tempo_performed / tempo_symbolic
    return result


def get_average_timing_one_piece(folder_path: str) -> dict or None:
    """
    Get the attributes for each beat for a piece where the piece can have
    multiple performances
    :param folder_path: the path to the piece folder
    :return: dict
    """
    files = [file for file in os.listdir(folder_path) if file.endswith("annotations.txt")]
    files.remove("midi_score_annotations.txt")
    if len(files) == 0:
        print("No annotation files found")
        return
    if len(files) == 1:
        return get_piece_symbolic_to_performed_times(folder_path + "/midi_score_annotations.txt",
                                                     folder_path + "/" + files[0])

    # Case multiple files :
    # Get the symbolic times only once
    symbolic_times = get_symbolic_attributes(folder_path + "/midi_score_annotations.txt")
    performed_list = []
    for file in files:
        performed_list.append(get_performed_attributes(folder_path + "/" + file))

    # Average the onsets for each beat for performed times
    avg_performed = {}
    for i in range(len(symbolic_times)):
        onset_sum = 0
        for performed in performed_list:
            if i not in performed:
                continue
            onset_sum += float(performed[i]["onset"])
        avg_performed[i] = onset_sum / len(performed_list)

    result = {}
    for key in symbolic_times:
        result[key] = {
            "symbolic": symbolic_times[key],
            "performed": {
                "onset": avg_performed[key],
                "key": performed_list[0][key]["key"],
                "meter": performed_list[0][key]["meter"],
                "beat_type": performed_list[0][key]["beat_type"]
            }
        }
    return result
