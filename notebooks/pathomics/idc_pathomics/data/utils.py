import os
import pandas as pd
import subprocess
from openslide import open_slide
from multiprocessing import Process
from typing import List

from .tile_generation import _get_path_to_slide_from_gcs_url


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
        _get_thumbnail_in_process(slide_id, slides_metadata, output_folder, google_cloud_project_id)


# Workaround for a potential memory leak in Openslide 
def _get_thumbnail_in_process(slide_id: str, slides_metadata: pd.DataFrame, output_folder: str, google_cloud_project_id: str) -> None:
    p = Process(target=_get_thumbnail, args=(slide_id, slides_metadata, output_folder, google_cloud_project_id))
    p.start()
    p.join()


def _get_thumbnail(slide_id: str, slides_metadata: pd.DataFrame, output_folder: str, google_cloud_project_id: str) -> None:  
    gcs_url = slides_metadata[slides_metadata['slide_id']==slide_id]['gcs_url'].item()
    # Download slide
    path_to_slide = _get_path_to_slide_from_gcs_url(gcs_url, output_folder) 
    cmd = ['gsutil -u {id} cp {url} {local_dir}'.format(id=google_cloud_project_id, url=gcs_url, local_dir=os.path.dirname(path_to_slide))]
    subprocess.run(cmd, shell=True)
    # Open slide and generate thumbnail. Afterwards delete the slide.
    slide = open_slide(path_to_slide)
    thumbnail = slide.get_thumbnail((300,300)) # get and save thumbnail image
    thumbnail.save(os.path.join(os.path.dirname(path_to_slide), slide_id + '.png'))
    os.remove(path_to_slide)


