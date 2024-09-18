# Welcome!

This repository contains tutorial materials (for the most part, as Python notebooks) that are developed to help you learn about [NCI Imaging Data Commons](https://imaging.datacommons.cancer.gov) and utilize it in your work.

If this is the first time you hear about IDC, you may want to check out our [Getting Started documentation page](https://learn.canceridc.dev/getting-started-with-idc). Here are some highlights about what IDC has to offer:

* **>78 TB of data**: IDC contains radiology, brightfield (H&E) and fluorescence slide microscopy images, along with image-derived data (annotations, segmentations, quantitative measurements) and accompanying clinical data

* **free**: all of the data in IDC is publicly available: no registration, no access requests

* **commercial-friendly**: >95% of the data in IDC is covered by the permissive CC-BY license, which allows commercial reuse (small subset of data is covered by the CC-NC license); each file in IDC is tagged with the license to make it easier for you to understand and follow the rules

* **cloud-based**: all of the data in IDC is available from both Google and AWS public buckets: fast and free to download, no out-of-cloud egress fees

* **harmonized**: all of the images and image-derived data in IDC is harmonized into standard DICOM representation

The tutorial notebooks are located in the [notebooks](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks), and are organized in the following folders.

## [`getting_started`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/getting_started)

"Getting Started" python notebooks are intended to introduce the users to IDC. 

* [Basics of using IDC data programmatically](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/getting_started/part2_searching_basics.ipynb): learn how to use `idc-index` python package to programmatically search and download IDC data, visualize images and annotations, build cohorts and checking acknowledgments and liceses for the data included in your cohort.
* [Searching clinical data](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/getting_started/exploring_clinical_data.ipynb): identify clinical and other non-imaging data accompanying imaging collections in IDC using `idc-index` python package and `duckdb`.
* [Advanced searching using BigQuery](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/getting_started/part3_exploring_cohorts.ipynb): access all of the metadata to build comprehensive queries and detailed cohort selection criteria.

## [`advanced_topics`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/advanced_topics)

Notebooks in this folder focus on topics that will require understanding of the basics, and aim to address more narrow use cases of IDC usage. 

* [Searching DICOM private tags](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/advanced_topics/dicom_private_tags_intro.ipynb): all of DICOM attributes for the imaging data in IDC are searchable using BigQuery. DICOM private tags often contain critical information, such as diffusion b-values, but are a bit more tricky to access from BigQuery. In this tutorial you will learn how to accomplish this.
* [Using BigQuery for searching IDC clinical data](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/advanced_topics/clinical_data_intro.ipynb): BigQuery is an alternative to `idc-index` and `duckdb` for searching clinical data. This tutorial demonstrates more capabilities compared to the introductory clinical data usage tutorial.

## [`viewers_deployment`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/viewers_deployment)

These notebooks can be used to deploy your own cloud-based instance of OHIF or Slim viewers using Google Firebase, which you can use to visualize analysis results you generated for IDC data, or to work with your own images. These tutorials utilize free tier of Firebase, and so there is no cost to keep the deployed viewers available in the cloud.

* [OHIF Firebase deployment](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/viewers_deployment/OHIF_FireBase_deployment.ipynb)
* [Slim Firebase deployment](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/viewers_deployment/slim_Firebase_deployment.ipynb)
* [Setting up Google Healthcare DICOM store](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/viewers_deployment/Creating_Google_Healthcare_DICOM_store.ipynb): once you have your viewers deployed, you can use this tutorial to create a DICOM store with your data, which you can then access from the viewers deployed

## [`collectons_demos`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/collections_demos)

This folders contains notebooks that demonstrate the usage of the data in the specific IDC collections. The notebooks in this folder will always have the prefix of the `collection_id` they correspond to, for easier navigation.

* [Using hiplot for exploring prostate MRI in IDC](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/collections_demos/prostate-MRI_hiplot_experiments.ipynb): this notebook demonstrates how [`hiplot`](https://facebookresearch.github.io/hiplot/), an open source package for high-dimensional parameter visualization, for examining various MRI acquisition parameters for the prostate MRI images available in IDC.
* [Visible Human Project exploration](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/collections_demos/nlm_visible_human_project.ipynb): demonstration of searching and visualizing images from the National Library of Medicine Visible Human Project available on IDC.
* [RMS-Mutation-Prediction collection exploration](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/collections_demos/rms_mutation_prediction): notebooks in this folder demonstrate selecting images from the `RMS-Mutation-Prediction` collection based on various attributes of images and expert annotations.

## [`pathomics`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/pathomics)

This folder is dedicated to the notebooks focused on the digital pathology (pathomics) applications. The use of DICOM standard is relatively new in digital pathology, and this field is being actively developed, thus a dedicated folder for this.
* [Getting started with pathology images in IDC](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/pathomics/getting_started_with_digital_pathology.ipynb): all of the pathology images in IDC are in DICOM Slide Microscopy format; this notebook will help you get started with using this representation and also searching IDC pathology images.
* [Exploring IDC slide microscopy images metadata](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/pathomics/slide_microscopy_metadata_search.ipynb): introduction to the key metadata accompanying IDC slide microscopy images that can be used for subsetting data and building cohorts.

## [`analysis`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/analysis)

Demonstrations/examples of analyses of images from IDC.
* [MedSAM on IDC](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/analysis/MedSAM_with_IDC.ipynb): learn how to experiment with MedSAM on the images available from IDC.
* [MHub.ai with IDC data](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/analysis/mhubai_tutorial.ipynb): [MHub.ai](https://mhub.ai) is a platform for Deep Learning models in medical imaging, which are interoperable with IDC and can be applied directly to the IDC DICOM images. Learn how to get started from this notebook!

## [`labs`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/labs)

Here you will find an archive of the notebooks that were used in tutorials, which at times may demonstrate experimental features. By design, the notebooks presented at specific events may not be updated after the event, and are stored in this folder for archival purposes.

## [`deprecated`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/deprecated)

IDC is an actively evolving resource. As we develop new and improved capabilities, we improve our recommended usage practices, and may deprecate notebooks that are no longer maintained and may no longer work. You will find thse in the `deprecated` folder.

## `testing`

This directory is used for the maintenance of the repository to support testing of the actively supported notebooks. 

# Support

If you have any questions about the notebooks in this repository, please open a discussion thread in [IDC user forum](https://discourse.canceridc.dev), or [open the issue in this repository](https://github.com/ImagingDataCommons/IDC-Tutorials/issues/new).
