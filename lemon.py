### imports
from tkinter import filedialog, Tk
import os
import shutil
import pandas as pd
import datetime
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

### options
pd.options.mode.chained_assignment = None

### clear folders
root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
asheets_path = os.path.join(root_path, "lemon", "web", "sheets", "active-sheets")
sheets_path = os.path.join(root_path, "lemon", "web", "sheets")
acharts_path = os.path.join(root_path, "lemon", "web", "charts", "active-charts")
charts_path = os.path.join(root_path, "lemon", "web", "charts")

i = 0
while i==0:
    source = asheets_path
    target = sheets_path
    files = os.listdir(source)
    for file in files:
        shutil.copy(os.path.join(source, file), target)
        os.remove(os.path.join(source, file))
    i = 1

i = 0
while i==0:
    source = acharts_path
    target = charts_path
    files = os.listdir(source)
    for file in files:
        os.remove(os.path.join(source, file))
    i = 1

### eel
import eel
eel.init('web')

### functions
@eel.expose
def import_sheet(name):
    root = Tk()
    root.iconbitmap("lemon2.ico")
    root.title("Lemon Charts")
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    file = filedialog.askopenfilename(initialdir=sheets_path)
    root.destroy()
    filename = os.path.basename(file)
    dirfile = os.path.dirname(file)
    shutil.copyfile(file, os.path.join(asheets_path, name + ".csv"))

@eel.expose
def clear_active_sheets():
    source = asheets_path
    target = sheets_path
    files = os.listdir(source)
    for file in files:
        shutil.move(os.path.join(source, file), target)

@eel.expose
def update_data(wgen, hours, runs):

    wgen = float(wgen)
    hours = float(hours)
    runs = float(runs)

    raw_lists = []
    for filename in os.listdir(asheets_path):
        print(filename)
        with open(os.path.join(asheets_path, filename)) as f:
            f_reader = csv.reader(f)
            header = next(f_reader)
            rows = []
            i = 0
            for row in f_reader:
                nrow = row[0:2]
                nrow.extend([row[4], row[35]])
                nrow.append(filename[:-4])
                rows.append(nrow)
                i += 1
                if i > runs:
                    break
            raw_lists += rows

    enter_df = pd.DataFrame(raw_lists, columns = [
    "date_and_time", "rta", "nether", "seed", "runner"])

    enter_df = enter_df.drop_duplicates(subset = "seed")

    enter_df = enter_df.loc(axis = 1)["runner", "date_and_time", "rta", "nether", "seed"]
    enter_df = enter_df.convert_dtypes()
    time_columns = ["date_and_time", "rta", "nether"]
    for i in time_columns:
        enter_df[i] = pd.to_datetime(enter_df[i], errors = 'coerce')

    for i in ["rta", "nether"]:
        t = enter_df[i]
        seconds = 60*(t.dt.minute) + t.dt.second
        enter_df[i] = seconds

    enter_df["count"] = 0
    enter_df["nether_tf"] = 0
    enter_df["nether_indicator"] = 0
    enter_df["count"] = enter_df.groupby(["runner"]).cumcount()
    enter_df["nether_tf"] = pd.isna(enter_df["nether"])
    enter_df["nether_indicator"] = enter_df["nether_tf"].apply(lambda x: (1 if x == False else 0))

    # removes times > 18 min and times > 4:15 that don't enter nether and times < :25 that enter nether
    enter_df = enter_df.query("rta <= 1000")
    enter_df = enter_df.query("(rta <= 255) or (nether_indicator == 1)")
    enter_df = enter_df.query("(nether > 25) or (nether_indicator == 0)")

    stat_csv = open("enter_stats.csv", "w", newline="")
    stat_csv.write(enter_df.to_csv())
    stat_csv.close()

    # abstract dataframe
    abstract_df = enter_df.copy()
    abstract_df["loads"] = 0
    abstract_df["abstract_rta"] = 0
    abstract_df["cum_nethers"] = 0
    abstract_df["nethers_per_hour"] = 0.0
    abstract_df["avg_enter"] = 0.0
    abstract_df["loads"] = wgen * abstract_df["count"]
    abstract_df["abstract_rta"] = abstract_df.groupby(["runner"])["rta"].cumsum()
    abstract_df["abstract_rta"] = abstract_df["abstract_rta"] + abstract_df["loads"]
    abstract_df["cum_nethers"] = abstract_df.groupby(['runner'])['nether_indicator'].cumsum()

    def get_nph_ae(df):
        for ind in df.index:
            arta = df["abstract_rta"][ind]
            if arta >= 3600*hours:
                arta2 = arta-(3600*hours)
                nethers = df.loc[(df['abstract_rta'] > arta2) & (df['abstract_rta'] <= arta)]
                nethers_per_hour = (nethers["nether_indicator"].sum()) / (hours)
                nether_count = (nethers["nether_indicator"].sum())
                average_enter = (nethers["nether"].sum()) / nether_count
                df.at[ind, "nethers_per_hour"] = nethers_per_hour
                df.at[ind, "avg_enter"] = average_enter
        return df

    abstract_df = abstract_df.groupby(["runner"]).apply(get_nph_ae)

    abstract_df = abstract_df.loc[abstract_df["nethers_per_hour"] * abstract_df["avg_enter"] != 0]

    stat_csv = open("abstract_stats.csv", "w", newline="")
    stat_csv.write(abstract_df.to_csv())
    stat_csv.close()

    # session dataframe
    runners = enter_df.groupby(["runner"])
    runner_keys = runners.groups.keys()
    session_df = pd.DataFrame()
    for runner in runner_keys:
        runner_df = runners.get_group(runner)
        summ_df = runner_df.resample('D', on='date_and_time').agg(
            dict(rta='sum',
                 nether = 'mean',
                 count = 'count',
                 nether_indicator='sum'))
        summ_df.reset_index(level=0, inplace=True)
        summ_df.insert(0, "runner", runner)
        session_df = session_df.append(summ_df)
        print(summ_df)
        print(session_df)
    session_df.dropna(inplace=True)
    session_df['seconds'] = session_df['rta'] + session_df['count']*wgen
    session_df['hours'] = session_df['seconds'] / 3600
    session_df['nethers_per_hour'] = session_df['nether_indicator'] / session_df['hours']

    session_csv = open("session_stats.csv", "w", newline="")
    session_csv.write(session_df.to_csv())
    session_csv.close()



    print("data updated successfully")

@eel.expose
def clear_charts():
    i = 0
    while i==0:
        source = acharts_path
        files = os.listdir(source)
        for file in files:
            os.remove(os.path.join(source, file))
        i = 1

@eel.expose
def gen_charts(hours, i_nph_dist, i_ae_dist, i_hist, i_contour, i_nph_time, i_ae_time, i_nph_line, i_ae_line,
                    v_nph_dist, v_ae_dist, v_hist, v_contour, v_nph_time, v_ae_time, v_nph_line, v_ae_line,
                    c_nph_dist, c_ae_dist, c_hist, c_contour, c_nph_time, c_ae_time, c_nph_line, c_ae_line):

    clear_charts()
    hours = float(hours)
    sns.set_theme()
    sns.set_style("whitegrid", {'axes.grid' : False})
    abstract_df = pd.read_csv("abstract_stats.csv")
    session_df = pd.read_csv("session_stats.csv")
    enter_df = pd.read_csv("enter_stats.csv")

    ### seaborn settings
    plt.rcParams["font.family"] = ['Trebuchet MS', 'sans-serif']
    colors = ["#D5BB67", "#4878D0", "#6ACC64", "#EE854A", "#D65F5F", "#956CB4",
              "#8C613C", "#DC7EC0", "#797979", "#82C6E2"]

    custom_pal = sns.set_palette(sns.color_palette(colors))

    ### individual charts
    abstract_df=abstract_df.rename(columns = {'runner':'Runner'})
    session_df=session_df.rename(columns = {'runner':'Runner'})
    enter_df=enter_df.rename(columns = {'runner':'Runner'})
    runners = abstract_df.groupby(['Runner'])
    runners2 = session_df.groupby(['Runner'])
    runners3 = enter_df.groupby(['Runner'])
    runner_keys = runners.groups.keys()

    enter_df["date_and_time"] = pd.to_datetime(enter_df["date_and_time"])
    session_df["date_and_time"] = pd.to_datetime(session_df["date_and_time"])

    if i_nph_dist == True:
        for runner in runner_keys:
            runner_df = runners.get_group(runner)
            sns.displot(data=runner_df, x="nethers_per_hour", hue="Runner", binwidth=1/hours, element="step", palette=custom_pal)
            plt.xlabel("Nethers Per Hour", labelpad=10)
            plt.ylabel("Count", labelpad=10)
            plt.savefig(os.path.join("web", "charts", "active-charts", str(runner) + "_NPH_distribution.png"), dpi=1000)
            plt.close()

    if i_ae_dist == True:
        for runner in runner_keys:
            runner_df = runners.get_group(runner)
            sns.displot(data=runner_df, x="avg_enter", hue="Runner", binwidth=2, element="step", palette=custom_pal)
            plt.xlabel("Average Enter", labelpad=10)
            plt.ylabel("Count", labelpad=10)
            plt.savefig(os.path.join("web", "charts", "active-charts", str(runner) + "_AE_distribution.png"), dpi=1000)
            plt.close()

    if i_hist == True:
        for runner in runner_keys:
            runner_df = runners.get_group(runner)
            sns.displot(data=runner_df, x="nethers_per_hour", y="avg_enter", hue="Runner", binwidth=((1/hours)+0.1, 2), palette=custom_pal)
            plt.xlabel("Nethers Per Hour", labelpad=10)
            plt.ylabel("Average Enter", labelpad=10)
            plt.savefig(os.path.join("web", "charts", "active-charts", str(runner) + "_hist.png"), dpi=1000)
            plt.close()

    if i_contour == True:
        for runner in runner_keys:
            runner_df = runners.get_group(runner)
            sns.displot(data=runner_df, x="nethers_per_hour", y="avg_enter", kind="kde", levels=5, fill=True, alpha=0.4, hue="Runner", palette=custom_pal)
            plt.xlabel("Nethers Per Hour", labelpad=10)
            plt.ylabel("Average Enter", labelpad=10)
            plt.savefig(os.path.join("web", "charts", "active-charts", str(runner) + "_contour.png"), dpi=1000)
            plt.close()

    if i_nph_time == True:
        for runner in runner_keys:
            runner_df = runners2.get_group(runner)
            fig, ax = plt.subplots()
            sns.lineplot(data=runner_df, ax=ax, x="date_and_time", y="nethers_per_hour", hue="Runner", palette=custom_pal)
            fig.autofmt_xdate()
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d-%y'))
            plt.xlabel("Date", labelpad=3)
            plt.ylabel("Nethers Per Hour", labelpad=10)
            plt.savefig(os.path.join("web", "charts", "active-charts", str(runner) + "_NPH_timeline_plot.png"), dpi=500)
            plt.close()

    if i_ae_time == True:
        for runner in runner_keys:
            runner_df = runners2.get_group(runner)
            fig, ax = plt.subplots()
            sns.lineplot(data=runner_df, ax=ax, x="date_and_time", y="nether", hue="Runner", palette=custom_pal)
            fig.autofmt_xdate()
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d-%y'))
            plt.xlabel("Date", labelpad=3)
            plt.ylabel("Average Enter", labelpad=10)
            plt.savefig(os.path.join("web", "charts", "active-charts", str(runner) + "_AE_timeline_plot.png"), dpi=500)
            plt.close()

    if i_nph_line == True:
        for runner in runner_keys:
            runner_df = runners.get_group(runner)
            runner_df = runner_df.round({'count':-2})
            sns.lineplot(data=runner_df, x="count", y="nethers_per_hour", hue="Runner", palette=custom_pal, ci=None)
            plt.xlabel("Count", labelpad=3)
            plt.ylabel("Nethers Per Hour", labelpad=10)
            plt.savefig(os.path.join("web", "charts", "active-charts", str(runner) + "_NPH_line_plot.png"), dpi=500)
            plt.close()

    if i_ae_line == True:
        for runner in runner_keys:
            runner_df = runners.get_group(runner)
            runner_df = runner_df.round({'count':-3})
            sns.lineplot(data=runner_df, x="count", y="nether", hue="Runner", palette=custom_pal, ci=None)
            plt.xlabel("Count", labelpad=3)
            plt.ylabel("Average Enter", labelpad=10)
            plt.savefig(os.path.join("web", "charts", "active-charts", str(runner) + "_AE_line_plot.png"), dpi=500)
            plt.close()

    ### versus charts
    abstract_df=abstract_df.rename(columns = {'Runner':'Runners'})
    session_df=session_df.rename(columns = {'Runner':'Runners'})
    enter_df=enter_df.rename(columns = {'Runner':'Runners'})

    if v_nph_dist == True:
        sns.displot(data=abstract_df, x="nethers_per_hour", hue="Runners", binwidth=1/hours, element="step", palette=custom_pal)
        plt.xlabel("Nethers Per Hour", labelpad=10)
        plt.ylabel("Count", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "versus_NPH_distribution.png"), dpi=1000)
        plt.close()

    if v_ae_dist == True:
        sns.displot(data=abstract_df, x="avg_enter", hue="Runners", binwidth=2, element="step", palette=custom_pal)
        plt.xlabel("Average Enter", labelpad=10)
        plt.ylabel("Count", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "versus_AE_distribution.png"), dpi=1000)
        plt.close()

    if v_hist == True:
        sns.displot(data=abstract_df, x="nethers_per_hour", y="avg_enter", hue="Runners", binwidth=((1/hours)+0.1, 2), palette=custom_pal)
        plt.xlabel("Nethers Per Hour", labelpad=10)
        plt.ylabel("Average Enter", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "versus_hist.png"), dpi=1000)
        plt.close()

    if v_contour == True:
        sns.displot(data=abstract_df, x="nethers_per_hour", y="avg_enter", kind="kde", levels=5, fill=True, alpha=0.4, hue="Runners", palette=custom_pal)
        plt.xlabel("Nethers Per Hour", labelpad=10)
        plt.ylabel("Average Enter", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "versus_contour.png"), dpi=1000)
        plt.close()

    if v_nph_time == True:
        fig, ax = plt.subplots()
        sns.lineplot(data=session_df, ax=ax, x="date_and_time", y="nethers_per_hour", hue="Runners", palette=custom_pal)
        fig.autofmt_xdate()
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d-%y'))
        plt.xlabel("Date", labelpad=3)
        plt.ylabel("Nethers Per Hour", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "versus_NPH_timeline_plot.png"), dpi=500)
        plt.close()

    if v_ae_time == True:
        fig, ax = plt.subplots()
        sns.lineplot(data=session_df, ax=ax, x="date_and_time", y="nether", hue="Runners", palette=custom_pal)
        fig.autofmt_xdate()
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d-%y'))
        plt.xlabel("Date", labelpad=3)
        plt.ylabel("Average Enter", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "versus_AE_timeline_plot.png"), dpi=500)
        plt.close()

    if v_nph_line == True:
        abstract_df = abstract_df.round({'count':-2})
        sns.lineplot(data=abstract_df, x="count", y="nethers_per_hour", hue="Runners", palette=custom_pal, ci=None)
        plt.xlabel("Count", labelpad=3)
        plt.ylabel("Nethers Per Hour", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "versus_NPH_line_plot.png"), dpi=500)
        plt.close()

    if v_ae_line == True:
        abstract_df = abstract_df.round({'count':-3})
        sns.lineplot(data=abstract_df, x="count", y="nether", hue="Runners", palette=custom_pal, ci=None)
        plt.xlabel("Count", labelpad=3)
        plt.ylabel("Average Enter", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "versus_AE_line_plot.png"), dpi=500)
        plt.close()

    ### cumulative charts
    if c_nph_dist == True:
        sns.displot(data=abstract_df, x="nethers_per_hour", binwidth=1/hours, element="step", palette=custom_pal)
        plt.xlabel("Nethers Per Hour", labelpad=10)
        plt.ylabel("Count", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "cumulative_NPH_distribution.png"), dpi=1000)
        plt.close()

    if c_ae_dist == True:
        sns.displot(data=abstract_df, x="avg_enter", binwidth=2, element="step", palette=custom_pal)
        plt.xlabel("Average Enter", labelpad=10)
        plt.ylabel("Count", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "cumulative_AE_distribution.png"), dpi=1000)
        plt.close()

    if c_hist == True:
        sns.displot(data=abstract_df, x="nethers_per_hour", y="avg_enter", binwidth=((1/hours)+0.1, 2), palette=custom_pal)
        plt.xlabel("Nethers Per Hour", labelpad=10)
        plt.ylabel("Average Enter", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "cumulative_hist.png"), dpi=1000)
        plt.close()

    if c_contour == True:
        sns.displot(data=abstract_df, x="nethers_per_hour", y="avg_enter", kind="kde", levels=5, fill=True, alpha=0.4, palette=custom_pal)
        plt.xlabel("Nethers Per Hour", labelpad=10)
        plt.ylabel("Average Enter", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "cumulative_contour.png"), dpi=1000)
        plt.close()

    if c_nph_time == True:
        fig, ax = plt.subplots()
        sns.lineplot(data=session_df, ax=ax, x="date_and_time", y="nethers_per_hour", palette=custom_pal)
        fig.autofmt_xdate()
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d-%y'))
        plt.xlabel("Date", labelpad=3)
        plt.ylabel("Nethers Per Hour", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "cumulative_NPH_timeline_plot.png"), dpi=500)
        plt.close()

    if c_ae_time == True:
        fig, ax = plt.subplots()
        sns.lineplot(data=session_df, ax=ax, x="date_and_time", y="nether", palette=custom_pal)
        fig.autofmt_xdate()
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d-%y'))
        plt.xlabel("Date", labelpad=3)
        plt.ylabel("Average Enter", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "cumulative_AE_timeline_plot.png"), dpi=500)
        plt.close()

    if c_nph_line == True:
        abstract_df = abstract_df.round({'count':-2})
        sns.lineplot(data=abstract_df, x="count", y="nethers_per_hour", palette=custom_pal, ci=None)
        plt.xlabel("Count", labelpad=3)
        plt.ylabel("Nethers Per Hour", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "cumulative_NPH_line_plot.png"), dpi=500)
        plt.close()

    if c_ae_line == True:
        abstract_df = abstract_df.round({'count':-3})
        sns.lineplot(data=abstract_df, x="count", y="nether", palette=custom_pal, ci=None)
        plt.xlabel("Count", labelpad=3)
        plt.ylabel("Average Enter", labelpad=10)
        plt.savefig(os.path.join("web", "charts", "active-charts", "cumulative_AE_line_plot.png"), dpi=500)
        plt.close()

@eel.expose
def list_images():
    image_files = os.listdir(os.path.join("web", "charts", "active-charts"))
    image_paths = []
    for file in image_files:
        image_paths.append(os.path.join('charts', 'active-charts', file))
    print("charts successfully generated")
    return image_paths

### eel
eel.start('main.html', size=(1100, 650))
