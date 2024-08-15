import os
import numpy as np
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from PIL.Image import Image
from typing import List, Union

# Path structure is /some/dirs/[SLIDE-ID]/[X]_[Y].jpeg 

class DataPoint:
    
    def __init__(self, patch_path: str, reference_value: Union[int, List[int]]) -> None:
        self.patch_path = patch_path
        self.reference_value = reference_value

    def get_patch(self) -> Image:
        img = load_img(self.patch_path, color_mode='rgb')
        return (img_to_array(img) / 127.5) - 1.0 # Scale to [-1, 1], expected input for InceptionV3 network

    def get_reference_value(self) -> Union[int, List[int]]:
        return self.reference_value

    def get_slide_id(self) -> str:
        return self.patch_path.split(os.sep)[-2]
        # TCGA: return self.patch_path.split(os.sep)[-3][:-6]
    
    def get_position(self) -> List[int]:
        filename = os.path.split(self.patch_path)[1]
        coord_string = os.path.splitext(filename)[0]
        return [int(c) for c in coord_string.split('_')]
