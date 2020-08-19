import os
import numpy as np
import pandas as pd
import rpy2
os.environ['R_HOME'] = 'C:\Program Files\R\R-3.5.0'
os.environ['R_USER'] = 'C:\Anaconda3\Lib\site-packages\rpy2'
os.environ['R_LIBS_USER'] = r'C:\Users\Cole\Documents\R\win-library\3.5'
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
pandas2ri.activate()
from rpy2.robjects.packages import importr

def CalcScore(df, Weights):
    """"Calculate overall PLIC Scores

    Keyword arguments:
    df -- pandas dataframe of student responses on the PLIC
    Weights -- pandas series of weights applied to PLIC item response choices when scoring
    """

    for Q in ['Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 'Q3b', 'Q3d', 'Q3e', 'Q4b']: # strings that are part of all PLIC item response choice variable names

        Items = [c for c in Weights.index if Q in c] # Get response choices for questions
        df_Q = df[Items].fillna(0).astype(str).apply(lambda x: x.str.replace('^(?!0).*$', '1')).astype(float) # Not useful for future surveys, but used to replace FR codes when coders used alternaive codes not 1
        Q_Weights = Weights[Items]
        Ordered_Weights = Q_Weights.nlargest(3) # Get the three largest weights, sorted
        NumSelectedSeries = df_Q.sum(axis = 1).clip(upper = 3).map({0:1, 1:Ordered_Weights[0], 2:Ordered_Weights[:-1].sum(), 3:Ordered_Weights.sum()}) # Get normalizations for each student, mapping number of selected items

        df[Q.upper() + 's'] = (df_Q * Q_Weights).sum(axis = 1) / NumSelectedSeries # Normalized scores for each student on the question

    df.loc[:, 'Q1Bs':] = df.loc[:, 'Q1Bs':].clip(upper = 1)
    df['TotalScores'] = df.loc[:, 'Q1Bs':].sum(axis = 1).astype(float)

    return df

def CalcFactorScores(df_Cumulative, df_Your):
    """Calculate students scores on PLIC factors

    Keyword arguments:
    df_Cumulative -- pandas dataframe of students responses to the PLIC from the national dataset
    df_Your -- pandas dataframe of responses from the target class on the PLIC
    """

    Question_Scores = ['Q1Bs', 'Q1Ds', 'Q1Es', 'Q2Bs', 'Q2Ds', 'Q2Es', 'Q3Bs', 'Q3Ds', 'Q3Es', 'Q4Bs']
    df_Cumulative = df_Cumulative.loc[:, Question_Scores]
    df_Your = df_Your.loc[:, Question_Scores]
    importr('lavaan') # get necessary R packages
    importr('semPlot')

    # Perform CFA in R to get factor scores
    CFA_func = robjects.r('''
        function(MainData, NewData = NULL){
            PLIC.model.HYP <- ' models  =~ Q1Bs + Q2Bs + Q3Bs + Q3Ds
                                methods =~ Q1Ds + Q2Ds + Q4Bs
                                actions =~ Q1Es + Q2Es + Q3Es '

            mod.cfa.HYP <- cfa(PLIC.model.HYP, data = MainData, std.lv = TRUE, estimator = 'ML')

            if(is.null(NewData)){
                scores.df <- data.frame(lavPredict(mod.cfa.HYP))
            }else{
                scores.df <- data.frame(lavPredict(mod.cfa.HYP, newdata = NewData))
            }
        }
    ''')

    # Convert dataframes back to python pandas dataframes
    df_Your_Scores = pandas2ri.ri2py_dataframe(CFA_func(df_Cumulative, df_Your))

    return df_Your_Scores
