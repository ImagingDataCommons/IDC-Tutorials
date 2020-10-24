# Imaging Data Commons - Radiomics Use Case <br>(Colab Demo - WIP)

*Curated by Dennis Bontempi and Andrey Fedorov*

This repository hosts the demo for *Hosny et Al. - [Deep learning for lung cancer prognostication: A retrospective multi-cohort radiomics study](https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.1002711)*, reproduced using the tools provided by the Imaging Data Commons.


[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ImagingDataCommons/IDC-Examples/blob/master/notebooks/nsclc-radiomics/nsclc_radiomics_demo.ipynb)

Clicking on the badge above will spawn a new Colab session, loading automatically the latest version of the demo notebook. Additional information about the Colab-GitHub integration can be found in [this Colab Notebook](https://colab.research.google.com/github/googlecolab/colabtools/blob/master/notebooks/colab-github-demo.ipynb#scrollTo=WzIRIt9d2huC).

## Paper Abstract

### Background

Non-small-cell lung cancer (NSCLC) patients often demonstrate varying clinical courses and outcomes, even within the same tumor stage. This study explores deep learning applications in medical imaging allowing for the automated quantification of radiographic characteristics and potentially improving patient stratification.

### Methods and Findings

We performed an integrative analysis on 7 independent datasets across 5 institutions totaling 1,194 NSCLC patients (age median = 68.3 years [range 32.5–93.3], survival median = 1.7 years [range 0.0–11.7]). Using external validation in computed tomography (CT) data, we identified prognostic signatures using a 3D convolutional neural network (CNN) for patients treated with radiotherapy (n = 771, age median = 68.0 years [range 32.5–93.3], survival median = 1.3 years [range 0.0–11.7]). We then employed a transfer learning approach to achieve the same for surgery patients (n = 391, age median = 69.1 years [range 37.2–88.0], survival median = 3.1 years [range 0.0–8.8]). We found that the CNN predictions were significantly associated with 2-year overall survival from the start of respective treatment for radiotherapy (area under the receiver operating characteristic curve [AUC] = 0.70 [95% CI 0.63–0.78], p < 0.001) and surgery (AUC = 0.71 [95% CI 0.60–0.82], p < 0.001) patients. The CNN was also able to significantly stratify patients into low and high mortality risk groups in both the radiotherapy (p < 0.001) and surgery (p = 0.03) datasets. Additionally, the CNN was found to significantly outperform random forest models built on clinical parameters—including age, sex, and tumor node metastasis stage—as well as demonstrate high robustness against test–retest (intraclass correlation coefficient = 0.91) and inter-reader (Spearman s rank-order correlation = 0.88) variations. To gain a better understanding of the characteristics captured by the CNN, we identified regions with the most contribution towards predictions and highlighted the importance of tumor-surrounding tissue in patient stratification. We also present preliminary findings on the biological basis of the captured phenotypes as being linked to cell cycle and transcriptional processes. Limitations include the retrospective nature of this study as well as the opaque black box nature of deep learning networks.

### Conclusions 

Our results provide evidence that deep learning networks may be used for mortality risk stratification based on standard-of-care CT images from NSCLC patients. This evidence motivates future research into better deciphering the clinical and biological basis of deep learning networks as well as validation in prospective data.

## Replication Notes

The goal of this Colab notebook is to provide the user with an example of how the tools provided by the Imaging Data Commons can be used to run an AI/ML end-to-end analysis on cohorts hosted by the portal, and to describe what we identified as the best practices to do so.

### Deep Learning Framework Compatibility

Hosny et Al. model was developed using Keras 1.2.2 and an old version of Tensorflow, as stated by the authors (e.g., see [the docker config file in the model GitHub repository](https://github.com/modelhub-ai/deep-prognosis/blob/master/dockerfiles/keras:1.0.1)). Since Google Colab instances are running either TensorFlow 2.x.x or TensorFlow 1.15.2, and Keras 2.x.x, pulling the model from the [project repository](https://github.com/modelhub-ai/deep-prognosis) will not work out-of-the-box (due to compatibility issues between Keras 1.x.x and Keras 2.x.x). 

While it is possible to [use the `%tensorflow_version 1.x` magic to switch to the latest 1.x version of TensorFlow](https://colab.research.google.com/notebooks/tensorflow_version.ipynb)<sup>*</sup>, Colab does not allow to switch to older version of Keras. Fortunately, the solution to this issue is known and discussed in [various threads](https://github.com/keras-team/keras/issues/6382#issuecomment-530258501). Hence, together with this notebook provide a [Keras-2-compatible network configuration JSON file](https://github.com/ImagingDataCommons/IDC-Examples/blob/master/notebooks/nsclc-radiomics/demo/architecture.json).

<i><sup>*</sup>the magic command must be run before importing TensorFlow.</i>

### Replication Results

By default, due to the how time-consuming the preprocessing operations are, the analysis pipeline is run on a sub-cohort rather then on the full one. Depending on such selected sub-cohort, the reproduced pipeline can yield results that are up to 10% better (or worse, depending on the selected patients) with respect to the original results. When the same cohort as the authors is analysed, Hosny et Al. model shows a ROC AUC of 0.7, whereas the IDC replicated pipeline reaches a ROC AUC of 0.68.