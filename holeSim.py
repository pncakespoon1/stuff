import random
import pygsheets
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import scipy.stats as st
import math

obsidian_requirement = 10
pearl_requirement = 14
explosive_requirement = 4
potion_requirement = 1
bed_requirement = 0

start = 35
leftTripleLootTime = 45
leftSingleLootTime = 15

simNUM = 500000

path1 = "D:/ResetEfficiency/"
gc_sheets = pygsheets.authorize(service_file=path1 + "credentials.json")


def runTradeSim(chestNum):

    obsidian_trades = 0
    crying_obsidian_trades = 0
    string_trades = 0
    glowstone_dust_trades = 0
    potion_trades = 0
    pearl_trades = 0

    obsidian_chests = 0
    crying_obsidian_chests = 0
    string_chests = 0

    trades=0
    for i in range(chestNum):
        rolls = (random.randrange(3, 6))
        while rolls > 0:
            choose_item = (random.randrange(1, 12))
            if choose_item == 1:
                obsidian_chests += (random.randrange(4, 7))
            if choose_item == 2:
                crying_obsidian_chests += (random.randrange(1, 6))
            if choose_item == 3:
                string_chests += (random.randrange(4, 7))
            rolls -= 1
    while pearl_trades < pearl_requirement or potion_trades < potion_requirement or (obsidian_trades + obsidian_chests) < obsidian_requirement or (glowstone_dust_trades // 16) < (explosive_requirement - ((string_trades + string_chests) // 12)) or ((crying_obsidian_trades + crying_obsidian_chests) // 6) < (explosive_requirement - ((string_trades + string_chests) // 12)) or ((string_trades + string_chests) // 12) < bed_requirement:
        choose_trade = (random.randrange(1, 424))
        if 21 > choose_trade >= 1:
            pearl_trades += (random.randrange(4, 9))
        if 41 > choose_trade >= 21:
            potion_trades += 1
        if 61 > choose_trade >= 41:
            string_trades += (random.randrange(8, 25))
        if 81 > choose_trade >= 61:
            glowstone_dust_trades += (random.randrange(5, 13))
        if 121 > choose_trade >= 81:
            obsidian_trades += 1
        if 161 > choose_trade >= 121:
            crying_obsidian_trades += (random.randrange(1, 4))
        trades += 1
    if trades > 100:
        return 0
    else:
        return trades


def runRouteSim(piglins, finish, tenBarters):
    time = tenBarters
    floor = finish
    leftTriple = random.randrange(0, 2)
    if leftTriple == 1:
        floor += leftTripleLootTime
        chestNum = 6
    else:
        floor += leftSingleLootTime
        chestNum = 3
    trades = runTradeSim(chestNum)
    time += ((max((trades-10), 0)/piglins)*6)
    if trades > 0:
        return max(time, floor)
    else:
        return 0


def getListOfRouteTimes(high, exposed):
    routeTimeList = []

    sh = gc_sheets.open("bridgehole data")
    if high:
        wks = sh[2]
        if exposed:
            wks = sh[4]
    else:
        wks = sh[3]
        if exposed:
            wks = sh[5]

    piglinList = wks.get_col(col=2, include_tailing_empty=False, returnas='matrix')
    piglinList.pop(0)
    doneList = wks.get_col(col=3, include_tailing_empty=False, returnas='matrix')
    doneList.pop(0)
    tenBarterList = wks.get_col(col=4, include_tailing_empty=False, returnas='matrix')
    tenBarterList.pop(0)
    totalPiglins = 0
    countPiglins = 0
    for item in piglinList:
        totalPiglins += int(item)
        countPiglins += 1
    print("Average Piglins      | " + str(round(totalPiglins/countPiglins, 1)))
    for i in range(simNUM):
        index = random.randrange(0, len(piglinList))
        piglins = int(piglinList[index])
        finish = int(doneList[index])
        tenBarters = int(tenBarterList[index])
        routeTimeList.append(runRouteSim(piglins, finish, tenBarters))
    return routeTimeList


def analyze():
    timeList = []
    labelList = []
    for hole in [True, False]:
        for exposed in [True, False]:
            if hole:
                label = "high "
            else:
                label = "low "
            if exposed:
                label = label + "exposed"
            else:
                label = label + "buried"
            print(label + ": ")
            listOfRouteTimes = getListOfRouteTimes(hole, exposed)
            sum = 0
            count = 0
            for item in listOfRouteTimes:
                if item > 0:
                    timeList.append(item)
                    labelList.append(label)
                    sum += item
                    count += 1
            print("Average Route Time   | " + str(round(sum/count, 3) + start))
            print("")


    dict1 = {'time': timeList, 'label': labelList}
    sns.kdeplot(data=dict1, x='time', hue='label', legend=True, bw_adjust=0.95)
    plt.savefig("C:/Users/thoma/OneDrive/Desktop/holeSim.png", dpi=1000)


analyze()

