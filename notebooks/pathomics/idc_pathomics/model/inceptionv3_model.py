import tensorflow as tf 
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras import Model
from typing import Tuple, Dict, Union

from .base_model import BaseModel


class InceptionModel(BaseModel):
    
    def _create_model(self, num_classes: int = 2, input_shape: Tuple[int, int, int] = (512, 512, 3), learning_rate: float = 0.001) -> tf.keras.Model:
        # Use Inception v3 model by Keras and add top layers manually 
        configs = self._define_configurations(num_classes)
        model = tf.keras.applications.InceptionV3(include_top=False, weights=None, input_shape=input_shape)
        model = self._add_top_layers(model, configs['classifier_activation'], configs['num_outputs'])
        opt = tf.keras.optimizers.RMSprop(learning_rate=learning_rate, rho=0.9, momentum=0.9, epsilon=1.0)
        model.compile(optimizer=opt, loss=configs['loss'], metrics=[configs['metric']]) # note that AUC is on tile-level, not on slide-levela as in the final evaluation
        return model

    def _define_configurations(self, num_classes: int) -> Dict[str, Union[str, int]]:
        # For a binary classification problem: we use single output value from sigmoid layer instead of two output values from softmax layer
        configs = dict()
        if num_classes == 2: 
            configs['num_outputs'] = 1  
            configs['classifier_activation'] = 'sigmoid'
            configs['loss'] = 'binary_crossentropy'
            configs['metric'] = tf.keras.metrics.AUC(curve='ROC')
        elif num_classes == 3: 
            configs['num_outputs'] = num_classes 
            configs['classifier_activation'] = 'softmax'
            configs['loss'] = 'categorical_crossentropy'
            configs['metric'] = tf.keras.metrics.AUC(curve='ROC')
        elif num_classes == 10:
            configs['num_outputs'] = num_classes 
            configs['classifier_activation'] = 'sigmoid'
            configs['loss'] = 'binary_crossentropy'
            configs['metric'] = tf.keras.metrics.AUC(curve='ROC')
        else:
            raise Exception('Number of classes has to be 2, 3 or 10.')
        return configs

    def _add_top_layers(self, model: tf.keras.Model, classifier_activation: str, num_classes: int) -> tf.keras.Model:
        output = model.output
        output = GlobalAveragePooling2D()(output)
        output = Dense(num_classes, activation=classifier_activation, name='predictions')(output)
        return Model(model.input, output)

