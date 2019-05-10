import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
from matplotlib import gridspec
matplotlib.rcParams.update({'font.size': 32})
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
GradientYour = matplotlib.cm.get_cmap('PiYG')
GradientOther = matplotlib.cm.get_cmap('PiYG')
import dc_stat_think as dcst
import Valid_Matched
import Scoring

def GenerateGraph1(YourPostFile, OtherPreFile, OtherPostFile, Level, Where = 'Local'):

    NValidPost, dfYour_Post = Valid_Matched.ValMat(YourPostFile, Where = Where)

    if(Where == 'Local'):
        dfOther_Pre = pd.read_excel(OtherPreFile)
        dfOther_Post = pd.read_excel(OtherPostFile)
    else:
        dfOther_Pre = pd.read_csv(OtherPreFile)
        dfOther_Post = pd.read_csv(OtherPostFile)

    dfOther_Pre_Type = dfOther_Pre[dfOther_Pre['Course_Level'] == Level].reset_index()
    dfOther_Post_Type = dfOther_Post[dfOther_Post['Course_Level'] == Level].reset_index()

    if(len(dfOther_Post_Type.index) >= len(dfYour_Post.index)):
        dfOther_PreS = Scoring.CalcScore(dfOther_Pre_Type)
        dfOther_PostS = Scoring.CalcScore(dfOther_Post_Type)
    else:
        dfOther_PreS = Scoring.CalcScore(dfOther_Pre)
        dfOther_PostS = Scoring.CalcScore(dfOther_Post)

    dfYour_PostS = Scoring.CalcScore(dfYour_Post)

    OtherPreAvg = (dfOther_PreS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)
    OtherPostAvg = (dfOther_PostS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)
    YourPostAvg = (dfYour_PostS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)

    OtherPreCount = dfOther_PreS.loc[:, 'Q1Bs':'Q4Bs']
    OtherPostCount = dfOther_PostS.loc[:, 'Q1Bs':'Q4Bs']
    YourPostCount = dfYour_PostS.loc[:, 'Q1Bs':'Q4Bs']

    Delta = 0.3
    sep = 0.1
    y_pos = np.array([2 * i for i in range(10)])
    NumOther = float(len(OtherPostCount.index))
    NumYour = float(len(YourPostCount.index))

    fig = plt.figure(figsize = (18, 18))
    gs = plt.GridSpec(5, 10, wspace = 1)
    ax = plt.subplot(gs[:, :8])
    axYour = plt.subplot(gs[:, :4])
    axOther = plt.subplot(gs[:, 4:8])
    axColor1 = plt.subplot(gs[:4, 8])
    axColor2 = plt.subplot(gs[:4, 9])
    axSample = plt.subplot(gs[4, 8:])

    axYour.grid(b = False, axis = 'y')
    axOther.grid(b = False, axis = 'y')
    axColor1.tick_params(top =False, bottom = False, left = False, right = False, labelbottom = False, labelleft = False)
    axColor1.grid(b = False)
    axColor2.tick_params(top =False, bottom = False, left = False, right = False, labelbottom = False, labelleft = False)
    axColor2.grid(b = False)
    axSample.tick_params(top =False, bottom = False, left = False, right = False, labelbottom = False, labelleft = False)
    axSample.grid(b = False)

    y = 0
    for Question in YourPostCount.columns:
        PostCounts = []
        for Score in range(4, -1, -1):
            Score = Score/4.0
            PostCounts.append(YourPostCount[Question].tolist().count(Score)/NumYour)
        YourColor = axYour.barh(y + sep/2, width = PostCounts, height = Delta, align = 'edge', left = [0] + list(np.cumsum(PostCounts))[:-1], color = [GradientYour(0.4 - 0.1 * i) for i in range(4, -1, -1)])
        YourPostInt = np.percentile(dcst.draw_bs_reps(dfYour_PostS[Question], np.mean, size = 10000), [2.5, 97.5])
        axYour.plot(YourPostInt, (y - 2 * Delta, y - 2 * Delta), linewidth = 10, color = GradientYour(0), alpha = 0.3)
        axYour.scatter(YourPostAvg[Question], y - 2 * Delta, s = 100, c = GradientYour(0), marker = '>')
        y += 2

    axYour.set_title('Your Class (N = {})'.format(len(dfYour_PostS.index)), fontsize = 16)
    axYour.set_xticks((0, 0.2, 0.4, 0.6, 0.8, 1))
    # axYour.invert_xaxis()
    axYour.set_ylim(-1, 19)
    axYour.invert_yaxis()
    axYour.set_yticks(y_pos)
    axYour.tick_params(axis='y', which='major', labelsize=16)
    axYour.set_yticklabels(["Q1B - Which items reflect your\nreasoning for determining how\ndistinguishable Group 1's values\nfor the spring constant, k, are?",
                            "Q1D - Which items reflect your\nreasoning for determining how\nwell you think Group 1's\nmethod tested the model?",
                            "Q1E - What do you think\nGroup 1 should do next?",
                            "Q2B - Which items reflect your\nreasoning for determining how\ndistinguishable Group 2's data\nare from the best-fit line?",
                            "Q2D - Which items reflect your\nreasoning for determining how\nwell you think Group 2's\nmethod tested the model",
                            "Q2E - What do you think\nGroup 2 should do next?",
                            "Q3B - Which items reflect your\nreasoning for determing how\ndistinguishable Group 2's data\nare from the new best-fit line",
                            "Q3D - Which items reflect your\nreasoning for determing which\nfit you think Group 2 should use",
                            "Q3E - What do you think\nGroup 2 should do next?",
                            "Q4B - What features are most\nimportant for comparing\nthe two groups?"])
    axYour.set_ylabel('Questions', rotation = 0, fontsize = 16)
    axYour.yaxis.set_label_coords(-0.3, 1)

    y = 0
    for Question in OtherPostCount.columns:
        PreCounts = []
        PostCounts = []
        for Score in range(4, -1, -1):
            Score = Score/4.0
            if(Question != 'Q3Ds'):
                PreCounts.append(OtherPreCount[Question].tolist().count(Score)/NumOther)
                PostCounts.append(OtherPostCount[Question].tolist().count(Score)/NumOther)
            else:
                PreCounts.append(OtherPostCount[Question].tolist().count(Score)/OtherPostCount[Question].count().sum())
                PostCounts.append(OtherPostCount[Question].tolist().count(Score)/OtherPostCount[Question].count().sum())
        axOther.barh(y - sep/2, width = PreCounts, height = -Delta, align = 'edge', left = [0] + list(np.cumsum(PreCounts))[:-1], color = [GradientOther(0.6 + 0.1 * i) for i in range(4, -1, -1)])
        axOther.barh(y + sep/2, width = PostCounts, height = Delta, align = 'edge', left = [0] + list(np.cumsum(PostCounts))[:-1], color = [GradientOther(0.6 + 0.1 * i) for i in range(4, -1, -1)])
        if(Question == 'Q3Ds'):
            OtherPreInt = np.percentile(dcst.draw_bs_reps(dfOther_PostS[Question], np.mean, size = 10000), [2.5, 97.5])
        else:
            OtherPreInt = np.percentile(dcst.draw_bs_reps(dfOther_PreS[Question], np.mean, size = 10000), [2.5, 97.5])
        axOther.plot(OtherPreInt, (y - 2 * Delta, y - 2 * Delta), linewidth = 10, color = GradientOther(0.6 + 0.4), alpha = 0.3)
        if(Question == 'Q3Ds'):
            axOther.scatter(OtherPostAvg[Question], y - 2 * Delta, s = 100, c = GradientOther(0.6 + 0.4))
        else:
            axOther.scatter(OtherPreAvg[Question], y - 2 * Delta, s = 100, c = GradientOther(0.6 + 0.4))
            axOther.plot((OtherPreAvg[Question], OtherPostAvg[Question]), (y - 2 * Delta, y - 2 * Delta), c = GradientOther(0.6 + 0.4))
        if(OtherPostAvg[Question] >= OtherPreAvg[Question]):
            axOther.scatter(OtherPostAvg[Question], y - 2 * Delta, s = 100, c = GradientOther(0.6 + 0.4), marker = '>')
        else:
            axOther.scatter(OtherPostAvg[Question], y - 2 * Delta, s = 100, c = GradientOther(0.6 + 0.4), marker = '<')
        y += 2

    axOther.set_title('Similar Classes (N = {})'.format(len(dfOther_PostS.index)), fontsize = 16)
    axOther.set_xticks((0, 0.2, 0.4, 0.6, 0.8, 1))
    axOther.set_ylim(-1, 19)
    axOther.invert_yaxis()
    TickLists = [[y - 2 * sep for y in y_pos], [y + 2 * sep for y in y_pos]]
    Ticks = [x for t in zip(*TickLists) for x in t]
    axOther.set_yticks(Ticks)
    axOther.set_yticklabels([x for t in zip(['PRE'] * 10, ['POST'] * 10) for x in t], fontsize = 16, horizontalalignment = 'center')
    # axOther.yaxis.tick_right()
    axOther.tick_params(axis='y', which='major', pad=25)

    cmap = matplotlib.colors.ListedColormap([GradientYour(0.4 - 0.1 * i) for i in range(5)])
    bounds = [1, 2, 3, 4, 5, 6]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    cb2 = matplotlib.colorbar.ColorbarBase(axColor1, cmap=cmap,
                                    norm=norm,
                                    boundaries=bounds,
                                    ticks=[i + 1.5 for i in range(5)],
                                    spacing='proportional',
                                    orientation='vertical')
    cb2.set_ticklabels([''] * cmap.N)

    cmap = matplotlib.colors.ListedColormap([GradientYour(0.6 + 0.1 * i) for i in range(5)])
    bounds = [1, 2, 3, 4, 5, 6]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    cb3 = matplotlib.colorbar.ColorbarBase(axColor2, cmap=cmap,
                                    norm=norm,
                                    boundaries=bounds,
                                    ticks=[i + 1.5 for i in range(5)],
                                    spacing='proportional',
                                    orientation='vertical')
    cb3.set_ticklabels(np.arange(5)/4.0)
    axColor2.set_ylabel('Fraction of Students who score:', rotation = 0, fontsize = 16)
    axColor2.yaxis.set_label_coords(-0.5, 1.05)

    axSample.set_title('Average Shifts', y = 0.75, fontsize = 16)
    axSample.plot((0.4, 0.6), (1, 1), linewidth = 10, color = GradientOther(0), alpha = 0.3)
    axSample.scatter(0.5, 1, s = 100, c = GradientOther(0))
    axSample.scatter(0.8, 1, s = 100, c = GradientOther(0), marker = '>')
    axSample.plot((0.5, 0.8), (1, 1), c = GradientOther(0))
    axSample.text(0.2, 0.6, 'Avg Pre', horizontalalignment = 'center', verticalalignment = 'center',
             transform=axSample.transAxes, fontsize = 16)
    axSample.text(1, 0.6, 'Avg Post', horizontalalignment = 'center', verticalalignment = 'center',
             transform=axSample.transAxes, fontsize = 16)

    axYour.text(1.07, 20, 'Average Score/Fraction of Students', fontsize = 16, horizontalalignment = 'center')
    plt.subplots_adjust(left=0.21, bottom=None, right=0.96, top=None, wspace=0.05, hspace=None)
    if(Where == 'Local'):
        fig.savefig('Matched_PrePost.png', orientation = 'landscape')
    else:
        fig.savefig('C:/PLIC/Matched_PrePost.png', orientation = 'landscape')
    plt.close()
    plt.clf()

    dfYour_PostS['Class'] = 'Your'
    dfYour_PostS['PrePost'] = 'POST'
    dfOther_PreS['Class'] = 'Other'
    dfOther_PreS['PrePost'] = 'PRE'
    dfOther_PostS['Class'] = 'Other'
    dfOther_PostS['PrePost'] = 'POST'

    df = pd.concat([dfYour_PostS, dfOther_PreS, dfOther_PostS], axis = 0)

    sns.boxplot(data = df, x = 'Class', y = 'TotalScores', hue = 'PrePost', hue_order = ['PRE', 'POST'], palette = 'PiYG')
    plt.xlabel('')
    plt.xticks((np.arange(2)), ('Your Class (N = {})'.format(len(dfYour_PostS.index)), 'Similar Classes (N = {})'.format(len(dfOther_PostS.index))), fontsize = 18, rotation = 15)
    plt.ylabel('Scores on PLIC (/10)')
    plt.legend(bbox_to_anchor = (1, 1))
    plt.subplots_adjust(left=0.12, bottom=0.22, right=0.78)
    if(Where == 'Local'):
        plt.savefig('TotalScores.png')
    else:
        plt.savefig('C:/PLIC/TotalScores.png')
    plt.close()
    plt.clf()

    return NValidPost, dfYour_Post

def GenerateGraph2(OtherPreFile, OtherPostFile, Level, Where = 'Local', **Surveys):

    Survey1 = list(Surveys.keys())[0]
    YourPreFile = list(Surveys.values())[0]
    YourPostFile = list(Surveys.values())[1]

    NValidPre, NValidPost, dfYour_Pre, dfYour_Post = Valid_Matched.ValMat(YourPreFile, YourPostFile, Where = Where)

    if(Where == 'Local'):
        dfOther_Pre = pd.read_csv(OtherPreFile)
        dfOther_Post = pd.read_csv(OtherPostFile)
    else:
        dfOther_Pre = pd.read_csv(OtherPreFile)
        dfOther_Post = pd.read_csv(OtherPostFile)

    dfOther_Pre_Type = dfOther_Pre[dfOther_Pre['Course_Level'] == Level].reset_index()
    dfOther_Post_Type = dfOther_Post[dfOther_Post['Course_Level'] == Level].reset_index()

    if(len(dfOther_Post_Type.index) >= len(dfYour_Post.index)):
        dfOther_PreS = Scoring.CalcScore(dfOther_Pre_Type)
        dfOther_PostS = Scoring.CalcScore(dfOther_Post_Type)
    else:
        dfOther_PreS = Scoring.CalcScore(dfOther_Pre)
        dfOther_PostS = Scoring.CalcScore(dfOther_Post)

    dfYour_PreS = Scoring.CalcScore(dfYour_Pre)
    dfYour_PostS = Scoring.CalcScore(dfYour_Post)

    OtherPreAvg = (dfOther_PreS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)
    OtherPostAvg = (dfOther_PostS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)
    YourPreAvg = (dfYour_PreS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)
    YourPostAvg = (dfYour_PostS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)

    OtherPreCount = dfOther_PreS.loc[:, 'Q1Bs':'Q4Bs']
    OtherPostCount = dfOther_PostS.loc[:, 'Q1Bs':'Q4Bs']
    YourPreCount = dfYour_PreS.loc[:, 'Q1Bs':'Q4Bs']
    YourPostCount = dfYour_PostS.loc[:, 'Q1Bs':'Q4Bs']

    Delta = 0.3
    sep = 0.1
    y_pos = np.array([2 * i for i in range(10)])
    NumOther = float(len(OtherPostCount.index))
    NumYour = float(len(YourPostCount.index))

    fig = plt.figure(figsize = (18, 18))
    gs = plt.GridSpec(5, 10, wspace = 1)
    ax = plt.subplot(gs[:, :8])
    axYour = plt.subplot(gs[:, :4])
    axOther = plt.subplot(gs[:, 4:8])
    axColor1 = plt.subplot(gs[:4, 8])
    axColor2 = plt.subplot(gs[:4, 9])
    axSample = plt.subplot(gs[4, 8:])

    axYour.grid(b = False, axis = 'y')
    axOther.grid(b = False, axis = 'y')
    axColor1.tick_params(top =False, bottom = False, left = False, right = False, labelbottom = False, labelleft = False)
    axColor1.grid(b = False)
    axColor2.tick_params(top =False, bottom = False, left = False, right = False, labelbottom = False, labelleft = False)
    axColor2.grid(b = False)
    axSample.tick_params(top =False, bottom = False, left = False, right = False, labelbottom = False, labelleft = False)
    axSample.grid(b = False)

    y = 0
    for Question in YourPostCount.columns:
        PreCounts = []
        PostCounts = []
        for Score in range(4, -1, -1):
            Score = Score/4.0
            PreCounts.append(YourPreCount[Question].tolist().count(Score)/NumYour)
            PostCounts.append(YourPostCount[Question].tolist().count(Score)/NumYour)
        YourColor = axYour.barh(y - sep/2, width = PreCounts, height = -Delta, align = 'edge', left = [0] + list(np.cumsum(PreCounts))[:-1], color = [GradientYour(0.4 - 0.1 * i) for i in range(4, -1, -1)])
        axYour.barh(y + sep/2, width = PostCounts, height = Delta, align = 'edge', left = [0] + list(np.cumsum(PostCounts))[:-1], color = [GradientYour(0.4 - 0.1 * i) for i in range(4, -1, -1)])
        YourPreInt = np.percentile(dcst.draw_bs_reps(dfYour_PreS[Question], np.mean, size = 10000), [2.5, 97.5])
        axYour.plot(YourPreInt, (y - 2 * Delta, y - 2 * Delta), linewidth = 10, color = GradientYour(0), alpha = 0.3)
        axYour.scatter(YourPreAvg[Question], y - 2 * Delta, s = 100, c = GradientYour(0))
        axYour.plot((YourPreAvg[Question], YourPostAvg[Question]), (y - 2 * Delta, y - 2 * Delta), c = GradientYour(0))
        if(YourPostAvg[Question] >= YourPreAvg[Question]):
            axYour.scatter(YourPostAvg[Question], y - 2 * Delta, s = 100, c = GradientYour(0), marker = '>')
        else:
            axYour.scatter(YourPostAvg[Question], y - 2 * Delta, s = 100, c = GradientYour(0), marker = '<')
        y += 2

    axYour.set_title('Your Class (N = {})'.format(len(dfYour_PostS.index)), fontsize = 16)
    axYour.set_xticks((0, 0.2, 0.4, 0.6, 0.8, 1))
    # axYour.invert_xaxis()
    axYour.set_ylim(-1, 19)
    axYour.invert_yaxis()
    axYour.set_yticks(y_pos)
    axYour.tick_params(axis='y', which='major', labelsize=16)
    axYour.set_yticklabels(["Q1B - Which items reflect your\nreasoning for determining how\ndistinguishable Group 1's values\nfor the spring constant, k, are?",
                            "Q1D - Which items reflect your\nreasoning for determining how\nwell you think Group 1's\nmethod tested the model?",
                            "Q1E - What do you think\nGroup 1 should do next?",
                            "Q2B - Which items reflect your\nreasoning for determining how\ndistinguishable Group 2's data\nare from the best-fit line?",
                            "Q2D - Which items reflect your\nreasoning for determining how\nwell you think Group 2's\nmethod tested the model",
                            "Q2E - What do you think\nGroup 2 should do next?",
                            "Q3B - Which items reflect your\nreasoning for determing how\ndistinguishable Group 2's data\nare from the new best-fit line",
                            "Q3D - Which items reflect your\nreasoning for determing which\nfit you think Group 2 should use",
                            "Q3E - What do you think\nGroup 2 should do next?",
                            "Q4B - What features are most\nimportant for comparing\nthe two groups?"])
    axYour.set_ylabel('Questions', rotation = 0, fontsize = 16)
    axYour.yaxis.set_label_coords(-0.3, 1)

    y = 0
    for Question in OtherPostCount.columns:
        PreCounts = []
        PostCounts = []
        for Score in range(4, -1, -1):
            Score = Score/4.0
            if(Question != 'Q3Ds'):
                PreCounts.append(OtherPreCount[Question].tolist().count(Score)/NumOther)
                PostCounts.append(OtherPostCount[Question].tolist().count(Score)/NumOther)
            else:
                PreCounts.append(OtherPostCount[Question].tolist().count(Score)/OtherPostCount[Question].count().sum())
                PostCounts.append(OtherPostCount[Question].tolist().count(Score)/OtherPostCount[Question].count().sum())
        axOther.barh(y - sep/2, width = PreCounts, height = -Delta, align = 'edge', left = [0] + list(np.cumsum(PreCounts))[:-1], color = [GradientOther(0.6 + 0.1 * i) for i in range(4, -1, -1)])
        axOther.barh(y + sep/2, width = PostCounts, height = Delta, align = 'edge', left = [0] + list(np.cumsum(PostCounts))[:-1], color = [GradientOther(0.6 + 0.1 * i) for i in range(4, -1, -1)])
        if(Question == 'Q3Ds'):
            OtherPreInt = np.percentile(dcst.draw_bs_reps(dfOther_PostS[Question], np.mean, size = 10000), [2.5, 97.5])
        else:
            OtherPreInt = np.percentile(dcst.draw_bs_reps(dfOther_PreS[Question], np.mean, size = 10000), [2.5, 97.5])
        axOther.plot(OtherPreInt, (y - 2 * Delta, y - 2 * Delta), linewidth = 10, color = GradientOther(0.6 + 0.4), alpha = 0.3)
        if(Question == 'Q3Ds'):
            axOther.scatter(OtherPostAvg[Question], y - 2 * Delta, s = 100, c = GradientOther(0.6 + 0.4))
        else:
            axOther.scatter(OtherPreAvg[Question], y - 2 * Delta, s = 100, c = GradientOther(0.6 + 0.4))
            axOther.plot((OtherPreAvg[Question], OtherPostAvg[Question]), (y - 2 * Delta, y - 2 * Delta), c = GradientOther(0.6 + 0.4))
        if(OtherPostAvg[Question] >= OtherPreAvg[Question]):
            axOther.scatter(OtherPostAvg[Question], y - 2 * Delta, s = 100, c = GradientOther(0.6 + 0.4), marker = '>')
        else:
            axOther.scatter(OtherPostAvg[Question], y - 2 * Delta, s = 100, c = GradientOther(0.6 + 0.4), marker = '<')
        y += 2

    axOther.set_title('Similar Classes (N = {})'.format(len(dfOther_PostS.index)), fontsize = 16)
    axOther.set_xticks((0, 0.2, 0.4, 0.6, 0.8, 1))
    axOther.set_ylim(-1, 19)
    axOther.invert_yaxis()
    TickLists = [[y - 2 * sep for y in y_pos], [y + 2 * sep for y in y_pos]]
    Ticks = [x for t in zip(*TickLists) for x in t]
    axOther.set_yticks(Ticks)
    axOther.set_yticklabels([x for t in zip(['PRE'] * 10, ['POST'] * 10) for x in t], fontsize = 16, horizontalalignment = 'center')
    # axOther.yaxis.tick_right()
    axOther.tick_params(axis='y', which='major', pad=25)

    cmap = matplotlib.colors.ListedColormap([GradientYour(0.4 - 0.1 * i) for i in range(5)])
    bounds = [1, 2, 3, 4, 5, 6]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    cb2 = matplotlib.colorbar.ColorbarBase(axColor1, cmap=cmap,
                                    norm=norm,
                                    boundaries=bounds,
                                    ticks=[i + 1.5 for i in range(5)],
                                    spacing='proportional',
                                    orientation='vertical')
    cb2.set_ticklabels([''] * cmap.N)

    cmap = matplotlib.colors.ListedColormap([GradientYour(0.6 + 0.1 * i) for i in range(5)])
    bounds = [1, 2, 3, 4, 5, 6]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    cb3 = matplotlib.colorbar.ColorbarBase(axColor2, cmap=cmap,
                                    norm=norm,
                                    boundaries=bounds,
                                    ticks=[i + 1.5 for i in range(5)],
                                    spacing='proportional',
                                    orientation='vertical')
    cb3.set_ticklabels(np.arange(5)/4.0)
    axColor2.set_ylabel('Fraction of Students who score:', rotation = 0, fontsize = 16)
    axColor2.yaxis.set_label_coords(-0.5, 1.05)

    axSample.set_title('Average Shifts', y = 0.75, fontsize = 16)
    axSample.plot((0.4, 0.6), (1, 1), linewidth = 10, color = GradientOther(0), alpha = 0.3)
    axSample.scatter(0.5, 1, s = 100, c = GradientOther(0))
    axSample.scatter(0.8, 1, s = 100, c = GradientOther(0), marker = '>')
    axSample.plot((0.5, 0.8), (1, 1), c = GradientOther(0))
    axSample.text(0.2, 0.6, 'Avg Pre', horizontalalignment = 'center', verticalalignment = 'center',
             transform=axSample.transAxes, fontsize = 16)
    axSample.text(1, 0.6, 'Avg Post', horizontalalignment = 'center', verticalalignment = 'center',
             transform=axSample.transAxes, fontsize = 16)

    axYour.text(1.07, 20, 'Average Score/Fraction of Students', fontsize = 16, horizontalalignment = 'center')
    plt.subplots_adjust(left=0.21, bottom=None, right=0.96, top=None, wspace=0.05, hspace=None)
    if(Where == 'Local'):
        fig.savefig('Matched_PrePost.png', orientation = 'landscape')
    else:
        fig.savefig('C:/PLIC/Matched_PrePost.png', orientation = 'landscape')
    plt.close()
    plt.clf()

    dfYour_PreS['Class'] = 'Your'
    dfYour_PreS['PrePost'] = Survey1
    dfYour_PostS['Class'] = 'Your'
    dfYour_PostS['PrePost'] = 'POST'
    dfOther_PreS['Class'] = 'Other'
    dfOther_PreS['PrePost'] = 'PRE'
    dfOther_PostS['Class'] = 'Other'
    dfOther_PostS['PrePost'] = 'POST'


    df = pd.concat([dfYour_PreS, dfYour_PostS, dfOther_PreS, dfOther_PostS], axis = 0)

    sns.boxplot(data = df, x = 'Class', y = 'TotalScores', hue = 'PrePost', hue_order = [Survey1, 'POST'], palette = 'PiYG')
    plt.xlabel('')
    plt.xticks((np.arange(2)), ('Your Class (N = {})'.format(len(dfYour_Post.index)), 'Similar Classes (N = {})'.format(len(dfOther_PostS.index))), fontsize = 18, rotation = 15)
    plt.ylabel('Scores on PLIC (/10)')
    plt.legend(bbox_to_anchor = (1, 1))
    plt.subplots_adjust(left=0.12, bottom=0.22, right=0.78)
    if(Where == 'Local'):
        plt.savefig('TotalScores.png')
    else:
        plt.savefig('C:/PLIC/TotalScores.png')
    plt.close()
    plt.clf()

    if(Survey1 == 'PRE'):

        dfYour_Pre['Course_Level'] = Level
        dfYour_Post['Course_Level'] = Level

        dfOther_Pre = pd.concat([dfOther_Pre, dfYour_Pre], join = 'inner', axis = 0)
        dfOther_Post = pd.concat([dfOther_Post, dfYour_Post], join = 'inner', axis = 0)

        if(Where == 'Local'):
            dfOther_Pre.to_excel('PreSurveys_ValMat.xlsx', index = False)
            dfOther_Post.to_excel('PostSurveys_ValMat.xlsx', index = False)
        elif(Where == 'Automation'):
            dfOther_Pre.to_csv('C:/PLIC/PreSurveys_ValMat.csv', index = False)
            dfOther_Post.to_csv('C:/PLIC/PostSurveys_ValMat.csv', index = False)

    return NValidPre, NValidPost, dfYour_Pre, dfYour_Post

def GenerateGraph3(YourPreFile, YourMidFile, YourPostFile, OtherPreFile, OtherPostFile, Level, Where = 'Local'):

    NValidPre, NValidMid, NValidPost, dfYour_Pre, dfYour_Mid, dfYour_Post = Valid_Matched.ValMat(YourPreFile, YourMidFile, YourPostFile, Where = Where)

    if(Where == 'Local'):
        dfOther_Pre = pd.read_csv(OtherPreFile)
        dfOther_Post = pd.read_csv(OtherPostFile)
    else:
        dfOther_Pre = pd.read_csv(OtherPreFile)
        dfOther_Post = pd.read_csv(OtherPostFile)

    dfOther_Pre_Type = dfOther_Pre[dfOther_Pre['Course_Level'] == Level].reset_index()
    dfOther_Post_Type = dfOther_Post[dfOther_Post['Course_Level'] == Level].reset_index()

    if(len(dfOther_Post_Type.index) >= len(dfYour_Post.index)):
        dfOther_PreS = Scoring.CalcScore(dfOther_Pre_Type)
        dfOther_PostS = Scoring.CalcScore(dfOther_Post_Type)
    else:
        dfOther_PreS = Scoring.CalcScore(dfOther_Pre)
        dfOther_PostS = Scoring.CalcScore(dfOther_Post)

    dfYour_PreS = Scoring.CalcScore(dfYour_Pre)
    dfYour_MidS = Scoring.CalcScore(dfYour_Mid)
    dfYour_PostS = Scoring.CalcScore(dfYour_Post)

    OtherPreAvg = (dfOther_PreS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)
    OtherPostAvg = (dfOther_PostS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)
    YourPreAvg = (dfYour_PreS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)
    YourMidAvg = (dfYour_MidS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)
    YourPostAvg = (dfYour_PostS.loc[:, 'Q1Bs':'Q4Bs']).mean(axis = 0)

    OtherPreCount = dfOther_PreS.loc[:, 'Q1Bs':'Q4Bs']
    OtherPostCount = dfOther_PostS.loc[:, 'Q1Bs':'Q4Bs']
    YourPreCount = dfYour_PreS.loc[:, 'Q1Bs':'Q4Bs']
    YourMidCount = dfYour_MidS.loc[:, 'Q1Bs':'Q4Bs']
    YourPostCount = dfYour_PostS.loc[:, 'Q1Bs':'Q4Bs']

    Delta = 0.3
    sep = 0.35
    y_pos = np.array([2 * i for i in range(10)])
    NumOther = float(len(OtherPostCount.index))
    NumYour = float(len(YourPostCount.index))

    fig = plt.figure(figsize = (18, 18))
    gs = plt.GridSpec(5, 10, wspace = 1)
    ax = plt.subplot(gs[:, :8])
    axYour = plt.subplot(gs[:, :4])
    axOther = plt.subplot(gs[:, 4:8])
    axColor1 = plt.subplot(gs[:4, 8])
    axColor2 = plt.subplot(gs[:4, 9])
    axSample = plt.subplot(gs[4, 8:])

    axYour.grid(b = False, axis = 'y')
    axOther.grid(b = False, axis = 'y')
    axColor1.tick_params(top =False, bottom = False, left = False, right = False, labelbottom = False, labelleft = False)
    axColor1.grid(b = False)
    axColor2.tick_params(top =False, bottom = False, left = False, right = False, labelbottom = False, labelleft = False)
    axColor2.grid(b = False)
    axSample.tick_params(top =False, bottom = False, left = False, right = False, labelbottom = False, labelleft = False)
    axSample.grid(b = False)

    y = 0
    for Question in YourPostCount.columns:
        PreCounts = []
        MidCounts = []
        PostCounts = []
        for Score in range(4, -1, -1):
            Score = Score/4.0
            PreCounts.append(YourPreCount[Question].tolist().count(Score)/NumYour)
            MidCounts.append(YourMidCount[Question].tolist().count(Score)/NumYour)
            PostCounts.append(YourPostCount[Question].tolist().count(Score)/NumYour)
        YourColor = axYour.barh(y - sep, width = PreCounts, height = Delta, align = 'center', left = [0] + list(np.cumsum(PreCounts))[:-1], color = [GradientYour(0.4 - 0.1 * i) for i in range(4, -1, -1)])
        axYour.barh(y, width = MidCounts, height = Delta, align = 'center', left = [0] + list(np.cumsum(MidCounts))[:-1], color = [GradientYour(0.4 - 0.1 * i) for i in range(4, -1, -1)])
        axYour.barh(y + sep, width = PostCounts, height = Delta, align = 'center', left = [0] + list(np.cumsum(PostCounts))[:-1], color = [GradientYour(0.4 - 0.1 * i) for i in range(4, -1, -1)])
        YourPreInt = np.percentile(dcst.draw_bs_reps(dfYour_PreS[Question], np.mean, size = 10000), [2.5, 97.5])
        axYour.plot(YourPreInt, (y - 3 * Delta, y - 3 * Delta), linewidth = 10, color = GradientYour(0), alpha = 0.3)
        axYour.scatter(YourPreAvg[Question], y - 3 * Delta, s = 100, c = GradientYour(0))
        axYour.plot((YourPreAvg[Question], YourPostAvg[Question]), (y - 3 * Delta, y - 3 * Delta), c = GradientYour(0))
        if(YourPostAvg[Question] >= YourPreAvg[Question]):
            axYour.scatter(YourPostAvg[Question], y - 3 * Delta, s = 100, c = GradientYour(0), marker = '>')
        else:
            axYour.scatter(YourPostAvg[Question], y - 3* Delta, s = 100, c = GradientYour(0), marker = '<')
        y += 2

    axYour.set_title('Your Class (N = {})'.format(len(dfYour_PostS.index)), fontsize = 16)
    axYour.set_xticks((0, 0.2, 0.4, 0.6, 0.8, 1))
    # axYour.invert_xaxis()
    axYour.set_ylim(-1, 19)
    axYour.invert_yaxis()
    axYour.set_yticks(y_pos)
    axYour.tick_params(axis='y', which='major', labelsize=16)
    axYour.set_yticklabels(["Q1B - Which items reflect your\nreasoning for determining how\ndistinguishable Group 1's values\nfor the spring constant, k, are?",
                            "Q1D - Which items reflect your\nreasoning for determining how\nwell you think Group 1's\nmethod tested the model?",
                            "Q1E - What do you think\nGroup 1 should do next?",
                            "Q2B - Which items reflect your\nreasoning for determining how\ndistinguishable Group 2's data\nare from the best-fit line?",
                            "Q2D - Which items reflect your\nreasoning for determining how\nwell you think Group 2's\nmethod tested the model",
                            "Q2E - What do you think\nGroup 2 should do next?",
                            "Q3B - Which items reflect your\nreasoning for determing how\ndistinguishable Group 2's data\nare from the new best-fit line",
                            "Q3D - Which items reflect your\nreasoning for determing which\nfit you think Group 2 should use",
                            "Q3E - What do you think\nGroup 2 should do next?",
                            "Q4B - What features are most\nimportant for comparing\nthe two groups?"])
    axYour.set_ylabel('Questions', rotation = 0, fontsize = 16)
    axYour.yaxis.set_label_coords(-0.3, 1)

    y = 0
    for Question in OtherPostCount.columns:
        PreCounts = []
        PostCounts = []
        for Score in range(4, -1, -1):
            Score = Score/4.0
            if(Question != 'Q3Ds'):
                PreCounts.append(OtherPreCount[Question].tolist().count(Score)/NumOther)
                PostCounts.append(OtherPostCount[Question].tolist().count(Score)/NumOther)
            else:
                PreCounts.append(OtherPostCount[Question].tolist().count(Score)/OtherPostCount[Question].count().sum())
                PostCounts.append(OtherPostCount[Question].tolist().count(Score)/OtherPostCount[Question].count().sum())
        axOther.barh(y - sep, width = PreCounts, height = Delta, align = 'center', left = [0] + list(np.cumsum(PreCounts))[:-1], color = [GradientOther(0.6 + 0.1 * i) for i in range(4, -1, -1)])
        axOther.barh(y + sep, width = PostCounts, height = Delta, align = 'center', left = [0] + list(np.cumsum(PostCounts))[:-1], color = [GradientOther(0.6 + 0.1 * i) for i in range(4, -1, -1)])
        if(Question == 'Q3Ds'):
            OtherPreInt = np.percentile(dcst.draw_bs_reps(dfOther_PostS[Question], np.mean, size = 10000), [2.5, 97.5])
        else:
            OtherPreInt = np.percentile(dcst.draw_bs_reps(dfOther_PreS[Question], np.mean, size = 10000), [2.5, 97.5])
        axOther.plot(OtherPreInt, (y - 3 * Delta, y - 3 * Delta), linewidth = 10, color = GradientOther(0.6 + 0.4), alpha = 0.3)
        if(Question == 'Q3Ds'):
            axOther.scatter(OtherPostAvg[Question], y - 3 * Delta, s = 100, c = GradientOther(0.6 + 0.4))
        else:
            axOther.scatter(OtherPreAvg[Question], y - 3 * Delta, s = 100, c = GradientOther(0.6 + 0.4))
            axOther.plot((OtherPreAvg[Question], OtherPostAvg[Question]), (y - 3 * Delta, y - 3 * Delta), c = GradientOther(0.6 + 0.4))
        if(OtherPostAvg[Question] >= OtherPreAvg[Question]):
            axOther.scatter(OtherPostAvg[Question], y - 3 * Delta, s = 100, c = GradientOther(0.6 + 0.4), marker = '>')
        else:
            axOther.scatter(OtherPostAvg[Question], y - 3 * Delta, s = 100, c = GradientOther(0.6 + 0.4), marker = '<')
        y += 2

    axOther.set_title('Similar Classes (N = {})'.format(len(dfOther_PostS.index)), fontsize = 16)
    axOther.set_xticks((0, 0.2, 0.4, 0.6, 0.8, 1))
    axOther.set_ylim(-1, 19)
    axOther.invert_yaxis()
    TickLists = [[y - sep for y in y_pos], [y for y in y_pos], [y + sep for y in y_pos]]
    Ticks = [x for t in zip(*TickLists) for x in t]
    axOther.set_yticks(Ticks)
    axOther.set_yticklabels([x for t in zip(['PRE'] * 10, ['MID'] * 10, ['POST'] * 10) for x in t], fontsize = 16, horizontalalignment = 'center')
    # axOther.yaxis.tick_right()
    axOther.tick_params(axis='y', which='major', pad=25)

    cmap = matplotlib.colors.ListedColormap([GradientYour(0.4 - 0.1 * i) for i in range(5)])
    bounds = [1, 2, 3, 4, 5, 6]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    cb2 = matplotlib.colorbar.ColorbarBase(axColor1, cmap=cmap,
                                    norm=norm,
                                    boundaries=bounds,
                                    ticks=[i + 1.5 for i in range(5)],
                                    spacing='proportional',
                                    orientation='vertical')
    cb2.set_ticklabels([''] * cmap.N)

    cmap = matplotlib.colors.ListedColormap([GradientYour(0.6 + 0.1 * i) for i in range(5)])
    bounds = [1, 2, 3, 4, 5, 6]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    cb3 = matplotlib.colorbar.ColorbarBase(axColor2, cmap=cmap,
                                    norm=norm,
                                    boundaries=bounds,
                                    ticks=[i + 1.5 for i in range(5)],
                                    spacing='proportional',
                                    orientation='vertical')
    cb3.set_ticklabels(np.arange(5)/4.0)
    axColor2.set_ylabel('Fraction of Students who score:', rotation = 0, fontsize = 16)
    axColor2.yaxis.set_label_coords(-0.5, 1.05)

    axSample.set_title('Average Shifts', y = 0.75, fontsize = 16)
    axSample.plot((0.4, 0.6), (1, 1), linewidth = 10, color = GradientOther(0), alpha = 0.3)
    axSample.scatter(0.5, 1, s = 100, c = GradientOther(0))
    axSample.scatter(0.8, 1, s = 100, c = GradientOther(0), marker = '>')
    axSample.plot((0.5, 0.8), (1, 1), c = GradientOther(0))
    axSample.text(0.2, 0.6, 'Avg Pre', horizontalalignment = 'center', verticalalignment = 'center',
             transform=axSample.transAxes, fontsize = 16)
    axSample.text(1, 0.6, 'Avg Post', horizontalalignment = 'center', verticalalignment = 'center',
             transform=axSample.transAxes, fontsize = 16)

    axYour.text(1.07, 20, 'Average Score/Fraction of Students', fontsize = 16, horizontalalignment = 'center')
    plt.subplots_adjust(left=0.21, bottom=None, right=0.96, top=None, wspace=0.05, hspace=None)
    if(Where == 'Local'):
        fig.savefig('Matched_PrePost.png', orientation = 'landscape')
    else:
        fig.savefig('C:/PLIC/Matched_PrePost.png', orientation = 'landscape')
    plt.close()
    plt.clf()

    dfYour_PreS['Class'] = 'Your'
    dfYour_PreS['PrePost'] = 'PRE'
    dfYour_MidS['Class'] = 'Your'
    dfYour_MidS['PrePost'] = 'MID'
    dfYour_PostS['Class'] = 'Your'
    dfYour_PostS['PrePost'] = 'POST'
    dfOther_PreS['Class'] = 'Other'
    dfOther_PreS['PrePost'] = 'PRE'
    dfOther_PostS['Class'] = 'Other'
    dfOther_PostS['PrePost'] = 'POST'


    df = pd.concat([dfYour_PreS, dfYour_MidS, dfYour_PostS, dfOther_PreS, dfOther_PostS], axis = 0)

    sns.boxplot(data = df, x = 'Class', y = 'TotalScores', hue = 'PrePost', palette = 'PiYG')
    plt.xlabel('')
    plt.xticks((np.arange(2)), ('Your Class (N = {})'.format(len(dfYour_Post.index)), 'Similar Classes (N = {})'.format(len(dfOther_PostS.index))), fontsize = 18, rotation = 15)
    plt.ylabel('Scores on PLIC (/10)')
    plt.legend(bbox_to_anchor = (1, 1))
    plt.subplots_adjust(left=0.12, bottom=0.22, right=0.78)
    if(Where == 'Local'):
        plt.savefig('TotalScores.png')
    else:
        plt.savefig('C:/PLIC/TotalScores.png')
    plt.close()
    plt.clf()

    dfYour_Pre['Course_Level'] = Level
    dfYour_Post['Course_Level'] = Level

    dfOther_Pre = pd.concat([dfOther_Pre, dfYour_Pre], join = 'inner', axis = 0)
    dfOther_Post = pd.concat([dfOther_Post, dfYour_Post], join = 'inner', axis = 0)

    if(Where == 'Local'):
        dfOther_Pre.to_excel('PreSurveys_ValMat.xlsx', index = False)
        dfOther_Post.to_excel('PostSurveys_ValMat.xlsx', index = False)
    elif(Where == 'Automation'):
        dfOther_Pre.to_csv('C:/PLIC/PreSurveys_ValMat.csv', index = False)
        dfOther_Post.to_csv('C:/PLIC/PostSurveys_ValMat.csv', index = False)

    return NValidPre, NValidMid, NValidPost, dfYour_Pre, dfYour_Mid, dfYour_Post
