import os
import json 
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger
from tensorflow.keras.models import load_model
from typing import Dict, List

from ..data.data_set import Dataset
from ..data.data_point import DataPoint

class BaseModel:
    def __init__(self, model=None, *args, **kwargs):
        if model: 
            self.model = model 
        else: 
            self.model = self._create_model(*args, **kwargs)
    
    @classmethod
    def load(cls, file_path: str) -> tf.keras.Model:
        model = load_model(file_path, compile=False)
        return cls(model)

    def _create_model(self, *args, **kwargs):
        raise NotImplementedError

    def __repr__(self) -> str:
        lines = []
        self.model.summary(print_fn=lambda line: lines.append(line))
        return os.linesep.join(lines)

    def train(
        self, 
        training_dataset: Dataset, 
        batch_size: int, 
        epochs: int, 
        output_path: str, 
        validation_dataset: Dataset = None, 
        class_weights: Dict[int, float] = None,
        max_queue_size: int = 100) -> tf.keras.callbacks.History:

        training_generator = training_dataset.get_generator(
            batch_size=batch_size,
            infinite=True,
            shuffle=True)

        if validation_dataset:
            validation_generator = validation_dataset.get_generator(
                batch_size=batch_size,
                infinite=True)
            validation_steps = len(validation_dataset)//batch_size
        else:
            validation_generator = None
            validation_steps = None

        save_model_callback = ModelCheckpoint(
            filepath=os.path.join(output_path, 'checkpoint_{epoch:03d}'), 
            save_weights_only=False, 
            monitor='val_loss', 
            mode='min',
            save_best_only=True
        )

        csv_logger_callback = CSVLogger(
            filename=os.path.join(output_path, 'train.csv')
        )

        configs_to_store = self.model.optimizer.get_config()
        configs_to_store['batch_size'] = batch_size
        configs_to_store['class_weights'] = class_weights
        configs_to_store['epochs'] = epochs
        configs_to_store['tile_size'] = self.model.layers[0].input_shape
        with open(os.path.join(output_path, 'training_config.txt'), 'w') as configs_file:
            json.dump(configs_to_store, configs_file)

        self.model.fit(
            training_generator,
            epochs=epochs,
            max_queue_size=max_queue_size,
            steps_per_epoch=len(training_dataset)//batch_size,
            validation_data=validation_generator,
            validation_steps=validation_steps, 
            callbacks=[save_model_callback, csv_logger_callback], 
            class_weight=class_weights
        )
    
    def make_prediction(self, data_points: List[DataPoint]) -> np.ndarray: 
        # Create batch
        tile_size = self.model.layers[0].input_shape[0][1]
        required_dtype = data_points[0].get_patch().dtype
        batch = np.empty((0, tile_size, tile_size, 3), required_dtype)
        for data_point in data_points:
            patch = data_point.get_patch()[np.newaxis, ...] # add batch dimension
            batch = np.append(batch, patch, axis=0)
        # Make prediction 
        prediction = self.model(batch)
        return prediction

    def save(self, output_dir: str) -> None:
        self.model.save(
            os.path.join(output_dir, 'trained_model'),
            overwrite=True,
            include_optimizer=False
        )

