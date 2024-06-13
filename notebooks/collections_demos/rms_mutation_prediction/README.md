# About

This folder contains notebooks that demonstrate how to work with the [`RMS-Mutation-Prediction`](https://portal.imaging.datacommons.cancer.gov/explore/filters/?collection_id=rms_mutation_prediction) collection.

Read more about this collection in the following:

> Clunie, D., Khan, J., Milewski, D., Jung, H., Bowen, J., Lisle, C., Brown, T., Liu, Y., Collins, J., Linardic, C. M., Hawkins, D. S., Venkatramani, R., Clifford, W., Pot, D., Wagner, U., Farahani, K., Kim, E., & Fedorov, A. (2023). DICOM converted whole slide hematoxylin and eosin images of rhabdomyosarcoma from Children's Oncology Group trials [Data set]. Zenodo. https://doi.org/10.5281/zenodo.8225132

> Bridge, C., Brown, G. T., Jung, H., Lisle, C., Clunie, D., Milewski, D., Liu, Y., Collins, J., Linardic, C. M., Hawkins, D. S., Venkatramani, R., Fedorov, A., & Khan, J. (2024). Expert annotations of the tissue types for the RMS-Mutation-Prediction microscopy images [Data set]. Zenodo. https://doi.org/10.5281/zenodo.10462858

# Notebooks

* [RMS-Mutation-Prediction-Expert-Annotations_exploration.ipynb](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/collections_demos/rms_mutation_prediction/RMS-Mutation-Prediction-Expert-Annotations_exploration.ipynb): introductory tutorial demonstrating how to find, download, and use planar region of interest annotations accompanying this collection, which are stored as DICOM Structured Reports. This tutorial does not have any dependencies on the Google Cloud, and does not have any prerequisites.
* [RMS-Mutation-Prediction-Expert-Annotations_BigQuery.ipynb](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/collections_demos/rms_mutation_prediction/RMS-Mutation-Prediction-Expert-Annotations_BigQuery.ipynb): advanced tutorial that provides examples of using Google BigQuery for searching metadata available in the DICOM SR annotations. You will need to complete prerequisites to set up your own Google Cloud project (see details and pointers in the tutorial).

# Support

Please ask your questions by either opening issues in this repository, or by asking them in the IDC Forum: https://discourse.canceridc.dev.