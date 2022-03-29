import numpy as np
import pickle
from typing import Tuple
import os

from numpy import ndarray

"""

    File: group_poss_real.py
    Author: MA Gehrke
    Date: 15.03.2022
    
    We are grouping the stimuli regarding to 
    their values of reality and possiblity
    in the behavioral analysis.
"""


def average_for_each_viewpoint(data) -> Tuple[ndarray, ndarray]:
    pose_names = []
    avg_data = []
    for uparam in data:
        # Take average of each stimuli
        for pose_name in data[uparam]:
            avg_data.append(np.mean(data[uparam][pose_name]['raw']))
            pose_names.append(pose_name)
    return np.array(pose_names), np.array(avg_data)


# Get data
with open(f'../output/all/stat_dicts/possibility_dict.pkl', "rb") as input_file:
    poss_data = pickle.load(input_file)
with open(f'../output/all/stat_dicts/realism_dict.pkl', "rb") as input_file:
    real_data = pickle.load(input_file)

poss_posenames, poss_avg_data = average_for_each_viewpoint(poss_data)
real_posenames, real_avg_data = average_for_each_viewpoint(real_data)

save_dir = f'../output/all/all_viewpoints/grouping/'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
# --------------------------------------------------------------------------- #
"""
    4 Groups.
    DISCARD average stimuli.
    We discard the middle group and only take into
    account stimuli that fall in both categories 
    into the upper or lower third.
"""
p_high_r_high = []
p_high_r_low = []
p_low_r_high = []
p_low_r_low = []

for poss_ind, pose in enumerate(poss_posenames):
    real_ind = np.where(real_posenames == pose)[0]
    assert len(real_ind) == 1
    real_ind = real_ind[0]
    poss_val = round(poss_avg_data[poss_ind], 3)
    real_val = round(real_avg_data[real_ind], 3)

    if poss_val > 3.66 and real_val > 3.66:
        p_high_r_high.append([pose, poss_val, real_val])
    elif poss_val > 3.66 and real_val < 2.34:
        p_high_r_low.append([pose, poss_val, real_val])
    elif poss_val < 2.34 and real_val > 3.66:
        p_low_r_high.append([pose, poss_val, real_val])
    elif poss_val < 2.34 and real_val < 2.34:
        p_low_r_low.append([pose, poss_val, real_val])

# PRINTING
out_file = open(f'{save_dir}grouping_poss_real_3categories.txt', 'w')
out_file.write(f'Behavioral Questions: Possiblity & Realism\n')
out_file.write(f'Cutoff points: high > 3.66, low < 2.34.\n\n')
out_file.write(f'Number of Stimuli:\n')
group_stack = [p_high_r_high, p_high_r_low, p_low_r_high, p_low_r_low]
group_names = ['Poss high, real high: ', 'Poss high, real low: ',
               'Poss low, real high: ', 'Poss low, real low: ']
for g_name, g in zip(group_names, group_stack):
    out_file.write(f'{g_name}{len(g)}\n')
for g_name, g in zip(group_names, group_stack):
    out_file.write(f'\n{g_name}\n')
    g_strings = [''.join(str(x)) for x in g]
    g_strings = [x + '\n' for x in g_strings]
    out_file.writelines(g_strings)
out_file.close()


# --------------------------------------------------------------------------- #
"""
    4 Groups.
    USE ALL stimuli.
    The split criterion is at 3.
"""
p_high_r_high = []
p_high_r_low = []
p_low_r_high = []
p_low_r_low = []

for poss_ind, pose in enumerate(poss_posenames):
    real_ind = np.where(real_posenames == pose)[0]
    assert len(real_ind) == 1
    real_ind = real_ind[0]
    poss_val = poss_avg_data[poss_ind]
    real_val = real_avg_data[real_ind]

    if poss_val > 3 and real_val > 3:
        p_high_r_high.append([pose, poss_val, real_val])
    elif poss_val > 3 and real_val <= 3:
        p_high_r_low.append([pose, poss_val, real_val])
    elif poss_val <= 3 and real_val > 3:
        p_low_r_high.append([pose, poss_val, real_val])
    elif poss_val <= 3 and real_val <= 3:
        p_low_r_low.append([pose, poss_val, real_val])

# PRINTING
out_file = open(f'{save_dir}grouping_poss_real_2categories.txt', 'w')
out_file.write(f'Behavioral Questions: Possiblity & Realism\n')
out_file.write(f'Cutoff points: high > 3, low <= 3.\n\n')
out_file.write(f'Number of Stimuli:\n')
group_stack = [p_high_r_high, p_high_r_low, p_low_r_high, p_low_r_low]
group_names = ['Poss high, real high: ', 'Poss high, real low: ',
               'Poss low, real high: ', 'Poss low, real low: ']
for g_name, g in zip(group_names, group_stack):
    out_file.write(f'{g_name}{len(g)}\n')
for g_name, g in zip(group_names, group_stack):
    out_file.write(f'\n{g_name}\n')
    g_strings = [''.join(str(x)) for x in g]
    g_strings = [x + '\n' for x in g_strings]
    out_file.writelines(g_strings)
out_file.close()


