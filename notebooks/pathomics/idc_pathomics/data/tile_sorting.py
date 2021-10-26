import os 
from glob import glob
from collections import defaultdict
import pandas as pd
from typing import Dict

from .utils import get_slide_tissue_type

SORTING_OPTIONS = {'norm_cancer': {'normal':0, 'luad':1, 'lscc':1}, 'luad_lscc': {'luad':0, 'lscc':1}, 'norm_luad_lscc': {'normal':0, 'luad':1, 'lscc':2}}


def sort_tiles(tiles_folder: str, slides_metadata_path: str, output_folder: str, sorting_option: str = 'norm_luad_lscc') -> None:
    """ 
    Sort the tiles by one of the following three options while balancing classes to be distributed equally to training
    test and validation set. 
    Stores separate csv files for training, test and validation set, each in the format "path, reference_class" 
        > 'normal_cancer': 'normal' vs. 'cancer'
        > 'luad_lssc': 'cancer subtype LUAD' vs. 'cancer subtype LUSC'
        > 'normal_luad_lssc': 'normal' vs. 'LUAD' vs. 'LUSC'

    Args:
        tiles_folder (str): absolute path to the folder containing all tiles (in separate subfolders per slide)
        slides_file (str): absolute path to CSV file containing required metadata (information about tissue_types etc.)
        output_folder (str): absolute path to the output folder where to store the csv files.
        sorting_option (int): one of the three above-mentioned sorting options specified by the respective identifier.

    Returns:
        None
    """

    if not slides_metadata_path.endswith('.csv'):
        raise ValueError('Please provide a metadata file in CSV format.') 
    else: 
        slides_metadata = pd.read_csv(slides_metadata_path)
    
    classes = _get_classes(sorting_option)
    
    patient_metadata_path = os.path.join(output_folder, 'patient_metadata.csv')
    patient_metadata = _get_patient_meta(patient_metadata_path, slides_metadata, tiles_folder)
    patient_to_category = _assign_patients_to_category(patient_metadata, classes) 
    _write_csv_files(tiles_folder, output_folder, patient_to_category, slides_metadata, classes, sorting_option)
    _add_category_information_to_slide_metadata(slides_metadata, slides_metadata_path, patient_to_category)


def _get_classes(sorting_option: str) -> Dict[str, int]:
    try:
        return SORTING_OPTIONS[sorting_option]
    except:
        raise ValueError('Please specify a valid sorting option.')


def _get_patient_meta(patient_metadata_path: str, slides_metadata: pd.DataFrame, tiles_folder: str) -> pd.DataFrame: 
    # Load or generate internally used dataframe in the format: patientID | nr_tiles | cancer subtype (LUSC, LUAD)
    if os.path.isfile(patient_metadata_path): 
        patient_meta = pd.read_csv(patient_metadata_path)
    else: 
        patient_meta = _generate_patient_meta(slides_metadata, tiles_folder)
        patient_meta.to_csv(patient_metadata_path, index=False)
    return patient_meta


def _generate_patient_meta(slides_metadata: pd.DataFrame, tiles_folder: str) -> pd.DataFrame:
    patient_meta = defaultdict(lambda: [0, 0, None]) # store nr_tiles_total, nr_tiles_cancer and cancer subtype per patient

    for _, row in slides_metadata.iterrows():
        slide_id, patient_id = row['slide_id'], row['patient_id']
        patient_cancer_type, tissue_type = row['cancer_subtype'], row['tissue_type']
        nr_tiles = _get_number_of_tiles(slide_id, tiles_folder)
        
        if patient_id not in patient_meta:
            patient_meta[patient_id][2] = patient_cancer_type
        if tissue_type == 'tumor':
            patient_meta[patient_id][1] += nr_tiles
        patient_meta[patient_id][0] += nr_tiles 
    
    return _convert_to_dataframe(patient_meta)


def _get_number_of_tiles(slide_id: str, tiles_folder: str) -> int:
    tiles_folder_of_slide = os.path.join(tiles_folder, slide_id)
    try: 
        nr_tiles = len([x for x in os.listdir(tiles_folder_of_slide) if x.endswith('.jpeg')])
    except: 
        nr_tiles = 0
    return nr_tiles


def _convert_to_dataframe(patient_meta: Dict[str, list]) -> pd.DataFrame: 
    patient_meta = pd.DataFrame.from_dict(patient_meta, orient='index', columns=['nr_tiles_total', 'nr_tiles_cancer', 'cancer_subtype']).reset_index()
    patient_meta.rename({'index':'patient_id'}, axis='columns', inplace=True)
    return patient_meta


def _assign_patients_to_category(patient_metadata: pd.DataFrame, classes: Dict[str, int]) -> Dict[str, str]:
    # Assign patients to a category (training, validation, test) separately per patient subtype 
    patient_to_category = dict() 
    for c_type in ['luad', 'lscc']:  
        patient_meta_c = patient_metadata[patient_metadata['cancer_subtype'] == c_type] 
        _assign_patients(patient_meta_c, patient_to_category, classes)
    return patient_to_category


def _assign_patients(patient_metadata: pd.DataFrame, patient_to_category: Dict[str, str], classes: Dict[str, int]) -> Dict[str, str]:
    if 'normal' not in classes:
        tiles_to_consider = 'nr_tiles_cancer'
    else: 
        tiles_to_consider = 'nr_tiles_total'

    nr_all_tiles = patient_metadata[tiles_to_consider].sum() 
    nr_tiles_to_test = int(0.15 * nr_all_tiles)
    nr_tiles_to_valid = int(0.15 * nr_all_tiles)

    patient_metadata = patient_metadata.sample(frac=1).reset_index(drop=True) # shuffle rows 
    for _, row in patient_metadata.iterrows():
        patient_id, nr_tiles_patient = row['patient_id'], row[tiles_to_consider]

        # Assign patient to the test set -> if test is full,  assign to validation -> if validation is full, assign to training 
        if nr_tiles_to_test > 0: 
            category = 'test'
            nr_tiles_to_test = nr_tiles_to_test - nr_tiles_patient
        elif nr_tiles_to_valid > 0: 
            category = 'valid'
            nr_tiles_to_valid = nr_tiles_to_valid - nr_tiles_patient
        else: 
            category = 'train'
        patient_to_category[patient_id] = category
    return patient_to_category


def _write_csv_files(tiles_folder: str, output_folder: str, patient_to_category: Dict[str, str], slides_metadata: pd.DataFrame, classes: Dict[str, int], sorting_option: str) -> None:
    path_train = os.path.join(output_folder, 'train_' + sorting_option  + '.csv')
    path_test = os.path.join(output_folder, 'test_' + sorting_option + '.csv')
    path_valid = os.path.join(output_folder, 'valid_' + sorting_option + '.csv')

    with open(path_train, 'w') as csv_train, open(path_test, 'w') as csv_test, open(path_valid, 'w') as csv_valid:
        output_csv = {'train': csv_train, 'test': csv_test, 'valid': csv_valid}
        # Add header
        for csv in output_csv.values(): 
            csv.write('path,reference_value\n')

        # Fill csv files
        slide_folders = glob(os.path.join(tiles_folder, '*'))
        for slide_folder in slide_folders:
            _write_info(slide_folder, output_csv, output_folder, patient_to_category, slides_metadata, classes)
        

def _write_info(slide_folder: str, output_csv: dict, output_folder: str, patient_to_category: Dict[str, str], slides_metadata: pd.DataFrame, classes: Dict[str, int]) -> None:
    slide_id = slide_folder.split('/')[-1]
    patient_id = slides_metadata[slides_metadata['slide_id'] == slide_id]['patient_id'].item()
    if patient_id in patient_to_category: 
        category = patient_to_category[patient_id]
        slide_tissue_type = get_slide_tissue_type(slide_id, slides_metadata)
        try: 
            slide_class = str(classes[slide_tissue_type]) 
        except: # this skips 'normal' slides in the second sorting option that only considers luad vs. lusc slides
            return 
        tiles = os.listdir(slide_folder)
        tiles = [os.path.join(slide_folder, t) for t in tiles] # get full paths 
        tiles = [os.path.relpath(t, start=output_folder) for t in tiles] # convert to paths relative to output directory
        for tile in tiles:    
            output_csv[category].write(','.join([tile, slide_class]))
            output_csv[category].write('\n')


def _add_category_information_to_slide_metadata(slides_metadata: pd.DataFrame, slides_metadata_path: str, patient_to_category: Dict[str, str]) -> None: 
    slides_metadata['dataset'] = '' # initialize empty column to be filled with either train, valid or test 
    for _, row in slides_metadata.iterrows():
        slide_id, patient_id = row['slide_id'], row['patient_id']
        if patient_id in patient_to_category:
            category = patient_to_category[patient_id]
            slides_metadata.loc[slides_metadata['slide_id'] == slide_id, 'dataset'] = category
    slides_metadata.to_csv(slides_metadata_path)


