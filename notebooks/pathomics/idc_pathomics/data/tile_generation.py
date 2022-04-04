import os
from glob import glob 
import numpy as np
import pandas as pd
import re
from wsidicom import WsiDicom
from pydicom import config 
config.enforce_valid_values = False
from wsidicom.geometry import SizeMm
from PIL.Image import Image
import subprocess
from datetime import datetime
from typing import Tuple
 


def generate_tiles(slides_folder: str, metadata_path: str, output_folder: str, google_cloud_project_id: str, pixel_spacing: float=2.1, tile_size: int=128, every_xth_tile: int=1) -> None:
    """ 
    Run tiling for each slide separately. If tiles for the respective slide are already present, the slide is skipped. 
    Args:
        slides_folder (str): absolute path to the folder containing the slides. 
        metadata_path (str): absolute path to the metadata file. 
        output_folder (str): absolute path to the output folder. A separate subfolder containing the tiles will be created for every slide.
        google_cloud_project_id (str): ID of the Google Cloud Project used. 
        pixel_spacing (float): required pixel spacing in µm/px e.g. 2.1 for 5x resolution. Default 2.1. 
        tile_size (int): required tile size of the quadratic tiles in px e.g. 128. Default 128. 
        every_xth_tile (int): don't look at every tile, but only every x-th one. Should be set to 1 if all tiles should be considered. Default: 1. 
    Returns:
        None
    """

    if not os.path.exists(slides_folder):
        os.makedirs(slides_folder)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    slides_metadata = pd.read_csv(metadata_path)
    num_slides = len(slides_metadata)
    for idx, row in slides_metadata.iterrows():
        print('%s/%s' %(idx+1, num_slides))
        path_to_slide = _get_path_to_slide_from_gcs_url(row['gcs_url'], slides_folder) 
        slide_id = row['slide_id']
        gcs_url = row['gcs_url']
        _generate_tiles_for_slide(path_to_slide, slide_id, gcs_url, output_folder, google_cloud_project_id, pixel_spacing, tile_size, every_xth_tile)


def _generate_tiles_for_slide(path_to_slide: str, slide_id: str, gcs_url: str, output_folder: str, google_cloud_project_id: str, pixel_spacing: float, tile_size: int, every_xth_tile: int) -> None:
    # Check if slide is already tiled
    output_dir_tiles = os.path.join(output_folder, slide_id) 
    if os.path.exists(output_dir_tiles):
        print('Slide %s already downloaded and tiled' % slide_id)
        return
    
    # Download slide in DICOM format using gsutil
    print('Downloading slide %s - %s' %(slide_id, datetime.now()))
    cmd = ['gsutil -u {id} cp {url} {local_dir}'.format(id=google_cloud_project_id, url=gcs_url, local_dir=os.path.dirname(path_to_slide))]
    subprocess.run(cmd, shell=True)

    # Open slide and find the level closest to the required pixel spacing  
    print('Processing slide %s - %s' %(slide_id, datetime.now()))

    try:
        slide = WsiDicom.open(path_to_slide)
        level = _get_closest_level_by_pixel_spacing(slide, pixel_spacing) 
    except: 
        print('Some processing error for slide %s. Moving to the next slide.' %(slide_id))
        os.remove(path_to_slide)
        return 
    
    # Tiling 
    os.makedirs(output_dir_tiles) 
    cols, rows = _get_nr_cols_and_rows(slide, level) # get number of tiles in this level as (nr_tiles_xAxis, nr_tiles_yAxis)
    
    tuples = [(row,col) for row in range(1, rows) for col in range(1, cols)] # skip first row and colum (always background) 
    for (row, col) in tuples[::every_xth_tile]:
        tilename = os.path.join(output_dir_tiles, '%d_%d.%s' %(col, row, 'jpeg'))
        if not os.path.exists(tilename):
            wsidicom_tile = slide.read_tile(level, tile=(col, row)) 
            if wsidicom_tile.size[0] == wsidicom_tile.size[1]: # only consider quadratic tiles
                if (wsidicom_tile.size[0] != tile_size): 
                    tile = wsidicom_tile.resize((tile_size,tile_size))
                else: 
                    tile = wsidicom_tile
                # only store tile if there is enough amount of information, i.e. < 50 % background and the tile size is alright
                avg_bkg = _get_amount_of_background(tile)
                if avg_bkg <= 0.5:  
                    tile.save(tilename, quality=90)

    # After tiling delete the WSI to save disk space
    os.remove(path_to_slide)


def _get_path_to_slide_from_gcs_url(gcs_url: str, slides_folder: str) -> str:
    filename = os.path.basename(gcs_url)
    return os.path.join(slides_folder, filename)


def _get_closest_level_by_pixel_spacing(slide: WsiDicom, pixel_spacing: float) -> int: 
    wsidicom_level = slide.levels.get_closest_by_pixel_spacing(SizeMm(pixel_spacing/1000., pixel_spacing/1000.))
    return wsidicom_level.level # return level as integer


def _get_nr_cols_and_rows(slide: WsiDicom, level: int) -> Tuple[int, int]: 
    tiled_size = str(slide.levels.get_level(level).default_instance.tiled_size)
    cols_str = tiled_size.split(',')[0]
    cols = re.search(r'[0-9]{1,}', cols_str)[0]
    rows_str = tiled_size.split(',')[1]
    rows = re.search(r'[0-9]{1,}', rows_str)[0]
    return (int(cols), int(rows))


def _get_amount_of_background(tile: Image) -> float:
    grey = tile.convert(mode='L') 
    thresholded = grey.point(lambda x: 0 if x < 220 else 1, mode='F') 
    avg_bkg = np.average(np.array(thresholded))
    return avg_bkg   