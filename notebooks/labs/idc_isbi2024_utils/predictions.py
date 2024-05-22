import pandas as pd
from typing import List


class Predictions():
    """
    Class to organize the predictions that are returned by the network.

    Attributes
    ----------
    _predictions: pd.DataFrame
        Dataframe with columns image_id, tile_position, reference_class_index, 
        predicted_class_index and predicted_class_probabilites.
    """ 
    
    def __init__(self, predictions: pd.DataFrame) -> None:
        """
        Constructor of Predictions. 

        Parameters
        ----------
        predictions: pd.DataFrame
            Dataframe summarizing all predictions made by the network.
        """ 
        self._predictions = predictions

    def save(self, path: str) -> None:
        """
        Saves the prediction to a csv file. 

        Parameters
        -------
        path: str
            Complete path to save the predictions' csv table.
        """
        self._predictions.to_csv(path, index=False)
    
    def get_all_image_ids(self) -> List:
        """
        Gets all image IDs for which tile predictions have been made. 

        Returns
        -------
        list
            List of image IDs. 
        """ 
        return sorted(list(set(self._predictions['image_id'].tolist())))

    def get_results_of_image(self, image_id: str) -> pd.DataFrame:
        """
        Gets all predictions for a certain image ID.  

        Parameters
        ----------
        image_id: str
            Image ID of interest.

        Returns
        -------
        pd.DataFrame
            Subsample of self._predictions containing only predictions for image_id. 
        """ 
        return self._predictions.loc[self._predictions['image_id'] == image_id]