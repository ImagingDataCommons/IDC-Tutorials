"""
    ----------------------------------------
    IDC Radiomics use case (Colab Demo)
    
    useful functions for data handling/proc
    ----------------------------------------
    
    ----------------------------------------
    Author: Dennis Bontempi
    Email:  dennis_bontempi@dfci.harvard.edu
    Modified: 01 OCT 20
    ----------------------------------------
    
"""

import os
import json
import pydicom
import numpy as np
import SimpleITK as sitk

## ----------------------------------------

# normalise the values of the volume between new_min_val and new_max_val
def normalise_volume(input_volume, new_min_val, new_max_val, old_min_val = None, old_max_val = None):

  """
  Normalise a numpy volume intensity in a range between two given values
  
  @params:
    input_volume - required : numpy volume to rescale (intensity-wise) in the new range.
    new_min_val  - required : the lower bound of the new intensity range.
    new_max_val  - required : the upper bound of the new intensity range.
    old_min_val  - optional : the lower bound of the old intensity range. Defaults to input_volume's np.min()
    old_max_val  - optional : the lower bound of the old intensity range. Defaults to input_volume's np.max()
    
  """
  
  # make sure the input volume is treated as a float volume
  input_volume = input_volume.astype(dtype = np.float16)

  # if no old_min_val and/or old_max_val are specified, default to the np.min() and np.max() of input_volume
  
  curr_min = np.min(input_volume) if old_min_val == None else old_min_val
  curr_max = np.max(input_volume) if old_max_val == None else old_max_val


  # normalise the values of each voxel between zero and one
  zero_to_one_norm = (input_volume - curr_min)/(curr_max - curr_min)

  # normalise between new_min_val and new_max_val
  return (new_max_val - new_min_val)*zero_to_one_norm + new_min_val

## ----------------------------------------
## ----------------------------------------

def compute_center_of_mass(input_mask):
  
  """
  Compute the center of mass (CoM) of a given binary 3D numpy segmask (fast version, numpy based).
  The idea is the following:
    - create a 4D vector starting from the 3D, populating each channel as follows:
      (x pos, y pos, z pos, mask_value);
    - keep only the nonzero values;
    - compute an average of the position (CoM) using such triplets (x, y, z).
  
  @params:
    input_mask - required : the 3D numpy vector (binary mask) to compute the center of mass of.
    
  @returns:
    ctr_mass - a list of three elements storing the coordinates of the CoM
               (the axes are the same as the input mask)
    
  """
  
  # sanity check: mask should be binary (multi-class RT is taken care of during in the export function)
  assert(len(np.unique(input_mask)) <= 2)
  
  # display and log warning
  if len(np.unique(input_mask)) == 1:
    print('WARNING: DICOM RTSTRUCT is empty.')
    return [-1, -1, -1]
  
  # clip mask values between 0 and 1 (e.g., to cope for masks with max val = 255)
  input_mask = np.clip(input_mask, a_min = 0, a_max = 1)
  
  segmask_4d = np.zeros(input_mask.shape + (4, ))

  # create a triplet of grids that will serve as axis for the next step
  y, x, z = np.meshgrid(np.arange(input_mask.shape[1]), 
                        np.arange(input_mask.shape[0]), 
                        np.arange(input_mask.shape[2]))
  
  # populate
  segmask_4d[..., 0] = x 
  segmask_4d[..., 1] = y 
  segmask_4d[..., 2] = z 
  segmask_4d[..., 3] = input_mask
  
  # keep only the voxels belonging to the mask
  nonzero_voxels = segmask_4d[np.nonzero(segmask_4d[:, :, :, 3])]

  # average the (x, y, z) triplets
  ctr_mass = np.average(nonzero_voxels[:, :3], axis = 0)
    
  return ctr_mass

  
## ----------------------------------------
## ----------------------------------------

def get_bbox_dict(int_center_of_mass, seg_mask_shape, bbox_size, z_first = True):

  """
  Compute the crop bounding box indices starting from the CoM and the BBox size.
  
  @params:
    int_center_of_mass - required : a list of integers (int(CoM)) where CoM is the output
                                    of the function "compute_center_of_mass()"
    bbox_size          - required : the size of the bounding box along each axis.
    z_first            - optional : if True, returns the dict as (lon, cor, sag), i.e., (z, y, x),
                                    as opposed to (sag, cor, lon), i.e., (x, y, z) (defaults to True).
  
  @returns:
    bbox : a dictionary formatted as follows:
      {
       'lon': {'first': 89, 'last': 139}
       'cor': {'first': 241, 'last': 291},
       'sag': {'first': 150, 'last': 200}
      }
  """
  
  assert len(int_center_of_mass) == 3
  assert len(bbox_size) == 3
    
  bbox = dict()

  bbox['cor'] = dict()
  bbox['sag'] = dict()
  bbox['lon'] = dict()

  # take care of axes shuffling 
  cor_idx = 1
  lon_idx = 0 if z_first else 2
  sag_idx = 2 if z_first else 0
  
  
  # bounding box if no exception is found
  sag_first = int(int_center_of_mass[sag_idx] - np.round(bbox_size[sag_idx]/2))
  sag_last = int(int_center_of_mass[sag_idx] + np.round(bbox_size[sag_idx]/2)) - 1
  
  cor_first = int(int_center_of_mass[cor_idx] - np.round(bbox_size[cor_idx]/2))
  cor_last = int(int_center_of_mass[cor_idx] + np.round(bbox_size[cor_idx]/2)) - 1
  
  lon_first = int(int_center_of_mass[lon_idx] - np.round(bbox_size[lon_idx]/2))
  lon_last = int(int_center_of_mass[lon_idx] + np.round(bbox_size[lon_idx]/2)) - 1
  

  # print out exceptions
  if sag_last > seg_mask_shape[sag_idx] - 1 or sag_first < 0:
    print('WARNING: the bounding box size exceeds volume dimensions (sag axis)')
    print('Cropping will be performed ignoring the "bbox_size" parameter')
    
  if cor_last > seg_mask_shape[cor_idx] - 1 or cor_first < 0:
    print('WARNING: the bounding box size exceeds volume dimensions (cor axis)')
    print('Cropping will be performed ignoring the "bbox_size" parameter')
    
  if lon_last > seg_mask_shape[lon_idx] - 1 or lon_first < 0:
    print('WARNING: the bounding box size exceeds volume dimensions (lon axis)')
    print('Cropping will be performed ignoring the "bbox_size" parameter')
    
    
  # take care of exceptions where bbox is bigger than the actual volume
  sag_first = int(np.max([0, sag_first]))
  sag_last = int(np.min([seg_mask_shape[sag_idx] - 1, sag_last]))
  
  cor_first = int(np.max([0, cor_first]))
  cor_last = int(np.min([seg_mask_shape[cor_idx] - 1, cor_last]))
  
  lon_first = int(np.max([0, lon_first]))
  lon_last = int(np.min([seg_mask_shape[lon_idx] - 1, lon_last]))
  
  
  # populate the dictionary and return it
  bbox['sag']['first'] = sag_first
  bbox['sag']['last'] = sag_last

  bbox['cor']['first'] = cor_first
  bbox['cor']['last'] = cor_last

  bbox['lon']['first'] = lon_first
  bbox['lon']['last'] = lon_last
    
  return bbox
  

## ----------------------------------------
## ----------------------------------------

def get_input_volume(input_ct_nrrd_path):

  """
  Should accept path to (ideally 150x150x150) NRRD volumes only, obtained
  exploting the pipeline in "lung1_preprocessing.ipynb" using the functions above.
  
  FIXME: add as params also "com_int" and "final_crop_size = (50, 50, 50)"
         (handling of volumes that are not 150x150x150?)
  
  """
  
  sitk_ct_nrdd = sitk.ReadImage(input_ct_nrrd_path)
  ct_nrdd = sitk.GetArrayFromImage(sitk_ct_nrdd)
      
  # volume intensity normalisation, as seen in:
  # https://github.com/modelhub-ai/deep-prognosis/blob/master/contrib_src/processing.py
  ct_nrdd_norm = normalise_volume(input_volume = ct_nrdd,
                                  new_min_val = 0,
                                  new_max_val = 1,
                                  old_min_val = -1024,
                                  old_max_val = 3071)
    
  # FIXME: handle exceptions for volumes that are not 150x150x150
  ct_nrdd_norm_crop = ct_nrdd_norm[50:100, 50:100, 50:100]
  
  """
  # FIXME: debug
  print(ct_nrdd.shape)
  print(ct_nrdd_norm.shape)
  print(min_x, max_x)
  print(min_y, max_y)
  print(min_z, max_z)
  print(ct_nrdd_norm_crop.shape)
  """
  
  return ct_nrdd_norm_crop