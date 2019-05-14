import numpy as np
import pandas as pd
import sys

def ValMat(*Surveys, DoMatch = True):
    global NumSurveys
    NumSurveys = len(Surveys)

    PostFile = Surveys[-1]
    dfPost = pd.read_csv(PostFile, skiprows = [1, 2])
    dfPost = Validate(dfPost, 'POST')
    NValidPost = len(dfPost.index)
    if(NumSurveys >= 2):
        PreFile = Surveys[0]
        dfPre = pd.read_csv(PreFile, skiprows = [1, 2])
        dfPre = Validate(dfPre, 'PRE')
        NValidPre = len(dfPre.index)
        if(NumSurveys == 2):
            if(DoMatch == True):
                dfPre, dfPost = Match(dfPre = dfPre, dfPost = dfPost) # Matching Pre and Post
            return NValidPre, NValidPost, dfPre, dfPost
        elif(NumSurveys == 3):
            MidFile = Surveys[1]
            dfMid = pd.read_csv(MidFile, skiprows = [1, 2])
            dfMid = Validate(dfMid, 'MID')
            NValidMid = len(dfMid.index)
            if(DoMatch == True):
                dfPre, dfMid, dfPost = Match(dfPre = dfPre, dfMid = dfMid, dfPost = dfPost) # Matching Pre, Mid, and Post
            return NValidPre, NValidMid, NValidPost, dfPre, dfMid, dfPost

    else:
        return NValidPost, dfPost

def Validate(df, Survey):
    if(Survey == 'POST'):
        df = df[(df['Finished'] == 1) & (df['Unnamed: 8'] == 1) & (df['Q6d'] == 2)] # Drop students who are not consenting, did not finish, or are not at least 18 at Post
    else:
        df = df[(df['Finished'] == 1)] # Drop students who did not finish the pre/mid survey
    df = df.dropna(how = 'all', subset = ['Q5a', 'Q5b', 'Q5c']) # Drop students who did not provide any id or first/last name
    df = df[(df['Qt1_3'] >= 30) | (df['Qt2_3'] >= 30) | (df['Qt3_3'] >= 30) | (df['Qt4_3'] >= 30)] # Drop students who do not spend at least 30s on one page

    return df

def Match(dfPre, dfPost, dfMid = None):
    dfPre = ProcessNames(dfPre)
    dfPost = ProcessNames(dfPost)

    PreNameSet = set.union(set(dfPre['FullName']), set(dfPre['BackName'])) # Get the pool of full names (including reversed) that are in the pre survey
    PostNameSet = set.union(set(dfPost['FullName']), set(dfPost['BackName'])) # Get the pool of full names (including reversed) that are in the post survey
    if np.nan in PreNameSet:
        PreNameSet = PreNameSet.remove(np.nan)
    if np.nan in PostNameSet:
        PostNameSet = PostNameSet.remove(np.nan)

    if(NumSurveys == 2):
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
    if(NumSurveys == 2):
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
        df['Q5a'] = df['Q5a'].astype(str).str.split('@').str.get(0).str.lower() # Keep only first part of email addresses and take the lower case of all ids
        df['FullName'] = (df['Q5b'].apply(str).str.lower() + df['Q5c'].apply(str).str.lower()).str.replace('\W', '') # Get full name in lower case with no white space
        df['BackName'] = (df['Q5c'].apply(str).str.lower() + df['Q5b'].apply(str).str.lower()).str.replace('\W', '') # Get reverse full name in lower case with no white space
        df = df[df['FullName'].map(len) > 2] # Keep only full names with more than 2 characters
        df = df.drop_duplicates(subset = ['FullName']).drop_duplicates(subset = ['Q5a']) # Drop second entry if there are duplicate full names

        return df
