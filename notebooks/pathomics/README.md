# Introduction to working with digital pathology images in IDC
<img src="https://github.com/ImagingDataCommons/IDC-Tutorials/releases/download/0.20.0/patho_images.jpeg" width="1000"/>

## Repository content
This repository contains 
* a short notebook (**getting_started_with_digital_pathology.ipynb**) giving an idea on how to explore and work with available collections of pathology whole-slide images (WSIs) in the IDC. 
* an notebook (**slide_microscopy_metadata_search.ipynb**) to introduce the key metadata accompanying IDC slide microscopy images that can be used for subsetting data and building cohorts.
* a notebook (**Tutorial_MicroscopyBulkSimpleAnnotations.ipynb**) that shows how to work with bulk annotations encoded in DICOM using the example of nuclei annotations. 

More tutorials that show, for example, how to **train a tissue classification model** can be found in the Github repository [idc-comppath-reproducibility](https://github.com/ImagingDataCommons/idc-comppath-reproducibility) as part of the publication below:

> Schacherer, D. P., Herrmann, M. D., Clunie, D. A., Höfener, H., Clifford, W., Longabaugh, W. J. R., Pieper, S., Kikinis, R., Fedorov, A. & Homeyer, A. The NCI Imaging Data Commons as a platform for reproducible research in computational pathology. _Computer Methods and Programs in Biomedicine_. 107839 (2023). [doi:10.1016/j.cmpb.2023.107839](https://doi.org/10.1016/j.cmpb.2023.107839)


## Collection of common libraries supporting work with DICOM digital pathology images 
The following list contains a collection of (mostly Python) libraries that are well maintained and facilitate working with WSI files in DICOM format. 

### General analysis workflow
* [pydicom](https://github.com/pydicom/pydicom): Python package for reading, modifying, and writing DICOM files. It is not specific to individual types of DICOM files (e.g. WSI data), but instead serves as a basis for more application-specific libraries such as for example those listed [here](https://github.com/pydicom).  
* [wsidicom](https://github.com/imi-bigpicture/wsidicom): Python package for reading and working with DICOM WSI and annotation files. It allows for easy and efficient access of metadata and pixel data from file or via network using DICOMweb.
* [dicomslide](https://github.com/ImagingDataCommons/dicomslide): Python package for reading and working with DICOM WSI and derived information from file or via network using DICOMweb. 
* [openslide](https://pypi.org/project/openslide-python/): Python wrapper for the OpenSlide C package specific for reading and working with WSIs in various formats. Since OpenSlide 4.0.0 it also supports the DICOM format.
* [python-bioformats](https://github.com/CellProfiler/python-bioformats/tree/master): Python wrapper for the Bio-Formats JAVA library, to read and work with WSIs in various formats. Supports DICOM since version 6.8.0.
* [ez-wsi-dicomweb](https://github.com/GoogleCloudPlatform/EZ-WSI-DICOMweb): Python library designed for efficient access of image patches from DICOM WSIs that are stored in a cloud DICOM store. 
* [large-image](https://github.com/girder/large_image): Python library facilitating work with large, multiresolution files in different formats and from different application areas, such as geospatial or medical images. It also includes support for DICOM WSIs.

### Conversion tools
* [wsidicomizer](https://github.com/imi-bigpicture/wsidicomizer): Python library building on wsidicom that converts WSIs in proprietary formats like SVS, MIRAX or CZI into DICOM. The conversion can be lossy or lossless depending on the input format.
* [wsi-to-dicom-converter](https://github.com/GoogleCloudPlatform/wsi-to-dicom-converter): C++ library for the conversion of WSIs from different proprietary formats to DICOM.

### Network and visualization 
* [dicomweb_client](https://github.com/ImagingDataCommons/dicomweb-client): Python client for DICOMweb services, also used by wsidicom and dicomslide.
* [slim](https://github.com/ImagingDataCommons/idc-slim): Interactive web-viewer for WSIs and annotation files in DICOM format that can be deployed [locally](https://github.com/ImagingDataCommons/slim) or in the [cloud](https://tinyurl.com/idc-slim-gcp).
* [vipsdisp](https://github.com/jcupitt/vipsdisp): Lightweight WSI viewer supporting various file formats, including DICOM. 

