import numpy as np
import copy
import matplotlib
import matplotlib.pyplot as plt
from typing import List

from .predictions import Predictions 


def generate_heatmap(predictions: Predictions, slide_id: str, colormap_strings: List[str] = ['Greys', 'Oranges', 'Blues']) -> None:
    pred = predictions.get_predictions_for_slide(slide_id)
    coord = predictions.get_tile_positions_for_slide(slide_id)
    max_cols = max([c[0] for c in coord]) + 1
    max_rows = max([c[1] for c in coord]) + 1
    colormaps = _get_colormaps(colormap_strings)

    slide_heatmap = -1 * np.ones((max_rows, max_cols, 4)) # initialize heatmap with -1
    for c, p in zip(coord, pred):
        p = p.tolist()
        colormap_to_use = colormaps[p.index(max(p))] 
        slide_heatmap[c[1], c[0], :] = colormap_to_use(max(p))
    
    return slide_heatmap


def _get_colormaps(colormap_strings: List[str]) -> List[matplotlib.colors.Colormap]:
    colormaps = []
    for cstring in colormap_strings:
        cmap = copy.copy(plt.cm.get_cmap(cstring))
        cmap.set_over(alpha=0)
        cmap.set_under(alpha=0)
        colormaps.append(cmap)
    return colormaps


def plot_colormap_legend(colormap_strings: List[str] = ['Greys', 'Oranges', 'Blues'], labels: List[str] = ['normal', 'LUAD', 'LSCC']):
    fig, ax = plt.subplots(3, figsize=(1.5, 1), subplot_kw=dict(xticks=[], yticks=[]))
    cmaps = _get_colormaps(colormap_strings)
    for i, cmap in enumerate(cmaps):
        colors = cmap(np.arange(cmap.N))
        ax[i].imshow([colors], extent=[0, 11, 0, 1])
        ax[i].yaxis.set_label_position('right')
        ax[i].set_ylabel(labels[i], rotation='horizontal', labelpad=25, va='center')