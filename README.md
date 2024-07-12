# Welcome!

This repository contains tutorial materials (for the most part, as Python notebooks) that are developed to help you learn about [NCI Imaging Data Commons](https://imaging.datacommons.cancer.gov) and utilize it in your work.

If this is the first time you hear about IDC, you may want to check out our [Getting Started documentation page](https://learn.canceridc.dev/getting-started-with-idc). Here are some highlights about what IDC has to offer:

* **>65 TB of data**: IDC contains radiology, brightfield (H&E) and fluorescence slide microscopy images, along with image-derived data (annotations, segmentations, quantitative measurements) and accompanying clinical data

* **free**: all of the data in IDC is publicly available: no registration, no access requests

* **commercial-friendly**: >95% of the data in IDC is covered by the permissive CC-BY license, which allows commercial reuse (small subset of data is covered by the CC-NC license); each file in IDC is tagged with the license to make it easier for you to understand and follow the rules

* **cloud-based**: all of the data in IDC is available from both Google and AWS public buckets: fast and free to download, no out-of-cloud egress fees

* **harmonized**: all of the images and image-derived data in IDC is harmonized into standard DICOM representation

The tutorial notebooks are located in the [notebooks](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks), and are organized in the following folders.

## [`getting_started`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/getting_started)

"Getting Started" notebooks are intended to introduce the users to IDC. We believe those notebooks are the best place to start using IDC. In this notebook series you will learn:
* how IDC data is organized
* how to search IDC data
* how to download data from IDC
* how to use various visualization tools with IDC data
* how to properly acknowledge data contributors and stay compliant with the usage license

## [`advanced_topics`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/advanced_topics)

Notebooks in this folder focus on topics that will require understanding of the basics, and aim to address more narrow use cases of IDC usage. Such topics include:
* how to search clinical data accompanying IDC images and how to combine imaging and clinical metadata in your searches
* how to use AWS-specific components for working with IDC data
* how to deploy open source OHIF and Slim viewers using free Google Cloud resources

## [`collectons_demos`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/collections_demos)

This folders contains notebooks that demonstrate the usage of the data in the specific IDC collections. The notebooks in this folder will always have the prefix of the `collection_id` they correspond to, for easier navigation.

## [`pathomics`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/pathomics)

This folder is dedicated to the notebooks focused on the digital pathology (pathomics) applications. The use of DICOM standard is relatively new in digital pathology, and this field is being actively developed, thus a dedicated folder for this.

## [`analysis`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/analysis)

Demonstrations/examples of analyses of images from IDC.

## [`labs`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/labs)

Here you will find an archive of the notebooks that were used in tutorials, which at times may demonstrate experimental features. By design, the notebooks presented at specific events may not be updated after the event, and are stored in this folder for archival purposes.

## [`deprecated`](https://github.com/ImagingDataCommons/IDC-Tutorials/tree/master/notebooks/deprecated)

IDC is an actively evolving resource. As we develop new and improved capabilities, we improve our recommended usage practices, and may deprecate notebooks that are no longer maintained and may no longer work. You will find thse in the `deprecated` folder.

## `testing`

This directory is used for the maintenance of the repository to support testing of the actively supported notebooks. 

# Support

If you have any questions about the notebooks in this repository, please open a discussion thread in [IDC user forum](https://discourse.canceridc.dev), or [open the issue in this repository](https://github.com/ImagingDataCommons/IDC-Tutorials/issues/new).
