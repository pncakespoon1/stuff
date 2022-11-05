import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pygsheets
import json
from datetime import timedelta
from datetime import datetime
import math
import random
import gc
import statistics


path1 = "D:/ResetEfficiency/"
gc_sheets = pygsheets.authorize(service_file=path1 + "credentials.json")

jsonFile1 = open(path1 + "runners.json")
runners = json.load(jsonFile1)
jsonFileEK1 = open(path1 + 'effscore_keys1.json')
effscore_keys1 = json.load(jsonFileEK1)
jsonFileEK2 = open(path1 + 'effscore_keys2.json')
effscore_keys2 = json.load(jsonFileEK2)
target_time = 600
batch_size_1 = 4000
batch_size_2 = 20
es_interval = 1
session_threshold = 1


def get_sheet(sheetname):
    sh = gc_sheets.open(sheetname)
    wks = sh[1]
    return wks


def get_sessions():
    sessions = []
    for runner in runners:
        for sheetname in runner['sheet_names']:
            print(sheetname)
            sh = gc_sheets.open(sheetname)
            wks = sh[1]
            headers = wks.get_row(row=1, returnas='matrix', include_tailing_empty=False)
            timestamps = wks.get_col(col=1, include_tailing_empty=False, returnas='matrix')
            timestamps.pop(0)
            bt_col = wks.get_col(col=headers.index("BT") + 1, returnas='matrix', include_tailing_empty=True)
            bt_col.pop(0)
            start_row = 2
            valid_session = False
            for i in range(len(timestamps) - 1):
                timestamp_1 = datetime.strptime(timestamps[i], '%Y-%m-%d %H:%M:%S')
                timestamp_2 = datetime.strptime(timestamps[i+1], '%Y-%m-%d %H:%M:%S')
                if bt_col[i] != '':
                    valid_session = True
                if timestamp_1 - timestamp_2 > timedelta(hours=session_threshold) or i == len(timestamps) - 2:
                    end_row = i + 2
                    if valid_session:
                        sessions.append({'name': sheetname, 'start_row': start_row, 'end_row': end_row, 'version': runner['tracker_versions'][runner['sheet_names'].index(sheetname)]})
                    start_row = i + 3
                    valid_session = False
    return sessions


def get_stats(sheetname, tracker_version, use_subset, min_row, max_row):
    print(sheetname)
    gc.collect()
    min_row = min_row + 2
    max_row = max_row + 1
    entry_dist = []
    randomized_entry_dist = []
    entry_labels = []
    randomized_entry_labels = []
    entry_structure1 = []
    randomized_entry_structure1 = []
    entry_structure2 = []
    randomized_entry_structure2 = []
    entry_exit = []
    randomized_entry_exit = []
    entry_stronghold = []
    randomized_entry_stronghold = []
    exit_label = 'Eyes Crafted'
    if tracker_version in [2, 3]:
        exit_label = 'Nether Exit'
    wks = get_sheet(sheetname)
    headers = wks.get_row(row=1, returnas='matrix', include_tailing_empty=False)
    nether_col = wks.get_col(col=headers.index("Nether") + 1, returnas='matrix', include_tailing_empty=True)
    nether_col.pop(0)
    rta_col = wks.get_col(col=headers.index("RTA") + 1, returnas='matrix', include_tailing_empty=True)
    rta_col.pop(0)
    bt_col = wks.get_col(col=headers.index("BT") + 1, returnas='matrix', include_tailing_empty=True)
    bt_col.pop(0)
    bastion_col = wks.get_col(col=headers.index("Bastion") + 1, returnas='matrix', include_tailing_empty=True)
    bastion_col.pop(0)
    fortress_col = wks.get_col(col=headers.index("Fortress") + 1, returnas='matrix', include_tailing_empty=True)
    fortress_col.pop(0)
    exit_col = wks.get_col(col=headers.index(exit_label) + 1, returnas='matrix', include_tailing_empty=True)
    exit_col.pop(0)
    stronghold_col = wks.get_col(col=headers.index("Stronghold") + 1, returnas='matrix', include_tailing_empty=True)
    stronghold_col.pop(0)
    if use_subset:
        nether_col = nether_col[min_row:max_row]
        rta_col = rta_col[min_row:max_row]
        bt_col = bt_col[min_row:max_row]
    if tracker_version in [2, 3]:
        rta_since_prev_col = wks.get_col(col=headers.index("RTA Since Prev") + 1, returnas='matrix', include_tailing_empty=True)
        rta_since_prev_col.pop(0)
        if use_subset:
            rta_since_prev_col = rta_since_prev_col[min_row:max_row]
    nether_count = 0
    entry_sum = 0
    rta_sum = 0
    for cell_num in range(len(nether_col)):
        nether_cell = nether_col[cell_num]
        rta_cell = rta_col[cell_num]
        rta_cell = timedelta(hours=int(rta_cell[0:1]), minutes=int(rta_cell[2:4]), seconds=int(rta_cell[5:7])) / timedelta(seconds=1)
        if tracker_version in [2, 3]:
            rta_since_prev_cell = rta_since_prev_col[cell_num]
            rta_since_prev_cell = timedelta(hours=int(rta_since_prev_cell[0:1]), minutes=int(rta_since_prev_cell[2:4]), seconds=int(rta_since_prev_cell[5:7])) / timedelta(seconds=1)
            rta_sum += (rta_cell + rta_since_prev_cell)
        else:
            rta_sum += rta_cell
        bastion_cell = bastion_col[cell_num]
        if bastion_cell != '':
            bastion_cell = timedelta(hours=int(bastion_cell[0:1]), minutes=int(bastion_cell[2:4]), seconds=int(bastion_cell[5:7])) / timedelta(seconds=1)
        fortress_cell = fortress_col[cell_num]
        if fortress_cell != '':
            fortress_cell = timedelta(hours=int(fortress_cell[0:1]), minutes=int(fortress_cell[2:4]), seconds=int(fortress_cell[5:7])) / timedelta(seconds=1)
        exit_cell = exit_col[cell_num]
        if exit_cell != '':
            exit_cell = timedelta(hours=int(exit_cell[0:1]), minutes=int(exit_cell[2:4]), seconds=int(exit_cell[5:7])) / timedelta(seconds=1)
        stronghold_cell = stronghold_col[cell_num]
        if stronghold_cell != '':
            stronghold_cell = timedelta(hours=int(stronghold_cell[0:1]), minutes=int(stronghold_cell[2:4]),seconds=int(stronghold_cell[5:7])) / timedelta(seconds=1)
        if nether_cell != '':
            nether_cell = timedelta(hours=int(nether_cell[0:1]), minutes=int(nether_cell[2:4]), seconds=int(nether_cell[5:7])) / timedelta(seconds=1)
            nether_count += 1
            entry_sum += nether_cell
            rta_sum -= (rta_cell - nether_cell)
            entry_dist.append(nether_cell)
            if bt_col[cell_num] != '':
                entry_labels.append('bt')
            else:
                entry_labels.append('non-bt')
            if fortress_cell == '':
                entry_structure1.append(bastion_cell)
                entry_structure2.append(fortress_cell)
            else:
                if bastion_cell == '':
                    entry_structure1.append(fortress_cell)
                    entry_structure2.append(bastion_cell)
                else:
                    if bastion_cell < fortress_cell:
                        entry_structure1.append(bastion_cell)
                        entry_structure2.append(fortress_cell)
                    else:
                        entry_structure1.append(fortress_cell)
                        entry_structure2.append(bastion_cell)
            entry_stronghold.append(stronghold_cell)
            entry_exit.append(exit_cell)

    hours = rta_sum / 3600
    nph = nether_count / hours
    avg_enter = entry_sum / nether_count
    for i in range(100):
        index = random.randrange(0, len(entry_dist))
        randomized_entry_dist.append(entry_dist[index])
        randomized_entry_labels.append(entry_labels[index])
        randomized_entry_structure1.append(entry_structure1[index])
        randomized_entry_structure2.append(entry_structure2[index])
        randomized_entry_exit.append(entry_exit[index])
        randomized_entry_stronghold.append(entry_stronghold[index])
    stdev_enter = statistics.stdev(randomized_entry_dist)
    avg_RTA = rta_sum / len(rta_col)
    return nph, avg_enter, stdev_enter, randomized_entry_dist, randomized_entry_labels, randomized_entry_structure1, randomized_entry_structure2, randomized_entry_exit, randomized_entry_stronghold, avg_RTA


def get_efficiencyScore(nph, entry_distribution, entry_labels):
    sum = 0
    for entry in entry_distribution:
        if 390 <= (es_interval * (math.floor((target_time - entry) / es_interval))) <= 600:
            if entry_labels == 'bt':
                sum += effscore_keys1[1][effscore_keys1[0].index(target_time - entry)]
            else:
                sum += effscore_keys2[1][effscore_keys2[0].index(target_time - entry)]
    return nph * sum / len(entry_distribution)


def make_scatterplot1(nph_list, avg_enter_list, sheetname_list, runner_list):
    canvas = []
    for x in range(60, 140):
        canvas.append([])
        for y in range(90, 150):
            y = y / 1
            effscore = (x / 10) * (effscore_keys1[1][effscore_keys1[0].index(es_interval * (math.floor((target_time - y) / es_interval)))] + effscore_keys2[1][effscore_keys2[0].index(es_interval * (math.floor((target_time - y) / es_interval)))]) / 2
            (canvas[x - 60]).append(effscore)

    dict1 = {'nph': nph_list, 'avg_enter': avg_enter_list, 'runner': runner_list, 'sheetname': sheetname_list}

    x1 = np.linspace(6, 14.0, 60)
    x2 = np.linspace(90, 150, 80)
    x, y = np.meshgrid(x1, x2)
    cm = plt.cm.get_cmap('cividis')
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    p1 = plt.contourf(x, y, canvas, levels=1000)
    p2 = sns.scatterplot(x='nph', y='avg_enter', hue='runner', data=dict1, legend=False)
    plt.savefig(path1 + 'figures/scatterplot1.png', dpi=1000)
    plt.close()


def make_scatterplot2(nph_list, entry_dist_list, entry_labels_list, runner_list):
    new_efficiencyScore_list = []
    new_bt_proportion_list = []
    new_runner_list = []
    for i in range(len(entry_dist_list)):
        bt_label_count = 0
        for label in entry_labels_list[i]:
            if label == 'bt':
                bt_label_count += 1
        if bt_label_count != 0:
            new_efficiencyScore_list.append(get_efficiencyScore(nph_list[i], entry_dist_list[i], entry_labels_list[i]))
            new_bt_proportion_list.append(bt_label_count / len(entry_labels_list[i]))
            new_runner_list.append(runner_list[i])

    dict1 = {'efficiency_score': new_efficiencyScore_list, 'bt_proportion': new_bt_proportion_list, 'runner': new_runner_list}
    sns.scatterplot(x='efficiency_score', y='bt_proportion', hue='runner', data=dict1, legend=True)
    plt.savefig(path1 + 'figures/scatterplot2.png', dpi=1000)
    plt.close()


def make_scatterplot3(nph_list, entry_labels_list, runner_list):
    new_nph_list = []
    bt_proportion_list = []
    new_runner_list = []
    for i in range(len(nph_list)):
        bt_label_count = 0
        for label in entry_labels_list[i]:
            if label == 'bt':
                bt_label_count += 1
        if bt_label_count != 0:
            bt_proportion_list.append(bt_label_count / len(entry_labels_list[i]))
            new_nph_list.append(nph_list[i])
            new_runner_list.append(runner_list[i])

    dict1 = {'nph': new_nph_list, 'bt_proportion': bt_proportion_list, 'runner': new_runner_list}
    print(dict1)
    sns.scatterplot(x='nph', y='bt_proportion', hue='runner', data=dict1, legend=True)
    plt.savefig(path1 + 'figures/scatterplot4.png', dpi=1000)
    plt.close()


def make_scatterplot4(avg_enter_list, entry_labels_list, runner_list):
    new_avg_enter_list = []
    bt_proportion_list = []
    new_runner_list = []
    for i in range(len(avg_enter_list)):
        bt_label_count = 0
        for label in entry_labels_list[i]:
            if label == 'bt':
                bt_label_count += 1
        if bt_label_count != 0:
            bt_proportion_list.append(bt_label_count / len(entry_labels_list[i]))
            new_avg_enter_list.append(avg_enter_list[i])
            new_runner_list.append(runner_list[i])

    dict1 = {'avg_enter': new_avg_enter_list, 'bt_proportion': bt_proportion_list, 'runner': new_runner_list}
    print(dict1)
    sns.scatterplot(x='avg_enter', y='bt_proportion', hue='runner', data=dict1, legend=True)
    plt.savefig(path1 + 'figures/scatterplot4.png', dpi=1000)
    plt.close()


def make_histogram1(entry_dist_list):
    count = 0
    for runner in runners:
        runner_name = runner['twitch_name']
        print(runner_name)
        entry_dists_flattened = []
        entry_dists_flat_labels = []
        for sheetname in range(len(runner['sheet_names'])):
            for item in entry_dist_list[count]:
                if 7 < item < 210:
                    entry_dists_flattened.append(item)
                    entry_dists_flat_labels.append(sheetname)
            count += 1

        dict1 = {'entry_dist': entry_dists_flattened, 'sheetname': entry_dists_flat_labels}

        sns.kdeplot(data=dict1, x='entry_dist', hue='sheetname', legend=False, bw_adjust=0.9)
        plt.savefig(path1 + f'figures/histogram1_{runner_name}.png', dpi=1000)
        plt.close()


def make_histogram2(entry_dist_list, entry_labels_list):
    count = 0
    for runner in runners:
        for sheetname in runner['sheet_names']:
            entry_dist = []
            entry_labels = []
            for i in range(len(entry_dist_list[count])):
                if 7 < entry_dist_list[count][i] < 210:
                    entry_dist.append(entry_dist_list[count][i])
                    entry_labels.append(entry_labels_list[count][i])

            count += 1
            dict1 = {'entry_dist': entry_dist, 'sheetname': entry_labels}

            sns.kdeplot(data=dict1, x='entry_dist', hue='sheetname', legend=False, bw_adjust=0.9)
            plt.savefig(path1 + f'figures/histogram2_{sheetname}.png', dpi=1000)
            plt.close()


def make_histogram3(entry_dist_list, entry_exit_list, entry_labels_list, runner_list):
    exit_dist = []
    entry_labels = []
    for i1 in range(len(runner_list)):
        for i2 in range(len(entry_dist_list[i1])):
            if 7 < entry_dist_list[i1][i2] < 210:
                if entry_exit_list[i1][i2] != "":
                    exit_dist.append(entry_exit_list[i1][i2] - entry_dist_list[i1][i2])
                    entry_labels.append(entry_labels_list[i1][i2])
        if (i1 == len(runner_list) - 1) or (runner_list[i1] != runner_list[i1 + 1]):
            dict1 = {'entry_dist': exit_dist, 'sheetname': entry_labels}

            sns.kdeplot(data=dict1, x='entry_dist', hue='sheetname', legend=False, bw_adjust=0.9)
            plt.savefig(path1 + f'figures/histogram3_{runner_list[i1]}.png', dpi=1000)
            plt.close()


def makeplots(scatterplot1, scatterplot2, scatterplot3, scatterplot4, histogram1, histogram2, histogram3):
    nph_list1 = []
    avg_enter_list1 = []
    stdev_enter_list1 = []
    entry_dist_list1 = []
    entry_labels_list1 = []
    entry_structure1_list1 = []
    entry_structure2_list1 = []
    entry_exit_list1 = []
    entry_stronghold_list1 = []
    avg_RTA_list1 = []
    sheetname_list1 = []
    runner_list1 = []

    nph_list2 = []
    avg_enter_list2 = []
    stdev_enter_list2 = []
    entry_dist_list2 = []
    entry_labels_list2 = []
    entry_structure1_list2 = []
    entry_structure2_list2 = []
    entry_exit_list2 = []
    entry_stronghold_list2 = []
    avg_RTA_list2 = []
    sheetname_list2 = []
    runner_list2 = []

    sessions = get_sessions()

    for runner in runners:
        for i1 in range(len(runner['sheet_names'])):
            nph, avg_enter, stdev_enter, entry_dist, entry_labels, entry_structure1, entry_structure2, entry_exit, entry_stronghold, avg_RTA = get_stats(runner['sheet_names'][i1], runner['tracker_versions'][i1], False, 0, 0)
            nph_list1.append(nph)
            avg_enter_list1.append(avg_enter)
            stdev_enter_list1.append(stdev_enter)
            entry_dist_list1.append(entry_dist)
            entry_labels_list1.append(entry_labels)
            entry_structure1_list1.append(entry_structure1)
            entry_structure2_list1.append(entry_structure2)
            entry_exit_list1.append(entry_exit)
            entry_stronghold_list1.append(entry_stronghold)
            avg_RTA_list1.append(avg_RTA)
            sheetname_list1.append(runner['sheet_names'][i1])
            runner_list1.append(runner['twitch_name'])

    for session in sessions:
        nph, avg_enter, stdev_enter, entry_dist, entry_labels, entry_structure1, entry_structure2, entry_exit, entry_stronghold, avg_RTA = get_stats(session['name'], session['version'], True, session['start_row'], session['end_row'])
        nph_list2.append(nph)
        avg_enter_list2.append(avg_enter)
        stdev_enter_list2.append(stdev_enter)
        entry_dist_list2.append(entry_dist)
        entry_labels_list2.append(entry_labels)
        entry_structure1_list2.append(entry_structure1)
        entry_structure2_list2.append(entry_structure2)
        entry_exit_list2.append(entry_exit)
        entry_stronghold_list2.append(entry_stronghold)
        avg_RTA_list2.append(avg_RTA)
        sheetname_list2.append(session['name'])
        runner_list2.append(session['name'][:(len(session['name'])-1)])

    if scatterplot1:
        make_scatterplot1(nph_list2, avg_enter_list2, sheetname_list2, runner_list2)

    if scatterplot2:
        make_scatterplot2(nph_list2, entry_dist_list2, entry_labels_list2, runner_list2)

    if scatterplot3:
        make_scatterplot3(nph_list2, entry_labels_list2, runner_list2)

    if scatterplot4:
        make_scatterplot4(avg_enter_list2, entry_labels_list2, runner_list2)

    if histogram1:
        make_histogram1(entry_dist_list1)

    if histogram2:
        make_histogram2(entry_dist_list1, entry_labels_list1)

    if histogram3:
        make_histogram3(entry_dist_list2, entry_exit_list2, entry_labels_list2, runner_list2)


makeplots(True, True, True, True, True, True, True)
