import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
from matplotlib import gridspec
import matplotlib.pyplot as plt
plt.style.use('seaborn-white')
import Valid_Matched
import Scoring

def GenerateGraph(OtherPreFile, OtherPostFile, Level, Weightsdf, **Surveys):
    global NValidPost, N_Other

    dfOther_Pre = pd.read_csv(OtherPreFile)
    dfOther_PreS = Scoring.CalcScore(dfOther_Pre, Weightsdf)

    dfOther_Post = pd.read_csv(OtherPostFile)
    N_Other = len(dfOther_Post)
    dfOther_PostS = Scoring.CalcScore(dfOther_Post, Weightsdf)

    dfOtherS = pd.concat([dfOther_PreS, dfOther_PostS], axis = 0, join = 'inner').reset_index(drop = True) # Collect all data together for CFA model building

    dfOther_PreS_Level = dfOther_PreS[dfOther_PreS['Course_Level'] == Level].reset_index(drop = True) # Filter out pre cumulative data by course level
    dfOther_PreS_Level = dfOther_PreS_Level.assign(Survey = 'PRE', Data = 'Other')

    dfOther_PostS_Level = dfOther_PostS[dfOther_PostS['Course_Level'] == Level].reset_index(drop = True) # Filter out post cumulative data by course level
    dfOther_PostS_Level = dfOther_PostS_Level.assign(Survey = 'POST', Data = 'Other')

    if('MID' in Surveys.keys()): # Build class dataframe when 3 surveys are given
        NValidPre, NValidMid, NValidPost, dfYour_Pre, dfYour_Mid, dfYour_Post = Valid_Matched.ValMat(Surveys['PRE'], Surveys['MID'], Surveys['POST'])

        dfYour_PreS = Scoring.CalcScore(dfYour_Pre, Weightsdf).loc[:, 'Q1Bs':]
        dfYour_PreS = dfYour_PreS.assign(Survey = 'PRE', Data = 'Yours')

        dfYour_MidS = Scoring.CalcScore(dfYour_Mid, Weightsdf).loc[:, 'Q1Bs':]
        dfYour_MidS = dfYour_MidS.assign(Survey = 'MID', Data = 'Yours')

        dfYour_PostS = Scoring.CalcScore(dfYour_Post, Weightsdf).loc[:, 'Q1Bs':]
        dfYour_PostS = dfYour_PostS.assign(Survey = 'POST', Data = 'Yours')

        df_Concat = pd.concat([dfYour_PreS, dfYour_MidS, dfYour_PostS, dfOther_PreS_Level, dfOther_PostS_Level], axis = 0, join = 'inner').reset_index(drop = True) # Collect all data to be plotted into one dataframe
    elif('PRE' in Surveys.keys()): # Build class dataframe when 2 surveys are given
        NValidPre, NValidPost, dfYour_Pre, dfYour_Post = Valid_Matched.ValMat(Surveys['PRE'], Surveys['POST'])

        dfYour_PreS = Scoring.CalcScore(dfYour_Pre, Weightsdf).loc[:, 'Q1Bs':]
        dfYour_PreS = dfYour_PreS.assign(Survey = 'PRE', Data = 'Yours')

        dfYour_PostS = Scoring.CalcScore(dfYour_Post, Weightsdf).loc[:, 'Q1Bs':]
        dfYour_PostS = dfYour_PostS.assign(Survey = 'POST', Data = 'Yours')

        df_Concat = pd.concat([dfYour_PreS, dfYour_PostS, dfOther_PreS_Level, dfOther_PostS_Level], axis = 0, join = 'inner').reset_index(drop = True) # Collect all data to be plotted into one dataframe
    else: # Build class dataframe when only 1 survey is given
        NValidPost, dfYour_Post = Valid_Matched.ValMat(Surveys['POST'])

        dfYour_PostS = Scoring.CalcScore(dfYour_Post, Weightsdf).loc[:, 'Q1Bs':]
        dfYour_PostS = dfYour_PostS.assign(Survey = 'POST', Data = 'Yours')

        df_Concat = pd.concat([dfYour_PostS, dfOther_PreS_Level, dfOther_PostS_Level], axis = 0, join = 'inner').reset_index(drop = True) # Collect all data to be plotted into one dataframe

    df_Factors = Scoring.CalcFactorScores(dfOtherS, df_Concat) # Get factor scores for yours and other classes
    df_Concat = pd.concat([df_Concat, df_Factors], axis = 1, join = 'inner') # Merge the factor scores back with the question scores dataframe for yours and other classes

    GenerateTotalScoresGraph(df_Concat)
    GenerateQuestionsGraph(df_Concat)

    if('PRE' in Surveys.keys()):
        dfYour_Pre['Course_Level'] = Level # Append the new pre data to the historical data for future use
        dfOther_Pre = pd.concat([dfOther_Pre, dfYour_Pre], join = 'inner', axis = 0)
        #dfOther_Pre.to_csv('C:/PLIC/PreSurveys_ValMat.csv', index = False)

        dfYour_Post['Course_Level'] = Level # Append the new post data to the historical data for future use
        dfOther_Post = pd.concat([dfOther_Post, dfYour_Post], join = 'inner', axis = 0)
        #dfOther_Post.to_csv('C:/PLIC/PostSurveys_ValMat.csv', index = False)

        if('MID' in Surveys.keys()):
            return NValidPre, NValidMid, NValidPost, dfYour_Pre, dfYour_Mid, dfYour_Post
        else:
            return NValidPre, NValidPost, dfYour_Pre, dfYour_Post
    else:
        return NValidPost, dfYour_Post

def GenerateTotalScoresGraph(df): # Generate main total scores graph that includes factor scores in a 2x2 layout
    df = df.loc[:, ['Data', 'Survey', 'models', 'methods', 'actions', 'TotalScores']]

    matplotlib.rcParams.update({'font.size': 16, 'font.family': "sans-serif", 'font.sans-serif': "Arial"})
    fig, axes = plt.subplots(2, 2, figsize = (12, 9))

    y_max = df.loc[:, 'models':].apply(max)

    plt.sca(axes[0, 0])
    sns.boxplot(x = 'Data', y = 'models', hue = 'Survey', data = df, linewidth = 0.5)
    plt.xticks((0, 1), ('Your Class', 'Other Classes'))
    plt.xlabel('')
    plt.ylabel('Score')
    plt.title('Evaluating models scale')
    axes[0, 0].legend(bbox_to_anchor = (0, 1.12))

    plt.sca(axes[0, 1])
    sns.boxplot(x = 'Data', y = 'methods', hue = 'Survey', data = df, linewidth = 0.5)
    plt.xticks((0, 1), ('Your Class', 'Other Classes'))
    plt.xlabel('')
    plt.ylabel('Score')
    plt.title('Evaluating methods scale')
    axes[0, 1].legend().remove()

    plt.sca(axes[1, 0])
    sns.boxplot(x = 'Data', y = 'models', hue = 'Survey', data = df, linewidth = 0.5)
    plt.xticks((0, 1), ('Your Class', 'Other Classes'))
    plt.xlabel('')
    plt.ylabel('Score')
    plt.title('Suggesting follow-ups scale')
    axes[1, 0].legend().remove()

    plt.sca(axes[1, 1])
    sns.boxplot(x = 'Data', y = 'TotalScores', hue = 'Survey', data = df, linewidth = 0.5)
    plt.xticks((0, 1), ('Your Class', 'Other Classes'))
    plt.xlabel('')
    plt.ylabel('Score')
    plt.title('Total Scores')
    axes[1, 1].legend().remove()

    plt.tight_layout()
    fig.savefig('FactorsLevel.png')
    plt.close()
    plt.clf()

def GenerateQuestionsGraph(df):
    df_melt = pd.melt(df, id_vars = ['Data', 'Survey'], value_vars = ['Q1Bs', 'Q1Ds', 'Q1Es', 'Q2Bs', 'Q2Ds', 'Q2Es', 'Q3Bs', 'Q3Ds', 'Q3Es', 'Q4Bs'])

    dfYours = df_melt.loc[df_melt['Data'] == 'Yours', :]
    dfOther = df_melt.loc[df_melt['Data'] == 'Other', :]

    matplotlib.rcParams.update({'font.size': 16, 'font.family': "sans-serif", 'font.sans-serif': "Arial"})
    fig, axes = plt.subplots(1, 2, figsize = (12, 9))

    plt.sca(axes[0])
    sns.boxplot(x = 'value', y = 'variable', hue = 'Survey', data = dfYours, linewidth = 0.5, palette = {'PRE':'#ece7f2', 'MID':'#a6bddb', 'POST':'#2b8cbe'})
    plt.xlabel('Score')
    plt.ylabel('Question')
    plt.yticks(range(10), ('Q1B', 'Q1D', 'Q1E', 'Q2B', 'Q2D', 'Q2E', 'Q3B', 'Q3D', 'Q3E', 'Q4B'))
    plt.title('Your Class (N = {0})'.format(NValidPost))
    axes[0].legend(bbox_to_anchor = (-0.08, 1.05))

    plt.sca(axes[1])
    sns.boxplot(x = 'value', y = 'variable', hue = 'Survey', data = dfOther, linewidth = 0.5, palette = {'PRE':'#ece7f2', 'POST':'#2b8cbe'})
    plt.xlabel('Score')
    plt.title('Similar Classes (N = {0})'.format(N_Other))
    axes[1].legend().remove()

    axes[1].get_shared_y_axes().join(axes[0], axes[1])
    axes[1].set_ylabel('')
    axes[1].set_yticklabels([])

    plt.tight_layout()
    fig.savefig('QuestionsLevel.png', orientation = 'landscape')
    plt.close()
    plt.clf()
