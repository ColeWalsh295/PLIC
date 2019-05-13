import numpy as np
import pandas as pd

def CalcScore(df, Weights):

    df = df.fillna(0)
    Last_col = df.columns[-1]

    for Q in ['Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 'Q3b', 'Q3d', 'Q3e', 'Q4b']:

        Items = [c for c in Weights.index if Q in c]
        df_Q = df[Items].astype(str).apply(lambda x: x.str.replace('^(?!0).*$', '1')).astype(float)
        Q_Weights = Weights[Items]
        Ordered_Weights = Q_Weights.nlargest(3)
        NumSelectedSeries = df_Q.sum(axis = 1).clip(upper = 3).map({0:1, 1:Ordered_Weights[0], 2:Ordered_Weights[:-1].sum(), 3:Ordered_Weights.sum()})

        df[Q.upper() + 's'] = (df_Q * Q_Weights).sum(axis = 1) / NumSelectedSeries

    df['TotalScores'] = df.loc[:, 'Q1Bs':].sum(axis = 1).astype(float)

    return df
