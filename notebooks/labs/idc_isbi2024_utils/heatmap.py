import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Colormap
from copy import copy
from typing import List
from .predictions import Predictions
from .global_variables import CLASS_LABEL_TO_INDEX_MAP, NUM_CLASSES

def generate_heatmap(predictions: Predictions, image_id: str, colormap_strings: List[str] = ['Greys', 'Oranges', 'Blues']) -> np.ndarray:
    """
    Generates a heatmap of a certain slide.      
    
    Parameters
    ---------- 
    predictions: Predictions
        Predictions object to work with.
    image_id: str
        Image ID of the slide for which a heatmap should be generated.
    colormap_strings: list
        List of color strings.
    
    Returns
    -------
    np.array
        Heatmap. 
    """ 
    image_predictions = predictions.get_results_of_image(image_id)
    pred = np.stack(image_predictions['predicted_class_probabilities'])
    coord = np.stack(image_predictions['tile_position'])
    max_cols = max([c[0] for c in coord]) + 1
    max_rows = max([c[1] for c in coord]) + 1
    colormaps = _get_colormaps(colormap_strings)

    slide_heatmap = np.zeros((max_rows, max_cols, 4)) # initialize heatmap with 0
    for c, p in zip(coord, pred):
        p = p.tolist()
        max_p = max(p)
        colormap_to_use = colormaps[p.index(max_p)] 
        slide_heatmap[c[1], c[0], :] = colormap_to_use(max_p)

    return slide_heatmap


def _get_colormaps(colormap_strings: List[str]) -> List[Colormap]:
    """
    Obtains a bright-to-dark Colormap object for each color in 
    a given list of color strings.      
    
    Parameters
    ---------- 
    colormap_strings: list
        List of color strings.
    
    Returns
    -------
    list
        List of colormap objects. 
    """
    colormaps = []
    for cstring in colormap_strings:
        cmap = copy(matplotlib.colormaps[cstring])
        cmap.set_over(alpha=0)
        cmap.set_under(alpha=0)
        colormaps.append(cmap)
    return colormaps


def plot_colormap_legend(colormap_strings: List[str] = ['Greys', 'Oranges', 'Blues'], labels: List[str] = list(CLASS_LABEL_TO_INDEX_MAP.keys())):
    """
    Plots a color legend to the heatmap.     
    
    Parameters
    ---------- 
    colormap_strings: list
        List of color strings.
    labels: list
        List of labels with one label for each color string. 
    """
    fig, ax = plt.subplots(3, figsize=(1.5, 1), subplot_kw=dict(xticks=[], yticks=[]))
    cmaps = _get_colormaps(colormap_strings)
    for i, cmap in enumerate(cmaps):
        colors = cmap(np.arange(cmap.N))
        ax[i].imshow([colors], extent=[0, 11, 0, 1])
        ax[i].yaxis.set_label_position('right')
        ax[i].set_ylabel(labels[i], rotation='horizontal', labelpad=25, va='center')
    return None