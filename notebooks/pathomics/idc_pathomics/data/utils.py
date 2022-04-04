import os
import pandas as pd
import subprocess
from wsidicom import WsiDicom
from pydicom import config 
config.enforce_valid_values = False
from typing import List

from .tile_generation import _get_path_to_slide_from_gcs_url


def get_required_or_next_higher_resolution_slides(slides_df: pd.DataFrame, pixel_spacing_low: float, pixel_spacing_up: float) -> pd.DataFrame: 
    """ If available take the slide with pixel_spacing_low < pixel_spacing < pixel_spacing_up, otherwise take next higher available resolution, i.e.
    the slide with the next lower pixel spacing """

    unique_slide_ids = slides_df['slide_id'].unique().tolist()
    slides_to_download = pd.DataFrame(columns = slides_df.columns)
    for slide_id in unique_slide_ids: 
        sub_df = slides_df[slides_df['slide_id'] == slide_id]
        slide_to_download = get_required_or_next_higher_resolution_slide(sub_df, pixel_spacing_low, pixel_spacing_up)
        slides_to_download = slides_to_download.append(slide_to_download)
    return slides_to_download


def get_required_or_next_higher_resolution_slide(df: pd.DataFrame, pixel_spacing_low: float, pixel_spacing_up: float) -> pd.DataFrame: 
    slide_with_required_pixel_spacing = df.query('pixel_spacing > @pixel_spacing_low & pixel_spacing < @pixel_spacing_up') 
    if len(slide_with_required_pixel_spacing) > 0: # get slide with required pixel spacing
        return slide_with_required_pixel_spacing
    else: # get slide with next lower pixel spacing
        df['diff'] = abs(df['pixel_spacing'] - pixel_spacing_low)
        slide_with_next_lower_pixel_spacing = df.query('pixel_spacing < @pixel_spacing_low & diff == diff.min()')
        slide_with_next_lower_pixel_spacing.drop(columns=['diff'], inplace=True)
        return slide_with_next_lower_pixel_spacing


def get_slide_tissue_type(slide_id: str, slides_metadata: pd.DataFrame) -> str:
    cancer_subtype = slides_metadata[slides_metadata['slide_id'] == slide_id]['cancer_subtype'].item()
    tissue_type = slides_metadata[slides_metadata['slide_id'] == slide_id]['tissue_type'].item()
    if tissue_type == 'normal':
        return tissue_type
    else: 
        return cancer_subtype


def get_random_testset_slide_ids(slides_metadata: pd.DataFrame) -> List[str]:
    ts = slides_metadata[slides_metadata['dataset'] == 'test']
    slide_ids = ts[ts['cancer_subtype']=='luad'].sample(n=2)['slide_id'].tolist()
    slide_ids.extend(ts[ts['cancer_subtype']=='lscc'].sample(n=2)['slide_id'].tolist())
    return slide_ids


def get_thumbnails(slide_ids: List[str], metadata_path: str, output_folder: str, google_cloud_project_id: str) -> None:
    slides_metadata = pd.read_csv(metadata_path)
    for slide_id in slide_ids: 
        print('Generate thumbnail for slide %s' %(slide_id))
        _get_thumbnail(slide_id, slides_metadata, output_folder, google_cloud_project_id)


def _get_thumbnail(slide_id: str, slides_metadata: pd.DataFrame, output_folder: str, google_cloud_project_id: str) -> None:  
    gcs_url = slides_metadata[slides_metadata['slide_id']==slide_id]['gcs_url'].item()
    # Download slide
    path_to_slide = _get_path_to_slide_from_gcs_url(gcs_url, output_folder) 
    cmd = ['gsutil -u {id} cp {url} {local_dir}'.format(id=google_cloud_project_id, url=gcs_url, local_dir=os.path.dirname(path_to_slide))]
    subprocess.run(cmd, shell=True)
    # Open slide and generate thumbnail. Afterwards delete the slide.
    slide = WsiDicom.open(path_to_slide)
    thumbnail = slide.read_thumbnail((300,300)) # get and save thumbnail image
    thumbnail.save(os.path.join(os.path.dirname(path_to_slide), slide_id + '.png'))
    os.remove(path_to_slide)


