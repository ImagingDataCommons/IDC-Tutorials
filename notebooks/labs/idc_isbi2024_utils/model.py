import os
import json
import numpy as np 
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras import Model
from typing import Dict, Generator, Tuple


class BaseModel:
    """
    Neural network base model class.

    Attributes
    ----------
    model: tf.keras.Model
        Neural network model. 
    """

    def __init__(self, model=None, *args, **kwargs):
        """
        Constructor of BaseModel. 

        Parameters
        ----------
        model: tf.keras.Model
            Neural network model.
        """ 
        if model: 
            self.model = model 
        else: 
            self.model = self._create_model(*args, **kwargs)
    
    @classmethod
    def load(cls, file_path: str) -> tf.keras.Model:
        """
        Loads a pre-existing model and create a BaseModel instance from it. 

        Parameters
        ----------
        file_path: str
            Path to the pre-existing model in SavedModel format.
        """
        model = load_model(file_path, compile=False)
        return cls(model)

    def _create_model(self, *args, **kwargs):
        raise NotImplementedError

    def __repr__(self) -> str:
        lines = []
        self.model.summary(print_fn=lambda line: lines.append(line))
        return os.linesep.join(lines)

    def summarize_trainable_variables(self):
        return sum(map(lambda x: x.sum(), self.model.get_weights()))
    
    def train(
        self, 
        training_generator: Generator, 
        train_set_len: int,
        batch_size: int, 
        epochs: int, 
        output_path: str, 
        validation_generator: Generator = None,
        val_set_len: int = None,
        class_weights: Dict[int, float] = None,
        max_queue_size: int = 100) -> tf.keras.callbacks.History:
        """
        Function to invoke trainig of the neural network model. 

        Parameters
        ----------
        training_generator: Generator
            Generator object for the training data.
        train_set_len: int
            Number of elements in the training set.
        batch_size: int
            Number of elements to be in one batch.
        epochs: int
            Number of training epochs.
        output_path: str
            Path to the folder where to store configurations and parameters used.
        validation_generator: Generator = None
            Generator object for the validation data.
        val_set_len: int
            Number of elements in the validation set.
        class_weights: dict
            Dictionary defining weights for each class.
        max_queue_size: int
            The maximum number of tasks in the task queue.
        
        Returns
        -------
        tf.keras.callbacks.History
            History object as returned by the model.fit method of Keras.
        """

        if not validation_generator: 
            validation_steps = None
        else: 
            validation_steps = val_set_len//batch_size

        save_model_callback = ModelCheckpoint(
            filepath=os.path.join(output_path, 'checkpoint_{epoch:03d}'), 
            save_weights_only=False, 
            monitor='val_auc', 
            mode='max',
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
        configs_to_store = {str(key): str(val) for key, val in configs_to_store.items()}
        with open(os.path.join(output_path, 'training_config.txt'), 'w') as configs_file:
            json.dump(configs_to_store, configs_file)

        with open(os.path.join(output_path, 'determinism_checksum.txt'), 'w') as determinism_check:
            determinism_check.write('Summary of trainable variables before training: {}\n'
                                    .format(self.summarize_trainable_variables()))
        
        self.model.fit(
            training_generator,
            epochs=epochs,
            max_queue_size=max_queue_size,
            verbose=2, 
            steps_per_epoch=train_set_len//batch_size,
            validation_data=validation_generator,
            validation_steps=validation_steps, 
            callbacks=[save_model_callback, csv_logger_callback], 
            class_weight=class_weights, 
            workers=1 
        )

        with open(os.path.join(output_path, 'determinism_checksum.txt'), 'a') as determinism_check:
            determinism_check.write('Summary of trainable variables after training: {}\n'
                                    .format(self.summarize_trainable_variables()))
    
    def make_prediction(self, batch: np.ndarray) -> np.ndarray:
        """
        Function to make a prediction for one batch.  

        Parameters
        ----------
        batch: np.ndarray
            Batch of elements to obtain a prediction for.

        Returns
        -------
        np.ndarray
            Array of class predictions. 
        """ 
        # Make prediction 
        prediction = self.model(batch)
        return prediction

    def save(self, output_dir: str) -> None:
        """
        Function storing the neural network model in SavedModel format.  

        Parameters
        ----------
        output_dir: str
            Folder where to store the model.
        """
        self.model.save(
            os.path.join(output_dir, 'trained_model'),
            overwrite=True,
            include_optimizer=False)


class InceptionModel(BaseModel):
    
    def _create_model(self, num_classes: int, input_shape: Tuple[int, int, int], learning_rate: float) -> tf.keras.Model:
        # Use Inception v3 model by Keras and add top layers manually 
        model = tf.keras.applications.InceptionV3(include_top=False, weights='imagenet', input_shape=input_shape)
        model = self._add_top_layers(model, classifier_activation='softmax', num_classes=num_classes)
        opt = tf.keras.optimizers.RMSprop(learning_rate=learning_rate)
        # Note that AUC below is on tile-level, not on slide-level as in the final evaluation
        model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=[tf.keras.metrics.AUC(curve='ROC')])
        return model

    def _add_top_layers(self, model: tf.keras.Model, classifier_activation: str, num_classes: int) -> tf.keras.Model:
        output = model.output
        output = GlobalAveragePooling2D()(output)
        output = Dense(num_classes, activation=classifier_activation, name='predictions')(output)
        return Model(model.input, output)