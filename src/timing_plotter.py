"""
This module contains functions used to plot the results for Task A.

@Author: Joris Monnet
@Date: 2024-03-26
"""

import matplotlib.pyplot as plt
import seaborn as sns


def plot_timing_for_one_piece(tempo_map: dict, boundaries:list[int]):
    """
    Plot the tempo curve from the dict of tempo ratios (for one piece) with each beat as x-axis
    :param tempo_map: dict
    :return: None
    """
    fig, ax = plt.subplots()
    ax.plot(list(tempo_map.keys()), list(tempo_map.values()), linewidth=0.8)
    # Plot boundaries as vertical lines
    for boundary in boundaries:
        ax.axvline(x=boundary, color='r', linestyle='--', linewidth=0.5)
    ax.set(xlabel='Beats', ylabel='Tempo Ratio',
           title='Tempo curve')
    plt.grid(True)
    plt.show()