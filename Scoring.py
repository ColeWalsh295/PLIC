import numpy as np
import pandas as pd

def CalcScore(DataFrame, Output = None):

    df = DataFrame.fillna(0)

    Scores = []

    for Index, Student in df.iterrows():

        # Question 1B

        Q1B = 0
        if(df.loc[Index, "Q1b_5"] == 1):
            Q1B = 1
        elif(df.loc[Index, "Q1b_28"] == 1):
            Q1B = 0.5
        if((df.loc[Index, "Q1b_16"] == 1) | (df.loc[Index, "Q1b_31"] == 1)):
            Q1B -= 0.25

        Q1B = max(Q1B, 0)

        # Question 1D

        Q1D = 0
        if(df.loc[Index, "Q1d_3"] == 1):
            Q1D = 1
        elif((df.loc[Index, "Q1d_5"] == 1) | (df.loc[Index, "Q1d_63"] == 1)):
            Q1D = 0.5
        if((df.loc[Index, "Q1d_57"] == 1) | (df.loc[Index, "Q1d_61"] == 1)):
            Q1D -= 0.25

        Q1D = max(Q1D, 0)

        # Question 1E

        Q1E = 0
        if(df.loc[Index, "Q1e_1"] == 1):
            Q1E = 1
        elif((df.loc[Index, "Q1e_4"] == 1) | (df.loc[Index, "Q1e_20"] == 1)):
            Q1E = 0.5
        if((df.loc[Index, "Q1e_17"] == 1) | (df.loc[Index, "Q1e_23"] == 1)):
            Q1E -= 0.25

        Q1E = max(Q1E, 0)

        # Question 2B

        Q2B = 0
        if((df.loc[Index, "Q2b_2"] == 1) | (df.loc[Index, "Q2b_11"] == 1)):
            Q2B = 1
        elif(df.loc[Index, "Q2b_6"] == 1):
            Q2B = 0.5
        if((df.loc[Index, "Q2b_9"] == 1) | (df.loc[Index, "Q2b_21"] == 1)):
            Q2B -= 0.25

        Q2B = max(Q2B, 0)

        # Question 2D

        Q2D = 0
        if((df.loc[Index, "Q2d_4"] == 1) | (df.loc[Index, "Q2d_33"] == 1)):
            Q2D = 1
        elif(df.loc[Index, "Q2d_8"] == 1):
            Q2D = 0.5
        if((df.loc[Index, "Q2d_27"] == 1) | (df.loc[Index, "Q2d_35"] == 1)):
            Q2D -= 0.25

        Q2D = max(Q2D, 0)

        # Question 2E

        Q2E = 0
        if((df.loc[Index, "Q2e_19"] == 1)  | (df.loc[Index, "Q2e_28"] == 1)):
            Q2E = 1
        elif((df.loc[Index, "Q2e_6"] == 1) | (df.loc[Index, "Q2e_14"] == 1)):
            Q2E = 0.5
        if((df.loc[Index, "Q2e_15"] == 1) | (df.loc[Index, "Q2e_18"] == 1) | (df.loc[Index, "Q2e_23"] == 1)):
            Q2E -= 0.25

        Q2E = max(Q2E, 0)

        # Question 3B

        Q3B = 0
        if((df.loc[Index, "Q3b_2"] == 1) | (df.loc[Index, "Q3b_11"] == 1)):
            Q3B = 1
        elif(df.loc[Index, "Q3b_6"] == 1):
            Q3B = 0.5
        if((df.loc[Index, "Q3b_9"] == 1) | (df.loc[Index, "Q3b_21"] == 1)):
            Q3B -= 0.25

        Q3B = max(Q3B, 0)

        # Question 3D

        Q3D = 0
        
        # if(df.loc[Index, "Q3c"] != 0):
        #     if(df.loc[Index, "Q3d_8"] == 1):
        #         Q3D = 1
        #     elif(df.loc[Index, "Q3d_5"] == 1):
        #         Q3D = 0.5
        #     if((df.loc[Index, "Q3d_3"] == 1) | (df.loc[Index, "Q3d_6"] == 1)):
        #         Q3D -= 0.25

        if(df.loc[Index, "Q3d_8"] == 1):
            Q3D = 1
        elif(df.loc[Index, "Q3d_5"] == 1):
            Q3D = 0.5
        if((df.loc[Index, "Q3d_3"] == 1) | (df.loc[Index, "Q3d_6"] == 1)):
            Q3D -= 0.25

        Q3D = max(Q3D, 0)


        # Question 3E

        Q3E = 0
        if((df.loc[Index, "Q3e_11"] == 1) | (df.loc[Index, "Q3e_28"] == 1)):
            Q3E = 1
        elif(df.loc[Index, "Q3e_13"] == 1):
            Q3E = 0.5
        if((df.loc[Index, "Q3e_22"] == 1) | (df.loc[Index, "Q3e_24"] == 1) | (df.loc[Index, "Q3e_32"] == 1)):
            Q3E -= 0.25

        Q3E = max(Q3E, 0)

        # Question 4B

        Q4B = 0
        if((df.loc[Index, "Q4b_4"] == 1) | (df.loc[Index, "Q4b_33"] == 1)):
            Q4B = 1
        elif(df.loc[Index, "Q4b_21"] == 1):
            Q4B = 0.5
        if((df.loc[Index, "Q4b_27"] == 1) | (df.loc[Index, "Q4b_35"] == 1)):
            Q4B -= 0.25

        Q4B = max(Q4B, 0)

        Scores.append([Q1B, Q1D, Q1E, Q2B, Q2D, Q2E, Q3B, Q3D, Q3E, Q4B])
        # Scores.append([Q1B, Q1D, Q1E, Q2B, Q2D, Q2E, Q3B, Q3E, Q4B])

    Scoresdf = pd.DataFrame(Scores, columns = ['Q1Bs', 'Q1Ds', 'Q1Es', 'Q2Bs', 'Q2Ds', 'Q2Es', 'Q3Bs', 'Q3Ds', 'Q3Es', 'Q4Bs'])
    # Scoresdf = pd.DataFrame(Scores, columns = ['Q1Bs', 'Q1Ds', 'Q1Es', 'Q2Bs', 'Q2Ds', 'Q2Es', 'Q3Bs', 'Q3Es', 'Q4Bs'])
    Scoresdf['TotalScores'] = Scoresdf.sum(axis = 1).astype(float)

    df = pd.concat([DataFrame, Scoresdf], axis = 1, join = 'inner')
    #df.loc[pd.isnull(df['Q3c']), 'Q3Ds'] = df.loc[pd.isnull(df['Q3c']), 'TotalScores'] / 9.0
    #df.loc[pd.isnull(df['Q3c']), 'Q3Ds'] = np.nan
    #df.loc[pd.isnull(df['Q3c']), 'TotalScores'] = df.loc[pd.isnull(df['Q3c']), 'TotalScores'] * 10.0 / 9.0
    if Output is not None:
        df.to_excel(Output, index = False)
    # print(df['TotalScores'].mean(), df['TotalScores'].std()/np.sqrt(len(df.index)))
    return df
