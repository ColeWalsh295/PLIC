import numpy as np
import pandas as pd
import sys

def ValMat(*Surveys, Export = True):
    NumSurveys = len(Surveys)

    PostFile = Surveys[-1]
    dfPost = pd.read_csv(PostFile, skiprows = [1, 2])
    dfPost = Validate(dfPost, 'POST')
    NValidPre = len(dfPost.index)

    if(NumSurveys >= 2):
        PreFile = Surveys[0]
        dfPre = pd.read_csv(PreFile, skiprows = [1, 2])
        dfPre = Validate(dfPre, 'PRE')
        NValidPre = len(dfPre.index)

        if(NumSurveys == 2):
            dfPre, dfPost = Match2(dfPre, dfPost)

            if Export:
                dfPre.to_csv(PreFile[:-4] + '_ValMat.csv', index = False)
                dfPost.to_csv(PostFile[:-4] + '_ValMat.csv', index = False)

            return NValidPre, NValidPost, dfPre, dfPost

        elif(NumSurveys == 3):
            MidFile = Surveys[1]
            dfMid = pd.read_csv(MidFile, skiprows = [1, 2])
            dfMid = Validate(dfMid, 'MID')
            NValidPre = len(dfMid.index)

            dfPre, dfMid, dfPost = Match3(dfPre, dfMid, dfPost)

            if Export:
                dfPre.to_csv(PreFile[:-4] + '_ValMat.csv', index = False)
                dfMid.to_csv(MidFile[:-4] + '_ValMat.csv', index = False)
                dfPost.to_csv(PostFile[:-4] + '_ValMat.csv', index = False)

                return NValidPre, NValidMid, NValidPost, dfPre, dfMid, dfPost

        else:
            dfPost = dfPost.reset_index(drop = True)

            if Export:
                dfPost.to_csv(PostFile[:-4] + '_Valid.csv', index = False)

            return NValidPost, dfPost

def Validate(df, Survey):
    if(Survey == 'POST'):
        df = df[(df['Finished'] == 1) & (df['Unnamed: 8'] == 1) & (df['Q6d'] == 2)] # Drop students who are not consenting, did not finish, or are not at least 18 at Post
    else:
        df = df[(df['Finished'] == 1)] # Drop students who did not finish the pre/mid survey
    df = df.dropna(how = 'all', subset = ['Q5a', 'Q5b', 'Q5c']) # Drop students who did not provide any id or first/last name
    df = df[(df['Qt1_3'] >= 30) | (df['Qt2_3'] >= 30) | (df['Qt3_3'] >= 30) | (df['Qt4_3'] >= 30)] # Drop students who do not spend at least 30s on one page

    return df

def Match2(dfPre, dfPost, Where):
    dfPre = ProcessNames(dfPre)
    dfPost = ProcessNames(dfPost)

    Intersection_ID = set.intersection(set(dfPre['Q5a']), set(dfPost['Q5a'])) # Get ids that are in both pre and post surveys
    PreNameSet = set.union(set(dfPre['FullName']), set(dfPre['BackName'])) # Get the pool of full names (including reversed) that are in the pre survey
    PostNameSet = set.union(set(dfPost['FullName']), set(dfPost['BackName'])) # Get the pool of full names (including reversed) that are in the post survey

    if np.nan in Intersection_ID:
        Intersection_ID = Intersection_ID.remove(np.nan)
    if np.nan in PreNameSet:
        PreNameSet = PreNameSet.remove(np.nan)
    if np.nan in PostNameSet:
        PostNameSet = PostNameSet.remove(np.nan)

    # Match on ID or partial name matching (i.e., smithwill = smithwilliam and andrewwhite = drewwhite)
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

        # dfPre[['Q5a', 'Q5b', 'Q5c']].to_csv('PRE_Unmatched.csv', index = False)
        # dfPost[['Q5a', 'Q5b', 'Q5c']].to_csv('POST_Unmatched.csv', index = False)

    dfPre = dfPre.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)
    dfPost = dfPost.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)

    return dfPre, dfPost

def Match3(dfPre, dfMid, dfPost, Where):

    dfPre['Q5a'] = dfPre['Q5a'].apply(str).str.split('@').str.get(0).str.lower()
    dfMid['Q5a'] = dfMid['Q5a'].apply(str).str.split('@').str.get(0).str.lower()
    dfPost['Q5a'] = dfPost['Q5a'].apply(str).str.split('@').str.get(0).str.lower()

    dfPre['FullName'] = (dfPre['Q5b'].apply(str).str.lower() + dfPre['Q5c'].apply(str).str.lower()).str.replace('\W', '')
    dfMid['FullName'] = (dfMid['Q5b'].apply(str).str.lower() + dfMid['Q5c'].apply(str).str.lower()).str.replace('\W', '')
    dfPost['FullName'] = (dfPost['Q5b'].apply(str).str.lower() + dfPost['Q5c'].apply(str).str.lower()).str.replace('\W', '')

    dfPre['BackName'] = (dfPre['Q5c'].apply(str).str.lower() + dfPre['Q5b'].apply(str).str.lower()).str.replace('\W', '')
    dfMid['BackName'] = (dfMid['Q5c'].apply(str).str.lower() + dfMid['Q5b'].apply(str).str.lower()).str.replace('\W', '')
    dfPost['BackName'] = (dfPost['Q5c'].apply(str).str.lower() + dfPost['Q5b'].apply(str).str.lower()).str.replace('\W', '')

    dfPre = dfPre[dfPre['FullName'].map(len) > 4]
    dfMid = dfMid[dfMid['FullName'].map(len) > 4]
    dfPost = dfPost[dfPost['FullName'].map(len) > 4]

    dfPre = dfPre.drop_duplicates(subset = ['FullName'])
    dfMid = dfMid.drop_duplicates(subset = ['FullName'])
    dfPost = dfPost.drop_duplicates(subset = ['FullName'])

    Intersection_ID = set.intersection(set(dfPre['Q5a']), set(dfMid['Q5a']), set(dfPost['Q5a']))

    PreNameSet = set.union(set(dfPre['FullName']), set(dfPre['BackName']))
    MidNameSet = set.union(set(dfMid['FullName']), set(dfMid['BackName']))
    PostNameSet = set.union(set(dfPost['FullName']), set(dfPost['BackName']))

    if np.nan in Intersection_ID:
        Intersection_ID = Intersection_ID.remove(np.nan)
    if np.nan in PreNameSet:
        PreNameSet = PreNameSet.remove(np.nan)
    if np.nan in MidNameSet:
        MidNameSet = MidNameSet.remove(np.nan)
    if np.nan in PostNameSet:
        PostNameSet = PostNameSet.remove(np.nan)

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

    if(Where == 'Local'):
        print("Preliminary Matched (Pre): " + str(len(dfPre.index)))
        print("Preliminary Matched (Mid): " + str(len(dfMid.index)))
        print("Preliminary Matched (Post): " + str(len(dfPost.index)))

    if((len(dfPre.index) != len(dfMid.index)) or (len(dfPre.index) != len(dfPost.index)) or (len(dfMid.index) != len(dfPost.index))):

        PreRemove = (dfPre['FullName'].isin(set(dfPre['FullName']).difference(set(dfMid['FullName']).union(set(dfMid['BackName'])))) &
                        dfPre['FullName'].isin(set(dfPre['FullName']).difference(set(dfPost['FullName']).union(set(dfPost['BackName'])))) & ~(dfPre['Q5a'].isin(Intersection_ID)))
        if(np.sum(PreRemove) != 0):
            dfPre = dfPre.drop(labels = dfPre[PreRemove].index, axis = 0)

        MidRemove = (dfMid['FullName'].isin(set(dfMid['FullName']).difference(set(dfPre['FullName']).union(set(dfPre['BackName'])))) &
                        dfMid['FullName'].isin(set(dfMid['FullName']).difference(set(dfPost['FullName']).union(set(dfPost['BackName'])))) & ~(dMid['Q5a'].isin(Intersection_ID)))
        if(np.sum(PreRemove) != 0):
            dfPre = dfPre.drop(labels = dfPre[PreRemove].index, axis = 0)

        PostRemove = (dfPost['FullName'].isin(set(dfPost['FullName']).difference(set(dfPre['FullName']).union(set(dfPre['BackName'])))) &
                        dfPost['FullName'].isin(set(dfPost['FullName']).difference(set(dfMid['FullName']).union(set(dfMid['BackName'])))) & ~(dfPost['Q5a'].isin(Intersection_ID)))
        if(np.sum(PostRemove) != 0):
            dfPost = dfPost.drop(labels = dfPost[PostRemove].index, axis = 0)

        if(Where == 'Local'):
            print('PRE not in one of other surveys: {}'.format(PreRemove.sum()))
            print('MID not in one of other surveys: {}'.format(MidRemove.sum()))
            print('POST not in one of other surveys: {}'.format(PostRemove.sum()))

            print("Matched (Pre): " + str(len(dfPre.index)))
            print("Matched (Mid): " + str(len(dfMid.index)))
            print("Matched (Post): " + str(len(dfPost.index)))

    dfPre = dfPre.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)
    dfMid = dfMid.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)
    dfPost = dfPost.drop(columns = ['FullName', 'BackName']).reset_index(drop = True)

    assert(len(dfPre.index) == len(dfMid.index))
    assert(len(dfPre.index) == len(dfPost.index))
    assert(len(dfMid.index) == len(dfPost.index))

    return dfPre, dfMid, dfPost

def ProcessNames(df):
        df['Q5a'] = df['Q5a'].astype(str).str.split('@').str.get(0).str.lower() # Keep only first part of email addresses and take the lower case of all ids
        df['FullName'] = (df['Q5b'].apply(str).str.lower() + df['Q5c'].apply(str).str.lower()).str.replace('\W', '') # Get full name in lower case with no white space
        df['BackName'] = (df['Q5c'].apply(str).str.lower() + df['Q5b'].apply(str).str.lower()).str.replace('\W', '') # Get reverse full name in lower case with no white space
        df = df[df['FullName'].map(len) > 2] # Keep only full names with more than 2 characters
        df = df.drop_duplicates(subset = ['FullName']).drop_duplicates(subset = ['Q5a']) # Drop second entry if there are duplicate full names
