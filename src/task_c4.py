import os

from src.task_c1 import get_number_of_phrases_detected


def run_c1_whole_dataset(folder_path: str = "asap-dataset/"):
    """
    Run task C1 for the whole dataset
    :param folder_path: path to the dataset
    :return: a dictionary with the number of phrases detected for each piece
    """
    paths = []
    for root, dirs, files in os.walk(folder_path):
        if root in paths:
            continue
        for file in files:
            if file.endswith("midi_score_annotations.txt"):
                paths.append(root.replace("\\", "/"))
                break
    results = {}
    for path in paths:
        try:
            nb_measures = get_number_of_measures(path)
            nb_phrases = get_number_of_phrases_detected(path)
            results[path.replace("asap-dataset/", "")] = {
                "nb_phrases": nb_phrases,
                "nb_measures": nb_measures,
                "approx_ratio": nb_measures / 8
            }
        except Exception as e:
            print(f"Error for {path}: {e}")
            results[path.replace("asap-dataset/", "")] = "Error"
    return results


def get_number_of_measures(folder_path: str):
    """
    Get the number of measures for a piece
    :param folder_path: path to the piece folder
    :return: int
    """
    file = folder_path + "/midi_score_annotations.txt"
    count = 0
    with open(file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if "db" in line:
                count += 1
    return count
