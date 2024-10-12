import os

import music21


def extract_intervals_and_durations(midi_file_path) -> dict:
    """
    Extract intervals and durations from a MIDI file.
    """
    midi_data = music21.converter.parse(midi_file_path)
    pitches = {}
    for n in midi_data.recurse().notes:
        if n.isNote:
            if (n.measureNumber, n.offset) not in pitches:
                pitches[(n.measureNumber, n.offset)] = {
                    'pitch': {n.pitch.midi},
                    'duration': n.duration.quarterLength
                }
            else:
                pitches[(n.measureNumber, n.offset)]['pitch'].add(n.pitch.midi)
        elif n.isChord:
            if (n.measureNumber, n.offset) not in pitches:
                pitches[(n.measureNumber, n.offset)] = {
                    'pitch': {p.midi for p in n.pitches},
                    'duration': n.duration.quarterLength
                }
            else:
                pitches[(n.measureNumber, n.offset)]['pitch'].update({p.midi for p in n.pitches})

    # Calculate the interval (difference) between pitches
    pitches_with_intervals = {}
    last_pitch = None
    for onset, pitch in pitches.items():
        if onset == (1, 0) or last_pitch is None:
            pitches_with_intervals[onset] = {
                'pitch': pitch['pitch'],
                'root': min(pitch['pitch']),
                'interval': None,
                'duration': pitch['duration']
            }
        else:
            pitches_with_intervals[onset] = {
                'pitch': pitch['pitch'],
                'root': min(pitch['pitch']),
                'interval': min(pitch['pitch']) - last_pitch,
                'duration': pitch['duration']
            }
        last_pitch = min(pitch['pitch'])
    return pitches_with_intervals


def find_repeating_sequences(data, key):
    sequence = []
    positions = []
    durations = []

    # Concatenate sequences, positions, and durations from all measures
    for (measure, offset), value in sorted(data.items()):
        sequence.append(value[key])
        positions.append((measure, offset))
        durations.append(value['duration'])

    # Function to find repeating patterns with their positions
    def find_patterns_with_positions(seq, pos, dur):
        n = len(seq)
        patterns = []
        seen = {}
        for i in range(n):
            for length in range(1, n - i):
                pattern = tuple(seq[i:i + length])
                if pattern in seen:
                    first_occurrence = seen[pattern]
                    if i - first_occurrence[0] >= length:
                        total_duration = sum(dur[first_occurrence[0]:first_occurrence[0] + length])
                        if total_duration >= 6.0:
                            if pattern not in [p[0] for p in patterns]:
                                patterns.append((pattern, [first_occurrence[1]]))
                            for pat in patterns:
                                if pat[0] == pattern:
                                    pat[1].append(pos[i])
                else:
                    seen[pattern] = (i, pos[i])
        return patterns

    # Function to remove sub-patterns
    def remove_sub_patterns(patterns):
        patterns.sort(key=lambda x: len(x[0]), reverse=True)
        filtered_patterns = []
        for i, (pattern, positions) in enumerate(patterns):
            is_sub_pattern = False
            for longer_pattern, _ in filtered_patterns:
                if len(pattern) < len(longer_pattern):
                    for j in range(len(longer_pattern) - len(pattern) + 1):
                        if pattern == longer_pattern[j:j + len(pattern)]:
                            is_sub_pattern = True
                            break
            if not is_sub_pattern:
                filtered_patterns.append((pattern, positions))
        return filtered_patterns

    # Collect repeating sequences with positions
    patterns = find_patterns_with_positions(sequence, positions, durations)
    filtered_patterns = remove_sub_patterns(patterns)

    return filtered_patterns


def get_boundaries(midi_file_path):
    """
    Get boundaries for repeating patterns in a MIDI file.
    :param midi_file_path:
    :return:
    """
    data = extract_intervals_and_durations(midi_file_path)
    repeating_intervals = find_repeating_sequences(data, 'interval')
    repeating_root = find_repeating_sequences(data, 'root')
    repeating_durations = find_repeating_sequences(data, 'duration')
    boundaries = []
    for pattern, start_pos in repeating_intervals:
        boundaries.extend(start_pos)
    for pattern, start_pos in repeating_root:
        boundaries.extend(start_pos)
    for pattern, start_pos in repeating_durations:
        boundaries.extend(start_pos)
    boundaries = list(set(boundaries))
    boundary_results = set()
    for (measure, offset) in boundaries:
        for result in boundary_results:
            if abs(result - measure) < 2:
                break
        else:
            boundary_results.add(measure)
    return sorted(boundary_results)


def list_midi_files(base_path):
    """
    List all MIDI files in a directory and its subdirectories.
    :param base_path:
    :return:
    """
    midi_paths = []
    # Specify exact filenames to search for
    target_files = ['midi_score.mid', 'midi_score.midi']
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file in target_files:
                midi_paths.append(os.path.join(root, file).replace('\\', '/'))
    return midi_paths


def get_number_of_measures(midi_file_path):
    """
    Get the number of measures in a MIDI file.
    :param midi_file_path:
    :return:
    """
    midi_data = music21.converter.parse(midi_file_path)
    return len(midi_data.parts[0].getElementsByClass('Measure'))


def run_on_whole_dataset(base_path: str = '../asap-dataset/Bach') -> dict:
    """
    Run the functions on the whole dataset.
    :param base_path: path to the dataset
    :return results: dict
    """
    midi_files = list_midi_files(base_path)
    results = {}
    for midi_file in midi_files:
        try:
            boundaries = get_boundaries(midi_file)
            print(f"MIDI File: {midi_file}")
            nb_measures = get_number_of_measures(midi_file)
            results[midi_file] = {
                'boundaries': boundaries,
                "nb_boundaries": len(boundaries),
                "nb_measures": nb_measures,
                "approx_ratio": nb_measures / 8
            }
        except Exception as e:
            print(f"Error for {midi_file}: {e}")
    print("AVERAGE RATIO:",
          sum([value["nb_boundaries"] / value['approx_ratio'] for value in results.values()]) / len(results))
    return results


def plot_results(results: dict):
    """
    Plot the results as a line chart with the number of boundaries for each piece and the approximate ratio.
    :param results:
    :return:
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_theme()
    fig, ax = plt.subplots()
    ax.plot([value["approx_ratio"] for value in results.values()], label='Approximate Ratio', linewidth=0.8)
    ax.plot([value["nb_boundaries"] for value in results.values()], label='Number of Boundaries', linewidth=0.8)
    ax.set(xlabel='Piece', ylabel='Value',
           title='Number of Boundaries vs Approximate Ratio')
    plt.show()
