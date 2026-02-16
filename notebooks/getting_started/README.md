# NCI Imaging Data Commons: Getting started tutorial series

Not interested in the introductions and want to jump to the tutorial right away? [Basics of searching IDC data](https://github.com/ImagingDataCommons/IDC-Examples/blob/master/notebooks/getting_started/part2_searching_basics.ipynb) (beginner level)

## What is Imaging Data Commons (IDC)?

[NCI Imaging Data Commons (IDC)](https://datacommons.cancer.gov/repository/imaging-data-commons) is a cloud-based environment containing publicly available cancer imaging data co-located with the analysis and exploration tools and resources.

* **~100 TB**: IDC contains radiology, brightfield (H&E) and fluorescence slide microscopy images, along with image-derived data (annotations, segmentations, quantitative measurements) and accompanying clinical data

* **free**: all of the data in IDC is publicly available: no registration, no access requests

* **commercial-friendly**: >95% of the data in IDC is covered by the permissive CC-BY license, which allows commercial reuse (small subset of data is covered by the CC-NC license); each file in IDC is tagged with the license to make it easier for you to understand and follow the rules

* **cloud-based**: all of the data in IDC is available from both Google and AWS public  buckets: fast and free to download, no out-of-cloud egress fees

* **harmonized**: all of the images and image-derived data in IDC is harmonized into standard DICOM representation

## IDC is more than the data it provides! 

* Along with the data, IDC maintains a number of **tools** to help you search, visualize and download the data.
* IDC is cloud-based, which makes it easier to **access cloud resources** for imaging research.
* Cloud-based notebooks can help develop easily accessible demonstrations and make your analysese more easily **reproducible**.
* Computations can be distributed to thousands of cloud-based virtual machines to support **large-scale analysis**.
  
Finally, we want IDC to be a place where members of the community can contribute to enrichment and **collaborative analysis** of the imaging data. If you have robust analysis tools that can be applied to images in IDC to make them more usable and accessible by others - please reach out to support@canceridc.dev! For an example of such secondary analysis, you can read [this forum post](https://discourse.canceridc.dev/t/new-in-idc-v18-totalsegmentator-segmentations-and-radiomics-features-for-nlst-cts/582) to learn how we used _TotalSegmentator_ to annotate CT images in the IDC NLST collection. We want your robust tools to help us improve IDC data further!

<img src="https://raw.githubusercontent.com/ImagingDataCommons/IDC-Tutorials/master/notebooks/getting_started/what_is_idc.png" alt="whatis" width="800" class="center"/>

## Why programmatic access to IDC content?

[IDC Portal](https://imaging.datacommons.cancer.gov/explore/) is the interactive interface that allows exploring data available in IDC using a small subset of metadata attributes accompanying IDC data, visualize radiology and microscopy images and annotations, save cohorts (subsets of data) under user account based on the available metadata filters.

The real power of IDC comes, however, from programmatic interfaces available to work with IDC data. Most of the capabilities available through those interfaces are not available in the portal. As few examples

* you can script download of the files for your selection
* your selection of data can be more granular at the DICOM series level
* you can script generation of citations for complying with the attribution requirements for the individual files
* you have more flexibility in the metadata available for defining your cohorts

## Getting started with IDC tutorial series

Our tutorials are implemented as self-guided Jupyter notebooks. For ease of access, we recommend you use Google Colab for stepping through those notebooks (there is a convenience badge at the top of each tutorial - click it to open the notebook directly in Colab).

If you prefer not to use Google Colab, the beginner level notebook can be executed on your computer.

### Part 1: Introduction (beginner)

[Part 1: Introduction](https://github.com/ImagingDataCommons/IDC-Examples/blob/master/notebooks/getting_started/part1_prerequisites.ipynb) (beginner level)

  In this tutorial you will learn about the basic concepts of how IDC metadata is organized and different means of accessing the metadata for defining cohorts (subsets of data that share some common characteristics). We will also set up the prerequisites for the subsequent components of the tutorial.

### Part 2: First steps with IDC (beginner)

[Part 2: Basics of searching IDC data](https://github.com/ImagingDataCommons/IDC-Examples/blob/master/notebooks/getting_started/part2_searching_basics.ipynb) (beginner level)

  This tutorial will introduce you to the basic capabilities of [`idc-index` python package](https://github.com/ImagingDataCommons/idc-index). In this tutorial we will learn how `idc-index` can help you to:
  * download files corresponding to the collections/patients/images you selected in the IDC Portal
  * use the metadata accompanying IDC images to build cohorts
  * visualize images from your cohort
  * download files corresponding to the cohort
  * access license and citations for your cohort

### Part 3: First steps with Google BigQuery (intermediate)

[Part 3: Working with the cohorts: visualization, download, licenses](https://github.com/ImagingDataCommons/IDC-Examples/blob/master/notebooks/getting_started/part3_exploring_cohorts.ipynb) (intermediate level)
   In this tutorial series we will practice the use of Google BigQuery - a cloud-based query system designed to operate on large tabular datasets. `idc-index` gives you access to a small subset of the metadata accompanying the files available from IDC. With BigQuery you can search all of the metadata, gaining more flexibility in defining cohorts.

### Other topics

* [Exploring clinical data](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/getting_started/exploring_clinical_data.ipynb) (beginner level): many collections in IDC are accompanied by collection-specific metadata describing characteristics of the patient, disease, therapy etc. In IDC we refer to those broadly as "clinical data". In this tutorial you will learn basics about how to navigate IDC clinical data, and how to find what clinical data, if any, is available for a specific IDC collection.

## Advanced tutorials

1. [Experimenting with MedSAM on IDC](https://github.com/ImagingDataCommons/IDC-Examples/blob/master/notebooks/analysis/MedSAM_with_IDC.ipynb)
2. [Introduction to exploring clinical data in IDC](https://github.com/ImagingDataCommons/IDC-Examples/blob/master/notebooks/advanced_topics/clinical_data_intro.ipynb)

## Support and additional resources

* You can contact IDC support by sending email to support@canceridc.dev or posting your question on [IDC User forum](https://discourse.canceridc.dev (preferred).
* Please drop by IDC Office Hours to ask any questions about IDC: every Tuesday 16:30 – 17:30 (New York) and Wednesday 10:30-11:30 (New York) via Google Meet at [https://meet.google.com/xyt-vody-tvb ](https://imaging.datacommons.cancer.gov/).

## Acknowledgments

Imaging Data Commons has been funded in whole or in part with Federal funds from the National Cancer Institute, National Institutes of Health, under Task Order No. HHSN26110071 under Contract No. HHSN261201500003l.

If you use IDC in your research, please cite the following publication:

Fedorov, A., Longabaugh, W. J. R., Pot, D., Clunie, D. A., Pieper, S. D., Gibbs, D. L., Bridge, C., Herrmann, M. D., Homeyer, A., Lewis, R., Aerts, H. J. W., Krishnaswamy, D., Thiriveedhi, V. K., Ciausu, C., Schacherer, D. P., Bontempi, D., Pihl, T., Wagner, U., Farahani, K., Kim, E. & Kikinis, R. National Cancer Institute Imaging Data Commons: Toward Transparency, Reproducibility, and Scalability in Imaging Artificial Intelligence. RadioGraphics (2023). https://doi.org/10.1148/rg.230180
