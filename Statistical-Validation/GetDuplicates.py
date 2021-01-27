import os
import sys
import numpy as np
import pandas as pd
from glob import glob
os.chdir('C:/Users/Cole/Documents/GitHub/PLIC/Automation-Files/')
import Valid_Matched
import Scoring

def BuildDuplicatedDataset(dir = 'C:/Users/Cole/Documents/DATA/PLIC_DATA/'):
    """Create dataframe of students who completed the PLIC multiple times (validly) in the same semester at the same timepoint.

    Keyword arguments:
    dir -- base directory where PLIC data are stored
    """

    os.chdir(dir)
    Weights = pd.read_excel('Weights_May2019.xlsx').transpose()[0]
    Basedf = pd.read_csv('PLIC_May2019.csv', nrows = 1)
    MainSurveys_Folder = 'SurveysMay2019/'
    Questions = ['Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 'Q3b', 'Q3d', 'Q3e', 'Q4b']

    dfs = []
    files = glob('SurveysMay2019/**/*May2019.csv', recursive = True)
    for f in files:
        df = pd.read_csv(f, skiprows = [1]).dropna(subset = ['Q5b', 'Q5c'])
        df = Valid_Matched.Validate(df, 'PRE')
        if 'Survey' in df.columns:
            df = df.loc[df['Survey'] != 'F'].dropna(subset = ['Q3c'])
        if df.empty:
            continue
        df['Q5b'] = df['Q5b'].apply(str).str.lower().str.replace('\W', '')
        df['Q5c'] = df['Q5c'].apply(str).str.lower().str.replace('\W', '')
        df = df.loc[df.duplicated(subset = ['Q5b', 'Q5c'], keep = False), :]
        if not df.empty:
            df['Time'] = f.split('_')[-4]
            df['Class_ID'] = '_'.join(f.split('_')[-3:-1])
            dfs.append(df)

    df = pd.concat(dfs, axis = 0)

    df['anon_student_id'] = (df['Q5b'] + df['Q5c'] + df['Time']).astype(str).astype('category').cat.codes
    df = Scoring.CalcScore(df, Weights)
    df.to_csv('Collective_Surveys/DuplicatedSurveys.csv', index = False)

    return df
