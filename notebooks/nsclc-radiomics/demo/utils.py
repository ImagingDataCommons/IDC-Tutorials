"""
    ----------------------------------------
    IDC Radiomics use case (Colab)
    
    Functions for data viz and more
    ----------------------------------------
    
    ----------------------------------------
    Author: Dennis Bontempi
    Email:  dbontempi@bwh.harvard.edu
    ----------------------------------------
    
"""

import numpy as np

# ----------------------------------------

# everything that has to do with plotting goes here below
import seaborn as sns

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

from matplotlib.colors import ListedColormap

## ----------------------------------------

# Create new colormap appending the alpha channel to the selected one
# so that we don't get a "color overlay" when plotting the segmask over the CT image
cmap = plt.cm.Reds
my_reds = cmap(np.arange(cmap.N))
my_reds[:,-1] = np.linspace(0, 1, cmap.N)
my_reds = ListedColormap(my_reds)

cmap = plt.cm.jet
my_jet = cmap(np.arange(cmap.N))
my_jet[:,-1] = np.linspace(0, 1, cmap.N)
my_jet = ListedColormap(my_jet)

## ----------------------------------------

## ----------------------------------------
## ----------------------------------------


def export_png_slice(input_volume, input_segmask, fig_out_path, fig_dpi = 220,
                     lon_slice_idx = 0, cor_slice_idx = 0, sag_slice_idx = 0, z_first = True):
  
  """
  This function exports a PNG figure with 3 slices of the input volume and the corresponding segmentation mask.

  Parameters:
    - input_volume: a 3D numpy array representing the image to be normalized.
    - input_segmask: a 3D numpy array representing the segmentation mask.
    - fig_out_path: the path where the figure will be saved.
    - fig_dpi: the resolution of the figure.
    - lon_slice_idx: the index of the longitudinal slice to be exported.
    - cor_slice_idx: the index of the coronal slice to be exported.
    - sag_slice_idx: the index of the sagittal slice to be exported.

  Returns:
    - 0 if everything went well. 
  """

  idx_x1 = cor_slice_idx
  idx_x0 = lon_slice_idx if z_first else sag_slice_idx
  idx_x2 = sag_slice_idx if z_first else lon_slice_idx
  
  x1_view_str = 'cor'
  x0_view_str = 'lon' if z_first else 'sag'
  x2_view_str = 'sag' if z_first else 'lon'
  
  vol_slice_x0 = input_volume[idx_x0, :, :]
  seg_slice_x0 = input_segmask[idx_x0, :, :]

  vol_slice_x1 = input_volume[:, idx_x1, :]
  seg_slice_x1 = input_segmask[:, idx_x1, :]

  vol_slice_x2 = input_volume[:, :, idx_x2]
  seg_slice_x2 = input_segmask[:, :, idx_x2]

# ----------------------------------------

  fig, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(12, 12), dpi = fig_dpi)

  ax0.imshow(vol_slice_x0, cmap = 'gray', vmin = np.min(vol_slice_x0), vmax = np.max(vol_slice_x0))
  ax0.imshow(seg_slice_x0, cmap = my_reds, alpha = 0.6)
  ax0.set_title('CoM CT slice (%s) + GTV mask'%(x0_view_str))

  ax1.imshow(vol_slice_x1, cmap = 'gray', vmin = np.min(vol_slice_x1), vmax = np.max(vol_slice_x1))
  ax1.imshow(seg_slice_x1, cmap = my_reds, alpha = 0.6)
  ax1.set_title('CoM CT slice (%s) + GTV mask'%(x1_view_str))

  ax2.imshow(vol_slice_x2, cmap = 'gray', vmin = np.min(vol_slice_x2), vmax = np.max(vol_slice_x2))
  ax2.imshow(seg_slice_x2, cmap = my_reds, alpha = 0.6)
  ax2.set_title('CoM CT slice (%s) + GTV mask'%(x2_view_str))

  print('\nExporting figure at:', fig_out_path)
  fig.savefig(fig_out_path)
  plt.close(fig)

  return 0

## ----------------------------------------
## ----------------------------------------
