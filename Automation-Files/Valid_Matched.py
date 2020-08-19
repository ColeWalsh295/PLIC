import numpy as np
import pandas as pd
import sys

def ValMat(DoMatch = True, **Dataframes):
    """Filter out invalid PLIC responses and match students

    Keyword arguments:
    DoMatch -- binary; whether to match survey responses by student
    Dataframes -- pandas dataframes of students responses to the PRE, MID, and/or POST survey
    """

    dfPost = Dataframes['POST']
    dfPost = Validate(dfPost, 'POST')
    NValidPost = len(dfPost.index)
    if('PRE' in Dataframes.keys()): # conditions dictate which surveys to look for, validate, and match
        dfPre = Dataframes['PRE']
        dfPre = Validate(dfPre, 'PRE')
        NValidPre = len(dfPre.index)
        if('MID' not in Dataframes.keys() and DoMatch == True):
            dfPre, dfPost = Match(dfPre = dfPre, dfPost = dfPost)
            return NValidPre, NValidPost, dfPre, dfPost
        elif('MID' in Dataframes.keys()):
            dfMid = Dataframes['MID']
            dfMid = Validate(dfMid, 'MID')
            NValidMid = len(dfMid.index)
            if(DoMatch == True):
                dfPre, dfMid, dfPost = Match(dfPre = dfPre, dfMid = dfMid, dfPost = dfPost)
            return NValidPre, NValidMid, NValidPost, dfPre, dfMid, dfPost

    else:
        return NValidPost, dfPost

def Validate(df, Survey):
    """Remove invalid survey responses to the PLIC

    Keyword arguments:
    df -- pandas dataframe of student responses to the PLIC
    Survey -- which survey to validate: PRE/MID/ or POST
    """

    if(Survey == 'POST'):
        df = df[(df['V5'] == 1) & (df['Unnamed: 7'] == 1) & (df['Q6d'] == 2)] # must finish, consent, and be at least 18 at posttest
    else:
        df = df[(df['V5'] == 1)] # just need to finish any othe survey
    df = df.dropna(how = 'all', subset = ['Q5a', 'Q5b', 'Q5c']) # drop students who did not provide any id or first/last name
    df = df[(df['Qt1_3'] >= 30) | (df['Qt2_3'] >= 30) | (df['Qt3_3'] >= 30) | (df['Qt4_3'] >= 30)] # drop students who do not spend at least 30s on one page

    return df

def Match(dfPre, dfPost, dfMid = None):
    """Match students' responses across multiple surveys

    Keyword arguments:
    dfPre -- pandas dataframe of pretest survey responses
    dfPost -- pandas dataframe of posttest survey responses
    dfMid -- pandas dataframe of midtest survey responses
    """

    dfPre = ProcessNames(dfPre)
    dfPost = ProcessNames(dfPost)

    PreNameSet = set.union(set(dfPre['FullName']), set(dfPre['BackName'])) # Get the pool of full names (including reversed) that are in the pre survey
    PostNameSet = set.union(set(dfPost['FullName']), set(dfPost['BackName'])) # and same for post
    if np.nan in PreNameSet:
        PreNameSet = PreNameSet.remove(np.nan)
    if np.nan in PostNameSet:
        PostNameSet = PostNameSet.remove(np.nan)

    if(dfMid is None):
        Intersection_ID = set.intersection(set(dfPre['Q5a']), set(dfPost['Q5a'])) # Get ids that are in both pre and post surveys
    else:
        dfMid = ProcessNames(dfMid)
        Intersection_ID = set.intersection(set(dfPre['Q5a']), set(dfMid['Q5a']), set(dfPost['Q5a']))
        MidNameSet = set.union(set(dfMid['FullName']), set(dfMid['BackName']))
        if np.nan in MidNameSet:
            MidNameSet = MidNameSet.remove(np.nan)

    if np.nan in Intersection_ID:
        Intersection_ID = Intersection_ID.remove(np.nan)

    # Match on ID or partial name matching (i.e., smithwill = smithwilliam and andrewwhite = drewwhite)
    if(dfMid is None):
        dfPre = dfPre[(dfPre['Q5a'].isin(Intersection_ID)) | (dfPre['FullName'].str.contains('|'.join(list(PostNameSet)))) | (dfPre['FullName'].apply(lambda n: n in '|'.join(list(PostNameSet))))].reset_index(drop = True)
        dfPost = dfPost[(dfPost['Q5a'].isin(Intersection_ID)) | (dfPost['FullName'].str.contains('|'.join(list(PreNameSet)))) | (dfPost['FullName'].apply(lambda n: n in '|'.join(list(PreNameSet))))].reset_index(drop = True)

        if(len(dfPre.index) != len(dfPost.index)): # Sometimes this overmatches
            try: # First, we'll revert to exact matching on id or full name (including reversed)
                dfPre = dfPre[dfPre['Q5a'].isin(set(dfPost['Q5a'])) | dfPre['FullName'].isin(set.union(set(dfPost['FullName']), set(dfPost['BackName'])))].reset_index(drop = True)
                dfPost = dfPost[dfPost['Q5a'].isin(set(dfPre['Q5a'])) | dfPost['FullName'].isin(set.union(set(dfPre['FullName']), set(dfPre['BackName'])))].reset_index(drop = True)
                assert(len(dfPre.index) == len(dfPost.index))
            except: # Next, we'll try exact matching on id or full name (not reversed)
                dfPre = dfPre[dfPre['Q5a'].isin(set(dfPost['Q5a'])) | dfPre['FullName'].isin(set(dfPost['FullName']))].reset_index(drop = True)
                dfPost = dfPost[dfPost['Q5a'].isin(set(dfPre['Q5a'])) | dfPost['FullName'].isin(set(dfPre['FullName']))].reset_index(drop = True)
                assert(len(dfPre.index) == len(dfPost.index))

        dfPre = dfPre.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)
        dfPost = dfPost.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)

        return dfPre, dfPost
    else: # Match intersection of all three surveys
        dfPre = dfPre[(dfPre['Q5a'].isin(Intersection_ID)) | ((dfPre['FullName'].str.contains('|'.join(list(MidNameSet)))) & (dfPre['FullName'].str.contains('|'.join(list(PostNameSet))))) |
                        ((dfPre['FullName'].str.contains('|'.join(list(MidNameSet)))) & (dfPre['FullName'].apply(lambda n: n in '|'.join(list(PostNameSet))))) |
                        ((dfPre['FullName'].apply(lambda n: n in '|'.join(list(MidNameSet)))) & (dfPre['FullName'].str.contains('|'.join(list(PostNameSet))))) |
                        ((dfPre['FullName'].apply(lambda n: n in '|'.join(list(MidNameSet)))) & (dfPre['FullName'].apply(lambda n: n in '|'.join(list(PostNameSet)))))].reset_index(drop = True)

        dfMid = dfMid[(dfMid['Q5a'].isin(Intersection_ID)) | ((dfMid['FullName'].str.contains('|'.join(list(PreNameSet)))) & (dfMid['FullName'].str.contains('|'.join(list(PostNameSet))))) |
                        ((dfMid['FullName'].str.contains('|'.join(list(PreNameSet)))) & (dfMid['FullName'].apply(lambda n: n in '|'.join(list(PostNameSet))))) |
                        ((dfMid['FullName'].apply(lambda n: n in '|'.join(list(PreNameSet)))) & (dfMid['FullName'].str.contains('|'.join(list(PostNameSet))))) |
                        ((dfMid['FullName'].apply(lambda n: n in '|'.join(list(PreNameSet)))) & (dfMid['FullName'].apply(lambda n: n in '|'.join(list(PostNameSet)))))].reset_index(drop = True)

        dfPost = dfPost[(dfPost['Q5a'].isin(Intersection_ID)) | ((dfPost['FullName'].str.contains('|'.join(list(PreNameSet)))) & (dfPost['FullName'].str.contains('|'.join(list(MidNameSet))))) |
                        ((dfPost['FullName'].str.contains('|'.join(list(PreNameSet)))) & (dfPost['FullName'].apply(lambda n: n in '|'.join(list(MidNameSet))))) |
                        ((dfPost['FullName'].apply(lambda n: n in '|'.join(list(PreNameSet)))) & (dfPost['FullName'].str.contains('|'.join(list(MidNameSet))))) |
                        ((dfPost['FullName'].apply(lambda n: n in '|'.join(list(PreNameSet)))) & (dfPost['FullName'].apply(lambda n: n in '|'.join(list(MidNameSet)))))].reset_index(drop = True)

        if((len(dfPre.index) != len(dfMid.index)) or (len(dfPre.index) != len(dfPost.index)) or (len(dfMid.index) != len(dfPost.index))):
            try: # First, we'll revert to exact matching on id or full name (including reversed)
                dfPre = dfPre[(dfPre['Q5a'].isin(Intersection_ID)) | dfPre['FullName'].isin(set.intersection(MidNameSet, PostNameSet))].reset_index(drop = True)
                dfMid = dfMid[(dfMid['Q5a'].isin(Intersection_ID)) | dfMid['FullName'].isin(set.intersection(PreNameSet, PostNameSet))].reset_index(drop = True)
                dfPost = dfPost[(dfPost['Q5a'].isin(Intersection_ID)) | dfPost['FullName'].isin(set.intersection(PreNameSet, MidNameSet))].reset_index(drop = True)
                assert((len(dfPre.index) == len(dfMid.index)) & (len(dfPre.index) == len(dfPost.index)) & (len(dfMid.index) == len(dfPost.index)))
            except: # Next, we'll try exact matching on id or full name (not reversed)
                dfPre = dfPre[(dfPre['Q5a'].isin(Intersection_ID)) | dfPre['FullName'].isin(set(dfMid['FullName']).intersection(set(dfPost['FullName'])))].reset_index(drop = True)
                dfMid = dfMid[(dfMid['Q5a'].isin(Intersection_ID)) | dfMid['FullName'].isin(set(dfPre['FullName']).intersection(set(dfPost['FullName'])))].reset_index(drop = True)
                dfPost = dfPost[(dfPost['Q5a'].isin(Intersection_ID)) | dfPost['FullName'].isin(set(dfPre['FullName']).intersection(set(dfMid['FullName'])))].reset_index(drop = True)
                assert((len(dfPre.index) == len(dfMid.index)) & (len(dfPre.index) == len(dfPost.index)) & (len(dfMid.index) == len(dfPost.index)))

        dfPre = dfPre.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)
        dfMid = dfMid.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)
        dfPost = dfPost.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)

        return dfPre, dfMid, dfPost

def ProcessNames(df):
    """Process students' names and IDs for analysis and merging

    Keyword arguments:
    df -- pandas dataframe of student responses to the PLIC
    """
    
    df['Q5a'] = df['Q5a'].astype(str).str.split('@').str.get(0).str.lower() # Keep only first part of email addresses and take the lower case of all ids
    df['FullName'] = (df['Q5b'].apply(str).str.lower() + df['Q5c'].apply(str).str.lower()).str.replace('\W', '') # Get full name in lower case with no white space
    df['BackName'] = (df['Q5c'].apply(str).str.lower() + df['Q5b'].apply(str).str.lower()).str.replace('\W', '') # Get reverse full name in lower case with no white space
    df.loc[df['FullName'].map(len) <= 2, 'FullName'] = '' # Keep only full names with more than 2 characters
    df = df.drop_duplicates(subset = ['FullName']).drop_duplicates(subset = ['Q5a']) # Drop second entry if there are duplicate full names

    return df
