import random
import numpy as np 
from wsidicom import WsiDicom
from PIL import Image
from tensorflow.keras.preprocessing.image import img_to_array
from typing import Callable, List, Tuple


class BatchIterator:
    """
    An iterator class to iterate sequentially over all WSI respectively their tiles during network inference.

    Attributes
    ----------
    _wsi: 'WsiDicom'
        Attribute storing the WsiDicom object currently considered.
    _tile_size: int
        Size of the tiles. 
    _level: int 
        Level at which the tiles should be extracted 
    _accept_function: Callable
        Function defining whether a tile is discarded or used for analysis.
    _batch_size: int
        Batch size for network inference. Default: 1.
    _tile_positions: list
        List containing all tile positions present in a WSI. 
    """
    def __init__(self, wsi: WsiDicom, tile_size: int, level: int, 
                 accept_function: Callable[[Image.Image], bool], batch_size: int = 1,
                 coverage: float = 1.0) -> None:
        """
        Constructor of BatchIterator.    

        Parameters
        ----------
        wsi: 'WsiDicom'
            WsiDicom object to be considered for now.
        tile_size: int
            Size of the tiles. 
        _level: int 
            Level at which the tiles should be extracted 
        accept_function: Callable
            Function defining whether a tile is discarded or used for analysis.
        batch_size: int
            Batch size for network inference. Default: 1.
        coverage: float
            Percentage of tiles of a WSI that should be used for inference.   
        """  
        self._wsi = wsi
        self._tile_size = tile_size
        self._level = level
        self._batch_size = batch_size
        self._tile_positions = self._compile_all_tile_positions(\
            wsi, tile_size, level, coverage)
        self._accept_function = accept_function

    @staticmethod
    def _compile_all_tile_positions(wsi: WsiDicom, tile_size: int, level: int, coverage: float) -> list:
        """
        Compiles all possible tile positions with a certain tile size in a WSI with a certain pixel_spacing.

        Parameters
        ---------- 
        wsi: 'WsiDicom'
            WsiDicom object to be considered for now.
        tile_size: int
            Size of the tiles. 
        _level: int 
            Level at which the tiles should be extracted 
        coverage: float
            Percentage of tiles of a WSI that should be used for inference. 

        Returns
        -------
        list
            List of tile positions.   
        """ 
        image_size = (wsi.levels[1].size.width, wsi.levels[1].size.height)
        (cols, rows) = (image_size[0] // tile_size, image_size[1] // tile_size)
        tile_positions = [(tile_pos_x, tile_pos_y) for tile_pos_y in range(0, rows) for tile_pos_x in range(0, cols)]
        tile_positions = random.sample(tile_positions, int(len(tile_positions) * coverage))
        return tile_positions
    
    def __iter__(self):
        self._tile_index = 0
        return self

    @staticmethod
    def _scale_tile(tile: Image.Image) -> np.ndarray:
        """
        Scales image values to [-1, 1], the expected input for InceptionV3 network

        Parameters
        ---------- 
        tile: Image.Image
            Tile to be rescaled.

        Returns
        -------
        np.ndarray
            Tile with rescaled values. 
        """ 
        return (img_to_array(tile) / 127.5) - 1.0

    def __next__(self) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
        """
        Prepares next batch of tiles. 

        Returns
        -------
        tuple
            Tuple with the first element being all tiles in the batch as np.ndarray and 
            the second element being a list of tile positions corresponding to the tiles.
        """ 
        batch_images = np.empty((self._batch_size, self._tile_size, self._tile_size, 3))
        batch_tile_positions = [None] * self._batch_size

        curr_batch_size = 0
        while self._tile_index < len(self._tile_positions) and curr_batch_size < self._batch_size: 
            tile_pos = self._tile_positions[self._tile_index]
            pixel_pos = tile_pos[0] * self._tile_size, tile_pos[1] * self._tile_size
            tile = self._wsi.read_region(level=self._level, location=pixel_pos, size=(self._tile_size, self._tile_size)) 
            assert tile.size[0] == tile.size[1] == self._tile_size

            if self._accept_function(tile):
                tile = self._scale_tile(tile)
                batch_images[curr_batch_size] = tile[np.newaxis, ...]  # add batch dimension
                batch_tile_positions[curr_batch_size] = tile_pos
                curr_batch_size += 1
            
            self._tile_index += 1

        if curr_batch_size > 0:
            batch_images.resize((curr_batch_size, self._tile_size, self._tile_size, 3))
            batch_tile_positions = batch_tile_positions[0:curr_batch_size]
            return (batch_images, batch_tile_positions)
        else:
            raise StopIteration