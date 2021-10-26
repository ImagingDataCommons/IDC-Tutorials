import os 
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme()
from collections import defaultdict
import sklearn.metrics as skm
from sklearn.preprocessing import label_binarize
from sklearn.preprocessing import MultiLabelBinarizer
from scipy import interp
from copy import copy
from typing import Tuple, List, Dict

from .predictions import Predictions 


EXPERIMENTS = {'norm_cancer': {0: 'Normal', 1:'Tumor'}, 'luad_lssc': {0:'LUAD', 1:'LSSC'}, 'norm_luad_lssc': {0:'Normal', 1:'LUAD', 2:'LSSC'}, 
               'mutations': {0: 'STK11', 1: 'EGFR', 2: 'SETBP1', 3: 'TP53', 4: 'FAT1', 5: 'KRAS', 6: 'KEAP1', 7: 'LRP1B', 8: 'FAT4', 9: 'NF1'}, 
               'binary_egfr': {0: 'Normal', 1: 'EGFR'}, 'binary_stk11': {0: 'Normal', 1: 'STK11'}, 'binary_setbp1': {0: 'Normal', 1: 'SETBP1'}, 
               'binary_tp53': {0: 'Normal', 1: 'TP53'}}

class ROCAnalysis():

    def __init__(self, experiment: str = 'norm_luad_lssc') -> None:
        self.experiment = experiment
        self.num_classes = len(EXPERIMENTS[self.experiment])

    def run(self, predictions: Predictions) -> None: 
        # Tile-based analysis
        self.tile_auc, self.tile_ci = self._run_tile_based_roc_analysis(predictions)
        # Slide-based analysis
        slide_data = self._prepare_data_for_slide_based_roc_analysis(predictions)
        self.fpr, self.tpr, self.auc, self.ci = self._run_slide_based_roc_analysis(slide_data)

    def _run_tile_based_roc_analysis(self, predictions: Predictions) -> Tuple[dict,dict]:
        auc = {}
        ci = defaultdict(list)

        reference = predictions.predictions['reference_value'].to_numpy()
        prediction = np.stack(predictions.predictions['prediction'].values)

        if self.num_classes == 2: 
            prediction = np.reshape(prediction, (1, -1)).squeeze()
            auc[1] = skm.roc_auc_score(reference, prediction)
            ci[1] = self._get_confidence_interval_by_bootstrapping(reference, prediction)

        # Multi-class and multi-class multi-label data: Calculate AUC for each class separately      
        else: 
            reference = self._binarize_labels(reference)              
            auc_values = skm.roc_auc_score(reference, prediction, average=None)
            for i in range(self.num_classes):
                auc[i] = auc_values[i]
                ci[i] = self._get_confidence_interval_by_bootstrapping(reference[:, i], prediction[:,i])

            if self.num_classes == 3: 
                auc['micro'] = skm.roc_auc_score(reference.ravel(), prediction.ravel())
                ci['micro'] = self._get_confidence_interval_by_bootstrapping(reference.ravel(), prediction.ravel())
                auc['macro'] = sum(auc[i]for i in range(self.num_classes))/self.num_classes

        return auc, ci


    def _get_confidence_interval_by_bootstrapping(self, reference: np.ndarray, prediction: np.ndarray, num_bootstraps: int = 1000) -> List[float]: 
        bootstrap_scores = []

        for i in range(num_bootstraps):
            bootstrap_indices = np.random.randint(0, len(reference), size=len(reference))
            reference_sample = reference[bootstrap_indices]
            prediction_sample = prediction[bootstrap_indices]
            # We need at least one positive and one negative sample
            if len(np.unique(reference_sample)) < 2:
                continue
            else: 
                auc = skm.roc_auc_score(reference_sample, prediction_sample)
                bootstrap_scores.append(auc)

        bootstrap_scores = np.asarray(bootstrap_scores)
        bootstrap_scores.sort()
        ci_lower = bootstrap_scores[int(0.025* len(bootstrap_scores))]
        ci_upper = bootstrap_scores[int(0.975* len(bootstrap_scores))]
        return [ci_lower, ci_upper]  


    def _prepare_data_for_slide_based_roc_analysis(self, predictions: Predictions) -> pd.DataFrame:
        results_per_slide = defaultdict(dict)

        # Average predictions of tiles to obtain one prediction per slide
        all_slide_ids = list(set(predictions.predictions['slide_id'].tolist()))
        for slide_id in all_slide_ids:
            slide_predictions = predictions.get_predictions_for_slide(slide_id)
            reference_value = predictions.get_reference_value_for_slide(slide_id)
            
            average_probability = np.average(slide_predictions, axis=0)
            positive = np.where(np.asarray(slide_predictions) >= 0.5, 1, 0)
            percentage_positive = np.average(positive, axis=0)

            results_per_slide[slide_id]['reference_value'] = reference_value
            results_per_slide[slide_id]['average_probability'] = average_probability
            results_per_slide[slide_id]['percentage_positive'] = percentage_positive
        
        # Turn results into pandas data frame: slide_id (str) | reference_value (int) | average_probability (list[int]) | percentage_positive (list[int]))
        # Note: In two-class problem, average_probability and percentage_positive contain only one value, otherwise correspondingly to the number of classes.
        result_df = pd.DataFrame(results_per_slide).T
        result_df.reset_index(inplace=True)
        result_df.rename({'index':'slide_id'}, axis='columns', inplace=True)
        return result_df


    def _run_slide_based_roc_analysis(self, slide_data: pd.DataFrame) -> Tuple[dict, dict, dict, dict]:
        # Multi-class ROC curve including ROC curve for each class-vs-rest, micro- and macro-average ROC
        if self.num_classes > 2: 
            fpr, tpr, auc, ci = self._generate_multiclass_roc_curves(slide_data)

        # Two-class ROC curve
        else: 
            fpr, tpr, auc, ci = {}, {}, {}, {} 
            reference = slide_data['reference_value'].tolist()
            for column in ['average_probability', 'percentage_positive']:
                prediction = np.concatenate(slide_data[column]).ravel()
                fpr[column], tpr[column], auc[column] = self._generate_roc_curve(reference, prediction)
                ci[column] = self._get_confidence_interval_by_bootstrapping(np.asarray(reference), prediction)
        
        return fpr, tpr, auc, ci


    def _generate_multiclass_roc_curves(self, slide_data: pd.DataFrame) -> Tuple[dict, dict, dict, dict]: 
        # Binarize the reference values 
        reference = self._binarize_labels(slide_data['reference_value'].tolist())

        # Compute ROC curve and ROC area for each class vs. rest
        fpr = defaultdict(dict)
        tpr = defaultdict(dict)
        auc = defaultdict(dict)
        ci = defaultdict(dict)
        for i in range(self.num_classes):
            for column in ['percentage_positive', 'average_probability']:
                prediction = np.asarray([x[i] for x in slide_data[column]])
                fpr[column][i], tpr[column][i], auc[column][i] = self._generate_roc_curve(reference[:, i], prediction)
                ci[column][i] = self._get_confidence_interval_by_bootstrapping(reference[:,i], prediction)

        # Generate macro-average and micro-average ROC curve for the three-class classification problem
        if self.num_classes == 3:
            for column in ['percentage_positive', 'average_probability']:
                fpr[column]['macro'], tpr[column]['macro'], auc[column]['macro'] = self._generate_macro_average_roc(tpr[column], fpr[column])
                # TODO ci['macro] 

                all_predictions = np.asarray([i for x in slide_data[column] for i in x])
                fpr[column]['micro'], tpr[column]['micro'], auc[column]['micro'] = self._generate_roc_curve(reference.ravel(), all_predictions)
                ci[column]['micro'] = self._get_confidence_interval_by_bootstrapping(reference.ravel(), all_predictions)

        return fpr, tpr, auc, ci


    def _binarize_labels(self, values: np.ndarray) -> np.ndarray:
        if self.num_classes == 10: # multi-label
            mlb = MultiLabelBinarizer(classes=[i for i in range(self.num_classes)])
            binarized = mlb.fit_transform(values)
        else: 
            binarized = label_binarize(values, classes=[i for i in range(self.num_classes)]) 
        return binarized


    def _generate_roc_curve(self, reference: np.ndarray, prediction: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        fpr, tpr, _ = skm.roc_curve(
            y_true = reference,
            y_score = prediction
        )
        auc = skm.auc(fpr, tpr)
        return fpr, tpr, auc


    def _generate_macro_average_roc(self, tpr: np.ndarray, fpr: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        # Aggregate all false positive rates
        all_fpr = np.unique(np.concatenate([fpr[i] for i in range(3)]))

        # Interpolate true positive rate at the respective false positive rate
        mean_tpr = np.zeros_like(all_fpr)
        for i in range(3):
            mean_tpr += interp(all_fpr, fpr[i], tpr[i])
        mean_tpr = mean_tpr/self.num_classes  

        auc = skm.auc(all_fpr, mean_tpr)
        return all_fpr, mean_tpr, auc


    def plot_and_save(self, output_folder: str) -> None:
        colors = ['g', 'b', 'r', 'olive', 'gray', 'orange', 'magenta', 'royalblue', 'aqua', 'burlywood', 'yellow']

        if self.num_classes == 2:
            fig = plt.figure(fisize=(7,4)) 
            self._plot_bisector(fig)
            for i, avg_method in enumerate(self.fpr):
                label='%s (AUC = %0.3f)' % (avg_method, self.auc[avg_method])
                plt.plot(
                    self.fpr[avg_method],
                    self.tpr[avg_method],
                    color=colors[i],
                    linewidth=2,
                    label=label, 
                    alpha=0.3
                )
            self._format_and_save_plot(fig, 'Slide-based ROC analysis')
            plt.savefig(os.path.join(output_folder, 'roc_analysis.png'))
            plt.show()
            plt.close()

        # Plot ROC curves separately for the two averaging methods if num_classes > 2
        else: 
            fig, axes = plt.subplots(1,2, figsize=(10,4))
            fig.suptitle('Slide-based ROC analysis')
            for i, avg_method in enumerate(self.fpr):
                self._plot_bisector(axes[i])
                for idx, key in enumerate(self.fpr[avg_method]): 
                    if key=='macro': # to be removed as soon as macro computation is added 
                        continue 
                    class_to_str_mapping = copy(EXPERIMENTS[self.experiment])
                    class_to_str_mapping['micro'] = 'Micro'
                    class_to_str_mapping['macro'] = 'Macro'
                    label='%s (AUC = %0.3f)' % (class_to_str_mapping[key], self.auc[avg_method][key])
                    axes[i].plot(
                        self.fpr[avg_method][key],
                        self.tpr[avg_method][key],
                        color=colors[idx],
                        linewidth=2,
                        label=label
                    )
                self._format_and_save_plot(axes[i], 'ROC (%s)' % (avg_method))
            fig.savefig(os.path.join(output_folder, 'roc_analysis.png'))
            plt.show()
            plt.close()


    def _plot_bisector(self, axis: plt.Axes) -> None:
        axis.plot(
            [0, 1],
            [0, 1],
            color='black',
            linewidth=1,
            linestyle='--'
        )


    def _format_and_save_plot(self, axis: plt.Axes, title: str) -> None:
        axis.set_title(title)
        axis.set_xlim([0.0, 1.0])
        axis.set_ylim([0.0, 1.0])
        axis.set_xlabel('False positive rate')
        axis.set_ylabel('True positive rate')
        axis.legend(loc='lower right')


    def print_and_save_tabluar_results_with_ci(self, output_path: str) -> None:
        class_to_str_mapping = copy(EXPERIMENTS[self.experiment])
        class_to_str_mapping['micro'] = 'Micro'
        class_to_str_mapping['macro'] = 'Macro'
        if self.num_classes == 2: 
            results_dict = {('tile-based', ' ', 'auc'): self.tile_auc, 
                            ('tile-based', ' ', 'confidence'): self.tile_ci, 
                            ('slide-based', 'average probability', 'auc'): {1: self.auc['average_probability']}, 
                            ('slide-based', 'average probability', 'confidence'): {1: self.ci['average_probability']},
                            ('slide-based', 'percentage positive', 'auc'): {1: self.auc['percentage_positive']}, 
                            ('slide-based', 'percentage positive', 'confidence'): {1: self.ci['percentage_positive']}}
            results = pd.DataFrame.from_dict(results_dict, dtype=object)
        else: 
            results_dict = {('tile-based', ' ', 'auc'): self.tile_auc, 
                            ('tile-based', ' ', 'confidence'): self.tile_ci, 
                            ('slide-based', 'average probability', 'auc'): self.auc['average_probability'], 
                            ('slide-based', 'average probability', 'confidence'): self.ci['average_probability'],
                            ('slide-based', 'percentage positive', 'auc'): self.auc['percentage_positive'], 
                            ('slide-based', 'percentage positive', 'confidence'): self.ci['percentage_positive']}
            results = pd.DataFrame(results_dict, dtype=object)
            results.rename(index=class_to_str_mapping, inplace=True)
            results.drop(['Macro'], inplace=True) # remove macro averaging for now
        display(results)
        html = results.to_html()
        text_file = open(output_path, 'w')
        text_file.write(html)
        text_file.close()


    def print_and_save_tabluar_results(self, output_path:str) -> None:
        class_to_str_mapping = copy(EXPERIMENTS[self.experiment])
        class_to_str_mapping['micro'] = 'Micro'
        class_to_str_mapping['macro'] = 'Macro'
        results_dict = {('tile-based AUC', ''): self.tile_auc, 
                        ('slide-based AUC', 'average probability'): self.auc['average_probability'], 
                        ('slide-based AUC', 'percentage positive'): self.auc['percentage_positive']}
        results = pd.DataFrame(results_dict, dtype=float)
        results.rename(index=class_to_str_mapping, inplace=True)
        results.drop(['Macro'], inplace=True) # remove macro averaging for now
        results = results.round(decimals=3)
        display(results)
        html = results.to_html()
        text_file = open(output_path, 'w')
        text_file.write(html)
        text_file.close()