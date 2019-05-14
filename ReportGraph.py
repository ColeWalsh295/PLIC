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

def GenerateGraph(OtherPreFile, OtherPostFile, Level, **Surveys):

    dfOther_Pre = pd.read_csv(OtherPreFile)
    dfOther_PreS = Scoring.CalcScore(dfOther_Pre)

    dfOther_Post = pd.read_csv(OtherPostFile)
    N_Other = len(dfOther_Post)
    dfOther_PostS = Scoring.CalcScore(dfOther_Post)

    dfOtherS = pd.concat([dfOther_PreS, dfOther_PostS], axis = 0, join = 'inner') # Collect all data together for CFA model building

    dfOther_PreS_Level = dfOther_PreS[dfOther_PreS['Course_Level'] == Level].reset_index() # Filter out pre cumulative data by course level
    dfOther_PreS_Level.assign(Survey = 'PRE', Data = 'Other')

    dfOther_PostS_Level = dfOther_PostS[dfOther_PostS['Course_Level'] == Level].reset_index() # Filter out post cumulative data by course level
    dfOther_PostS_Level.assign(Survey = 'POST', Data = 'Other')

    Survey1 = list(Surveys.keys())[0]
    YourPreFile = list(Surveys.values())[0]
    YourPostFile = list(Surveys.values())[1]
    if('MID' in list(Surveys.keys())):
        NValidPre, NValidMid, NValidPost, dfYour_Pre, dfYour_Mid, dfYour_Post = Valid_Matched.ValMat(YourPreFile, YourMidFile, YourPostFile)

        dfYour_PreS = Scoring.CalcScore(dfYour_Pre).loc[:, 'Q1Bs':]
        dfYour_PreS.assign(Survey = 'PRE', Data = 'Yours')

        dfYour_MidS = Scoring.CalcScore(dfYour_Mid).loc[:, 'Q1Bs':]
        dfYour_MidS.assign(Survey = 'PRE', Data = 'Yours')

        dfYour_PostS = Scoring.CalcScore(dfYour_Post).loc[:, 'Q1Bs':]
        dfYour_PostS.assign(Survey = 'POST', Data = 'Yours')

        df_Concat = pd.concat([dfYour_PreS, dfYour_MidS, dfYour_PostS, dfOther_PreS_Level, dfOther_PostS_Level], axis = 0, join = 'inner').loc[:, 'Q1Bs':] # Collect all data to be plotted into one dataframe
    elif('PRE' in list(Surveys.keys())):
        NValidPre, NValidPost, dfYour_Pre, dfYour_Post = Valid_Matched.ValMat(YourPreFile, YourPostFile)

        dfYour_PreS = Scoring.CalcScore(dfYour_Pre).loc[:, 'Q1Bs':]
        dfYour_PreS.assign(Survey = 'PRE', Data = 'Yours')

        dfYour_PostS = Scoring.CalcScore(dfYour_Post).loc[:, 'Q1Bs':]
        dfYour_PostS.assign(Survey = 'POST', Data = 'Yours')

        df_Concat = pd.concat([dfYour_PreS, dfYour_PostS, dfOther_PreS_Level, dfOther_PostS_Level], axis = 0, join = 'inner').loc[:, 'Q1Bs':] # Collect all data to be plotted into one dataframe
    else:
        NValidPost, dfYour_Post = Valid_Matched.ValMat(YourPostFile)

        dfYour_PostS = Scoring.CalcScore(dfYour_Post).loc[:, 'Q1Bs':]
        dfYour_PostS.assign(Survey = 'POST', Data = 'Yours')

        df_Concat = pd.concat([dfYour_PostS, dfOther_PreS_Level, dfOther_PostS_Level], axis = 0, join = 'inner').loc[:, 'Q1Bs':] # Collect all data to be plotted into one dataframe

    df_Factors = Scoring.CalcFactorScores(dfOtherS, df_Concat) # Get factor scores for yours and other classes
    df_Concat = pd.concat([df_Concat, df_Factors], axis = 1, join = 'inner')

    GenerateTotalScoresGraph(df_Concat)
    GenerateQuestionsGraph(df_Concat)

    dfYour_Pre['Course_Level'] = Level
    dfYour_Post['Course_Level'] = Level

    dfOther_Pre = pd.concat([dfOther_Pre, dfYour_Pre], join = 'inner', axis = 0)
    dfOther_Post = pd.concat([dfOther_Post, dfYour_Post], join = 'inner', axis = 0)

    dfOther_Pre.to_csv('C:/PLIC/PreSurveys_ValMat.csv', index = False)
    dfOther_Post.to_csv('C:/PLIC/PostSurveys_ValMat.csv', index = False)

    return NValidPre, NValidPost, dfYour_Pre, dfYour_Post

def GenerateTotalScoresGraph(df): # Generate main total scores graph that includes factor scores in a 2x2 layout

    matplotlib.rcParams.update({'font.size': 16, 'font.family': "sans-serif", 'font.sans-serif': "Arial"})
    fig, axes = plt.subplots(2, 2, figsize = (12, 9))

    plt.sca(axes[0, 0])
    sns.boxplot(x = 'Data', y = 'models', hue = 'Survey', data = df, linewidth = 0.5)
    plt.xticks((0, 1), ('Your Class', 'Other Classes'), rotation = 40)
    plt.ylabel('Score')
    plt.text(0.5, 1.1, 'Evaluating models scale', ha = 'center', va = 'center')

    plt.sca(axes[0, 1])
    sns.boxplot(x = 'Data', y = 'methods', hue = 'Survey', data = df, linewidth = 0.5)
    plt.xticks((0, 1), ('Your Class', 'Other Classes'), rotation = 40)
    plt.ylabel('Score')
    plt.text(0.5, 1.1, 'Evaluating methods scale', ha = 'center', va = 'center')

    plt.sca(axes[1, 0])
    sns.boxplot(x = 'Data', y = 'models', hue = 'Survey', data = df, linewidth = 0.5)
    plt.xticks((0, 1), ('Your Class', 'Other Classes'), rotation = 40)
    plt.ylabel('Score')
    plt.text(0.5, 1.1, 'Suggesting follow-ups scale', ha = 'center', va = 'center')

    plt.sca(axes[1, 1])
    sns.boxplot(x = 'Data', y = 'TotalScores', hue = 'Survey', data = df, linewidth = 0.5)
    plt.xticks((0, 1), ('Your Class', 'Other Classes'), rotation = 40)
    plt.ylabel('Score')
    plt.text(0.5, 1.1, 'Total Scores', ha = 'center', va = 'center')

    plt.tight_layout()
    fig.savefig('FactorsLevel.png')
    plt.close()
    plt.clf()

def GenerateQuestionsGraph(df):

    df_melt = pd.melt(df, id_vars = ['Data', 'Survey'], value_vars = ['Q1Bs', 'Q1Ds', 'Q1Es', 'Q2Bs', 'Q2Ds', 'Q2Es', 'Q3Bs', 'Q3Ds', 'Q3Es', 'Q4Bs'])

    dfYours = df_melt.loc[df_melt['Data'] == 'Yours', :]
    dfOther = df_melt.loc[df_melt['Data'] == 'Other', :]

    matplotlib.rcParams.update({'font.size': 16, 'font.family': "sans-serif", 'font.sans-serif': "Arial"})
    fig, axes = plt.subplots(1, 2, figsize = (18, 18))

    plt.sca(axes[0, 0])
    sns.boxplot(x = 'value', y = 'variable', hue = 'Survey', data = df_Yours, linewidth = 0.5)
    plt.yticks(range(10), ('Q1B', 'Q1D', 'Q1E', 'Q2B', 'Q2D', 'Q2E', 'Q3B', 'Q3D', 'Q3E', 'Q4B'))
    plt.ylabel('Question')
    plt.text(0.5, 11, 'Your Class (N = {0})'.format(NValidPost), ha = 'center', va = 'center')

    plt.sca(axes[0, 1])
    sns.boxplot(x = 'value', y = 'variable', hue = 'Survey', data = df_Other, linewidth = 0.5)
    plt.yticks(range(10), ('Q1B', 'Q1D', 'Q1E', 'Q2B', 'Q2D', 'Q2E', 'Q3B', 'Q3D', 'Q3E', 'Q4B'))
    plt.ylabel('Question')
    plt.text(0.5, 11, 'Similar Classes (N = {0})'.format(N_Other), ha = 'center', va = 'center')

    plt.tight_layout()
    fig.savefig('QuestionsLevel.png', orientation = 'landscape')
    plt.close()
    plt.clf()
