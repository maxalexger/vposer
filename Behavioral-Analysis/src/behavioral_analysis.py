import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.stats import norm
from tqdm import tqdm
import os
import pickle
from collections import Counter


"""
    File: behavioral_analysis.py
    Author: MA Gehrke
    Date: 08.02.2022

    This class loads the data in form of arrays from 
    the hard drive and processes it to plot bar-
    and boxplots.
"""


class BehavioralAnalysis:
    def __init__(self, ba_numbers: [str]):
        """
        Class for executing statistical calculations on the data of the
        first, the second or both behavioral analyses.

        Make sure the 'Questionnaire.txt' has been downloaded from Qualtrics,
        using 'Numeric Values'.

        :param ba_number: chooses the data that will be used. Either from
            the first behavioral analysis, the second or all the data together.
        """
        self.ba_numbers = ba_numbers
        for n in ba_numbers:
            assert n in ['1', '2', 'all']
        print(f'Calculating plots for {ba_numbers}!')

        self.out_dir = {
            '1': f'../output/behavioral_analysis_1/',
            '2': f'../output/behavioral_analysis_2/',
            'all': f'../output/all/'
        }
        for v in self.out_dir.values():
            if not os.path.exists(v):
                os.makedirs(v)

        # Resolution of the plots
        self.dpi = 200

        # GET SCALES FOR EACH QUESTION/STIMULI/UPARAM
        # Load file containing which question belongs to which pose
        p_items_lst = np.load('../input/behavioral_analysis_1/item-question-association.npy', allow_pickle=True).item()
        p_items_lst = dict(p_items_lst)
        assert len(p_items_lst.keys()) == 324
        # Extract uparam names (108 names with 3 viewpoints each)
        uparam_names = [x[:x.find('Viewpoint') - 1] for x in
                        p_items_lst.keys()]
        uparam_names = set(uparam_names)
        assert len(uparam_names) == 108
        # Extract scales
        self.scale = {}
        for un in uparam_names:
            for stim in p_items_lst.keys():
                if stim.startswith(f'{un}_'):
                    self.scale[un] = stim[stim.find('scale') + 6:]

    def load_statistics(self, quest_dict: dict, ba_num: str) -> dict:
        """Load and return dictionary with the observations of the questions."""
        save_dir = f'{self.out_dir[ba_num]}stat_dicts/{quest_dict["prefix"]}_dict.pkl'
        if os.path.exists(save_dir):
            with open(save_dir, "rb") as input_file:
                stats = pickle.load(input_file)
                return stats

    # Not used
    def create_boxplots_vp(self, desc: dict, stats: dict):
        loop_desc = f'Creating {desc["prefix"]} boxplots'
        save_dir = f'boxplots-vp/{desc["prefix"]}'
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        for uparam, dfs_of_vps in tqdm(stats.items(), loop_desc):
            y_labels = []
            for i, (pose_name, vp_dict) in enumerate(dfs_of_vps.items()):
                plt.boxplot(vp_dict['raw'], positions=[i+1])
                y_labels.append(f'{i+1} (n={vp_dict["n"]})')
            plt.title(f'{uparam} (Scale = {self.scale[uparam]})')
            plt.ylim((desc['likert_min'] - 1, desc['likert_max'] + 1))
            plt.yticks(range(desc['likert_min'], desc['likert_max'] + 1),
                       range(desc['likert_min'],  desc['likert_max'] + 1))
            plt.xticks(range(1, 4), y_labels)
            plt.xlabel('Viewpoint')
            plt.ylabel('Likert Scale')
            plt.savefig(f'{save_dir}/{uparam}_scale_{self.scale[uparam]}',
                        dpi=self.dpi, bbox_inches='tight')
            plt.close()

    @staticmethod
    def grouping_folder_names(likert_mean):
        """
        We want 3 groups, but in case we want only two,
        we split the middle group again.
        """
        step_size = round((5 - 1) / 3, 2)
        if likert_mean <= 1 + step_size:
            return "1,00-2,33"
        elif likert_mean <= 1 + step_size + step_size / 2:
            return "2,34-3,00"
        elif likert_mean <= 1 + 2 * step_size:
            return "3,01-3,66"
        else:
            return "3,67-5,00"

    def create_boxplots(self, question: dict, sum_viewpoints=False, only_hist=False):
        """
        TODO
        """
        for ba_num in self.get_loops(question):
            subdir = f'all_viewpoints'
            if sum_viewpoints:
                subdir = f'viewpoint_avg'
            save_dir = f'{self.out_dir[ba_num]}{subdir}/boxplots/{question["prefix"]}'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            stats = self.load_statistics(question, ba_num)

            scatter_data = []
            loop_desc = f'Creating {question["prefix"]} boxplots (BA {ba_num})'
            for uparam, dfs_of_vps in tqdm(stats.items(), loop_desc):
                hist_data = []
                if sum_viewpoints:
                    # sum over viewpoints
                    raw_all = []
                    for i, (pose_name, vp_dict) in enumerate(dfs_of_vps.items()):
                        raw_all.extend(vp_dict['raw'])
                    scatter_data.append([uparam, np.mean(raw_all)])
                    hist_data.append(['proxy', raw_all])
                else:
                    for i, (pose_name, vp_dict) in enumerate(dfs_of_vps.items()):
                        hist_data.append([pose_name, vp_dict['raw']])
                        scatter_data.append([pose_name, np.mean(vp_dict['raw'])])

                if not only_hist:
                    for pose_name, hd in hist_data:
                        fig, ax = plt.subplots(1, 2)
                        if sum_viewpoints:
                            fig.suptitle(f'{uparam} (Scale = {self.scale[uparam]})')
                        else:
                            fig.suptitle(pose_name)

                        ax[0].boxplot(hd, positions=[0])
                        ax[0].plot([0], np.mean(hd), '+',
                                   label=f'Mean\n({round(np.mean(hd), 2)})')
                        ax[0].set_ylim((question['likert_min'] - 1, question['likert_max'] + 1))
                        ax[0].set_yticks(range(question['likert_min'], question['likert_max'] + 1))
                        ax[0].set_yticklabels(range(question['likert_min'],
                                                    question['likert_max'] + 1))
                        ax[0].set_ylabel(f'{question["likert_str_min"]}     =>     '
                                         f'{question["likert_str_max"]}')
                        ax[0].tick_params(labelbottom=False, bottom=False)
                        ax[0].legend(frameon=False)

                        if sum_viewpoints:
                            im = mpimg.imread(f'../input/stim_images/{uparam}_Viewpoint_2_scale_'
                                              f'{self.scale[uparam]}.png')
                            ax[1].set_title('Viewpoint 2')
                        else:
                            im = mpimg.imread(f'../input/stim_images/{pose_name}.png')
                            vi = pose_name.find("View")
                            ax[1].set_title(f'Viewpoint {pose_name[vi+10:vi+11]}')

                        ax[1].tick_params(left=False, labelleft=False,
                                          labelbottom=False, bottom=False)
                        ax[1].imshow(im)

                        final_dir = BehavioralAnalysis.grouping_folder_names(np.mean(hd))
                        subfolder = f'{save_dir}/{final_dir}'
                        if not os.path.exists(subfolder):
                            os.mkdir(subfolder)
                        save_path = f'{subfolder}/{uparam}_scale_{self.scale[uparam]}'
                        if not sum_viewpoints:
                            save_path = f'{subfolder}/{pose_name}'
                        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
                        plt.close()

            scatter_data = np.array(scatter_data)
            # Sort by value, but keep (name, value) setup
            scatter_data = scatter_data[np.argsort(scatter_data[:, 1])]
            scatter_data = np.transpose(scatter_data)
            float_value_arr = np.array(scatter_data[1], dtype=np.float)

            # Plot histogram of the posture means (incl. normal)
            mu, std = norm.fit(float_value_arr)
            plt.hist(float_value_arr, bins=15, density=False, label=f'mu = {round(mu, 2)}, std = {round(std, 2)}')
            plt.ylabel('Number of stimuli')
            plt.xlabel(f'{question["likert_str_min"]}     =>     '
                       f'{question["likert_str_max"]}')
            plt.xlim((question['likert_min'] - 1, question['likert_max'] + 1))
            plt.xticks(range(question['likert_min'], question['likert_max'] + 1),
                       range(question['likert_min'], question['likert_max'] + 1))
            # Plot normal distribution
            # xmin, xmax = plt.xlim()
            # x = np.linspace(xmin, xmax, 100)
            # p = norm.pdf(x, mu, std)
            # plt.plot(x, p, 'k', linewidth=2,
            #          label=f'mu = {round(mu, 2)}, std = {round(std, 2)}')
            plt.legend()
            save_path = f'{save_dir}/{question["prefix"]}_hist_all_vps'
            if sum_viewpoints:
                save_path = f'{save_dir}/{question["prefix"]}_hist_vp_avg'
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            plt.close()

            # Print & export overview of values
            if sum_viewpoints:
                out_file = open(f'{save_dir}/{question["prefix"]}_values_vps_avg.txt', 'w')
            else:
                out_file = open(f'{save_dir}/{question["prefix"]}_values_all_vps.txt', 'w')

            out_file.write(f'Stimuli, {question["likert_str_min"]} '
                           f'({question["likert_min"]}) => {question["likert_str_max"]}'
                           f'({question["likert_max"]})\n\n')
            last_group = BehavioralAnalysis.grouping_folder_names(float(scatter_data[1][0]))
            groups_in_total = []
            for i in range(len(scatter_data[0])):
                if sum_viewpoints:
                    out_str = f'{format(scatter_data[0][i] + " (" + self.scale[scatter_data[1][i]] + "),", " <30")}'
                else:
                    out_str = f'{format(scatter_data[0][i] + ", ", " <43")}'

                out_str += f'{round(float(scatter_data[1][i]), 2)}\n'
                out_file.write(out_str)
                curr_group = BehavioralAnalysis.grouping_folder_names(float(scatter_data[1][i]))
                groups_in_total.append(curr_group)
                if last_group is not curr_group:
                    out_file.write('\n')
                    last_group = curr_group
            count = Counter(groups_in_total)
            out_file.write(f'\nNumber of stimuli in groups:')
            for k, v in count.items():
                out_file.write(f'\n{k}: {v}')
            out_file.close()

    def barplot(self, question: dict, sum_viewpoints=False, hist_only=False):
        for ba_num in self.get_loops(question):
            ba_num = str(ba_num)
            subdir = f'viewpoint_avg' if sum_viewpoints else f'all_viewpoints'
            save_dir = f'{self.out_dir[ba_num]}{subdir}/barplots/{question["prefix"]}'
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            stats = self.load_statistics(question, ba_num)

            hist_data = []
            loop_desc = f'Creating {question["prefix"]} barplots (BA {ba_num})'
            for uparam, dfs_of_vps in tqdm(stats.items(), loop_desc):
                hist_uparam = []
                if sum_viewpoints:
                    raw_all = []
                    for i, (pose_name, vp_dict) in enumerate(dfs_of_vps.items()):
                        raw_all.extend(vp_dict['raw'])
                    hist_uparam.append(['proxy', raw_all])
                else:
                    for i, (pose_name, vp_dict) in enumerate(dfs_of_vps.items()):
                        hist_uparam.append([pose_name, vp_dict['raw']])
                for pose_name, hu in hist_uparam:
                    count = Counter(hu)
                    names = list(question['categories'].values())
                    keys = list(question['categories'].keys())
                    values = [0] * len(keys)
                    for k, v in count.items():
                        ind = keys.index(k)
                        values[ind] = v
                    max_ind = int(np.argmax(values))
                    max_name = names[max_ind]
                    hist_data.append(max_name)
                    if not hist_only:
                        fig, ax = plt.subplots(1, 2, gridspec_kw={'width_ratios': [2, 1]})
                        if sum_viewpoints:
                            fig.suptitle(f'{uparam} (Scale = {self.scale[uparam]})')
                        else:
                            fig.suptitle(pose_name)

                        ax[0].bar(names, values)
                        ax[0].tick_params(labelrotation=45)

                        if sum_viewpoints:
                            im = mpimg.imread(f'../input/stim_images/{uparam}_Viewpoint_2_scale_'
                                              f'{self.scale[uparam]}.png')
                            ax[1].set_title('Viewpoint 2')
                        else:
                            im = mpimg.imread(f'../input/stim_images/{pose_name}.png')
                            vi = pose_name.find("View")
                            ax[1].set_title(f'Viewpoint {pose_name[vi+10:vi+11]}')

                        ax[1].tick_params(left=False, labelleft=False,
                                          labelbottom=False, bottom=False)
                        ax[1].imshow(im)

                        if not os.path.exists(f'{save_dir}/{max_name}'):
                            os.mkdir(f'{save_dir}/{max_name}')
                        save_path = f'{save_dir}/{max_name}/{uparam}_scale_{self.scale[uparam]}'
                        if not sum_viewpoints:
                            save_path = f'{save_dir}/{max_name}/{pose_name}'
                        plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
                        plt.close()

            # Histogram of max categories
            hist_count = Counter(hist_data)
            keys = (hist_count.keys())
            values = list(hist_count.values())
            # - Add labels on top of bars
            bars = range(0, len(values)+1)
            plt.bar(keys, values)
            plt.xticks(rotation=45)
            plt.ylabel("Number of stimuli")
            for i in range(len(values)):
                plt.annotate(str(values[i]), xy=(bars[i], values[i]), ha='center', va='bottom')
            suffix = 'vp-avg' if sum_viewpoints else 'all-vps'
            plt.savefig(f'{save_dir}/{question["prefix"]}_bar_{suffix}',
                        dpi=self.dpi, bbox_inches='tight')
            plt.close()

    def get_loops(self, question: dict):
        # Check BA's we want to calculate plots for
        quest_ba_type = question['behavioral_analysis']
        ba_for_quest = []
        for i in self.ba_numbers:
            if i == 'all':
                if 2 in quest_ba_type:
                    ba_for_quest.append(i)
            elif int(i) in quest_ba_type:
                ba_for_quest.append(i)

        return ba_for_quest


