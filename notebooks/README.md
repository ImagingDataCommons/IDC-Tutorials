# IDC-Examples/notebooks
The **notebooks** subdirectory of this repository contains a series of IPython notebooks that are intended to help you get started working with IDC hosted data.

## Try these first
* [Getting started notebook series](https://github.com/ImagingDataCommons/IDC-Examples/tree/master/notebooks/getting_started): Introduction to IDC data organization and main features
* IDC segmentation primer: Experimenting with nnU-Net Segmentation of IDC Data [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/IDC_segmentation_primer.ipynb)

This notebook can be used as a source of small examples and useful bits for developing your own notebooks:
* IDC Colab cookbook [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/cookbook.ipynb)

## Data Download and Exploration

The following notebooks contain examples of how to download and explore IDC cohorts:

* Introduction to IDC clinical data organization [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/clinical_data_intro.ipynb)
* LIDC exploration [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/LIDC_exploration.ipynb)
* Cohort download [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/Cohort_download.ipynb)

Furthermore, the Cohort Preparation notebook [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/cohort_preparation.ipynb) contains a simple tutorial on how to get a cohort ready for your image processing applications (e.g., best practices for the conversion from DICOM to NRRD and NIfTI, pointers to pre-processing utilities).


## Imaging Analysis AI

The following notebooks contain examples of how IDC can be used to run AI-based medical imaging analysis pipelines on the cloud:

* DeepPrognosis use case - replication study, 2 year survival score of NSCLC patients [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/nsclc-radiomics/nsclc_radiomics_demo_release.ipynb)
* Lung Nodules segmentation and prognosis use case - NSCLC patients nodules segmentation (nnU-Net) and prognosis (DeepPrognosis) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/lung_nodules_demo.ipynb)
* Thoracic Organs at Risk segmentation use case - NSCLC patients thoracic OAR segmentation (nnU-Net) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/thoracic_oar_demo.ipynb)
* Pathomics: Lung Tissue Data Exploration [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/pathomics/lung_cancer_cptac_DataExploration.ipynb)
* Pathomics: Lung Tissue Classification - training and applying a DL model for classification of tissue types [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/pathomics/lung_cancer_cptac_TissueClassificationModel.ipynb)

**N.B.**: since these demonstrations run in Google Colab, they highlight only a small part of what IDC can offer in terms of computational capability for imaging analysis. A more comprehensive experience of such tools can be explored, e.g., by experimenting with GCP Virtual Machines.

To learn more about how to access the GCP virtual machines for free (using [free cloud credits](https://learn.canceridc.dev/introduction/requesting-gcp-cloud-credits)), please visit the [IDC user guide](https://learn.canceridc.dev/). 



