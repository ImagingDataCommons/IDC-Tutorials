import os
import pandas as pd
from typing import Any, Dict

def _get_reference_class_label(slide_metadata: pd.DataFrame) -> str:
    """
    Gets the reference class label of a certain slide.

    Parameters
    ----------
    slide_metadata: pd.DataFrame
        One-row dataframe containing metadata of the slide of interest

    Returns
    -------
    str
        String describing the tissue type ('normal', 'luad', 'lssc')
    """ 
    tissue_type = slide_metadata['tissue_type']
    if tissue_type == 'normal':
        return tissue_type
    else: 
        return slide_metadata['cancer_subtype']


def create_slides_metadata(bq_results_df: pd.DataFrame, local_slides_dir: str) -> Dict[str, Any]: 
    """
    Builds a dataframe comprising all slides' metadata. 

    Parameters
    ----------
    bq_results_df: pd.DataFrame
        Dataframe obtained from BigQuery. Contains one DICOM series per row.  

    Returns
    -------
    pd.DataFrame
        Slides metadata table with one row per slide. 
    """
    slides_metadata = dict()

    for index, row in bq_results_df.iterrows():
        slide_metadata = row.to_dict()
        image_id = slide_metadata['digital_slide_id']
        
        if not image_id in slides_metadata:
            slides_metadata[image_id] = slide_metadata
            local_path = os.path.join(local_slides_dir, image_id)
            slides_metadata[image_id]['local_path'] = local_path
            slides_metadata[image_id]['reference_class_label'] = _get_reference_class_label(slide_metadata)
            

    return pd.DataFrame.from_records(list(slides_metadata.values()),
                                     index=list(slides_metadata.keys()))