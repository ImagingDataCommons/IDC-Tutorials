import csv
import os
import random
import numpy as np
from tensorflow.keras.utils import to_categorical
from typing import Tuple, Generator

from .data_point import DataPoint


class Dataset:
    
    def __init__(self, csv_file: str, num_classes: int) -> None:
        self.num_classes = num_classes
        self.data_points = []
        
        base_path = os.path.abspath(os.path.split(csv_file)[0])
        with open(csv_file, mode='r') as f:
            csv_reader = csv.DictReader(f)
            for entry in csv_reader:
                if self.num_classes == 10:
                    reference_value = [int(x) for x in entry['reference_value'].split(';')]
                else: 
                    reference_value = int(entry['reference_value'])
                self.data_points.append(DataPoint(
                        os.path.join(base_path, entry['path']), 
                        reference_value
                    ))
                    
        self.patch_width, self.patch_height, self.num_channels = self.data_points[0].get_patch().shape
        

    def __len__(self) -> int:
        return len(self.data_points)

    def get_generator(self, batch_size: int = 1, infinite: bool = False, shuffle: bool = False) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]: 
        indices = list(range(len(self.data_points)))
        while True:
            if shuffle:
                random.shuffle(indices)

            for batch_indices in [indices[i*batch_size : (i+1)*batch_size] for i in range(len(indices)//batch_size)]:

                batch_x = np.empty((batch_size, self.patch_width, self.patch_height, self.num_channels))
                if self.num_classes == 2: 
                    batch_y = np.empty((batch_size))
                else: 
                    batch_y = np.empty((batch_size, self.num_classes))
                    
                for batch_index, data_index in enumerate(batch_indices):
                    data_point = self.data_points[data_index]
                    batch_x[batch_index] = data_point.get_patch()
                    if self.num_classes == 2: 
                        batch_y[batch_index] = data_point.get_reference_value()
                    elif self.num_classes == 3: 
                        # generate one-hot-encoding for the reference 
                        batch_y[batch_index] = to_categorical(data_point.get_reference_value(), num_classes=3) 
                    elif self.num_classes == 10:
                        # generate k-hot-encoding for the reference
                        batch_y[batch_index] = self.to_k_hot_encoding(data_point)

                yield batch_x, batch_y
            
            if not infinite:
                break

    def to_k_hot_encoding(self, data_point: DataPoint) -> np.ndarray:
        one_hot_in_lines = to_categorical(data_point.get_reference_value(), num_classes=10)
        k_hot = one_hot_in_lines.sum(axis=0)
        return k_hot