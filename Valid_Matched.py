import numpy as np
import pandas as pd
import sys

def ValMat(*Surveys, Where = 'Local', Type = 'C', To_Excel = True):
    NumSurveys = len(Surveys)

    if(Where == 'Local'):
        PostFile = Surveys[-1]
        dfPost = pd.read_excel(PostFile, skiprows = [1])

        dfPost = dfPost[dfPost['V5'] == 1]
        print("Finished (Post): " + str(len(dfPost.index)))

        dfPost = dfPost[(dfPost['Unnamed: 7'] == 1) & (dfPost['Q6d'] == 2)]
        print("Valid (Post): " + str(len(dfPost.index)))

        NValidPost = len(dfPost.index)

        dfPost = dfPost.dropna(how = 'all', subset = ['Q5a', 'Q5b', 'Q5c'])
        if(('Survey' in dfPost.columns) and (Type is not None)):
            dfPost = dfPost[dfPost['Survey'] == Type].reset_index(drop = True)
        print("Correct Format (Post): " + str(len(dfPost.index)))

        if(NumSurveys >= 2):
            PreFile = Surveys[0]
            dfPre = pd.read_excel(PreFile, skiprows = [1])

            dfPre = dfPre[dfPre['V5'] == 1]
            print("Valid and Finished (Pre): " + str(len(dfPre.index)))

            NValidPre = len(dfPre.index)

            dfPre = dfPre.dropna(how = 'all', subset = ['Q5a', 'Q5b', 'Q5c'])
            if(('Survey' in dfPre.columns) and (Type is not None)):
                dfPre = dfPre[dfPre['Survey'] == Type].reset_index(drop = True)
            print("Correct Format (Pre): " + str(len(dfPre.index)))

            if(NumSurveys == 2):
                dfPre, dfPost = Match2(dfPre, dfPost, Where = Where)

                if(To_Excel == True):
                    dfPre.to_excel(PreFile[:-5] + '_ValMat.xlsx', index = False)
                    dfPost.to_excel(PostFile[:-5] + '_ValMat.xlsx', index = False)

                return NValidPre, NValidPost, dfPre, dfPost

            elif(NumSurveys == 3):
                MidFile = Surveys[1]
                dfMid = pd.read_excel(MidFile, skiprows = [1])

                dfMid = dfMid[dfMid['V5'] == 1]
                print("Valid and Finished (Mid): " + str(len(dfMid.index)))

                NValidMid = len(dfMid.index)

                dfMid = dfMid.dropna(how = 'all', subset = ['Q5a', 'Q5b', 'Q5c'])
                if(('Survey' in dfMid.columns) and (Type is not None)):
                    dfMid = dfMid[dfMid['Survey'] == Type].reset_index(drop = True)
                print("Correct Format (Mid): " + str(len(dfMid.index)))

                dfPre, dfMid, dfPost = Match3(dfPre, dfMid, dfPost, Where = Where)

                if(To_Excel == True):
                    dfPre.to_excel(PreFile[:-5] + '_ValMat.xlsx', index = False)
                    dfMid.to_excel(MidFile[:-5] + '_ValMat.xlsx', index = False)
                    dfPost.to_excel(PostFile[:-5] + '_ValMat.xlsx', index = False)

                return NValidPre, NValidMid, NValidPost, dfPre, dfMid, dfPost

        else:
            dfPost = dfPost.reset_index(drop = True)

            if(To_Excel == True):
                dfPost.to_excel(PostFile[:-5] + '_Valid.xlsx', index = False)

            return NValidPost, dfPost

    else:
        PostFile = Surveys[-1]
        dfPost = pd.read_csv(PostFile, skiprows = [1, 2])

        dfPost = dfPost[dfPost['Finished'] == 1]
        dfPost = dfPost[(dfPost['Unnamed: 8'] == 1) & (dfPost['Q6d'] == 2)]

        NValidPost = len(dfPost.index)

        dfPost = dfPost.dropna(how = 'all', subset = ['Q5a', 'Q5b', 'Q5c'])
        dfPost = dfPost.dropna(subset = ['Qt4_3'])

        if(NumSurveys >= 2):
            PreFile = Surveys[0]
            dfPre = pd.read_csv(PreFile, skiprows = [1, 2])

            dfPre = dfPre[dfPre['Finished'] == 1]

            NValidPre = len(dfPre.index)

            dfPre = dfPre.dropna(how = 'all', subset = ['Q5a', 'Q5b', 'Q5c'])
            dfPre = dfPre.dropna(subset = ['Qt4_3'])

            if(NumSurveys == 2):
                dfPre, dfPost = Match2(dfPre, dfPost, Where = Where)

                dfPre.to_csv(PreFile[:-4] + '_ValMat.csv', index = False)
                dfPost.to_csv(PostFile[:-4] + '_ValMat.csv', index = False)

                return NValidPre, NValidPost, dfPre, dfPost

            elif(NumSurveys == 3):
                MidFile = Surveys[1]
                dfMid = pd.read_csv(MidFile, skiprows = [1])

                dfMid = dfMid[dfMid['Finished'] == 1]
                print("Valid and Finished (Mid): " + str(len(dfMid.index)))

                NValidMid = len(dfMid.index)

                dfMid = dfMid.dropna(how = 'all', subset = ['Q5a', 'Q5b', 'Q5c'])
                dfMid = dfMid.dropna(subset = ['Qt4_3'])

                dfPre, dfMid, dfPost = Match3(dfPre, dfMid, dfPost, Where = Where)

                dfPre.to_csv(PreFile[:-4] + '_ValMat.csv', index = False)
                dfMid.to_csv(MidFile[:-4] + '_ValMat.csv', index = False)
                dfPost.to_csv(PostFile[:-4] + '_ValMat.csv', index = False)

                return NValidPre, NValidMid, NValidPost, dfPre, dfMid, dfPost

        else:
            dfPost = dfPost.reset_index(drop = True)
            dfPost.to_csv(PostFile[:-4] + '_Valid.csv', index = False)

            return NValidPost, dfPost

def Match2(dfPre, dfPost, Where):

    dfPre['Q5a'] = dfPre['Q5a'].astype(str).str.split('@').str.get(0).str.lower()
    dfPost['Q5a'] = dfPost['Q5a'].astype(str).str.split('@').str.get(0).str.lower()

    dfPre['FullName'] = (dfPre['Q5b'].apply(str).str.lower() + dfPre['Q5c'].apply(str).str.lower()).str.replace('\W', '')
    dfPost['FullName'] = (dfPost['Q5b'].apply(str).str.lower() + dfPost['Q5c'].apply(str).str.lower()).str.replace('\W', '')

    dfPre['BackName'] = (dfPre['Q5c'].apply(str).str.lower() + dfPre['Q5b'].apply(str).str.lower()).str.replace('\W', '')
    dfPost['BackName'] = (dfPost['Q5c'].apply(str).str.lower() + dfPost['Q5b'].apply(str).str.lower()).str.replace('\W', '')

    dfPre = dfPre[dfPre['FullName'].map(len) > 2]
    dfPost = dfPost[dfPost['FullName'].map(len) > 2]

    dfPre = dfPre.drop_duplicates(subset = ['FullName']).drop_duplicates(subset = ['Q5a'])
    dfPost = dfPost.drop_duplicates(subset = ['FullName']).drop_duplicates(subset = ['Q5a'])

    Intersection_ID = set.intersection(set(dfPre['Q5a']), set(dfPost['Q5a']))

    PreNameSet = set.union(set(dfPre['FullName']), set(dfPre['BackName']))
    PostNameSet = set.union(set(dfPost['FullName']), set(dfPost['BackName']))

    if np.nan in Intersection_ID:
        Intersection_ID = Intersection_ID.remove(np.nan)
    if np.nan in PreNameSet:
        PreNameSet = PreNameSet.remove(np.nan)
    if np.nan in PostNameSet:
        PostNameSet = PostNameSet.remove(np.nan)

    dfPre = dfPre[(dfPre['Q5a'].isin(Intersection_ID)) | (dfPre['FullName'].str.contains('|'.join(list(PostNameSet)))) | (dfPre['FullName'].apply(lambda n: n in '|'.join(list(PostNameSet))))].reset_index(drop = True)
    dfPost = dfPost[(dfPost['Q5a'].isin(Intersection_ID)) | (dfPost['FullName'].str.contains('|'.join(list(PreNameSet)))) | (dfPost['FullName'].apply(lambda n: n in '|'.join(list(PreNameSet))))].reset_index(drop = True)

    if(Where == 'Local'):
        print("Preliminary Matched (Pre): " + str(len(dfPre.index)))
        print("Preliminary Matched (Post): " + str(len(dfPost.index)))

    if(len(dfPre.index) != len(dfPost.index)):

        PreRemove = ((dfPre['FullName'].isin(set(dfPre['FullName']).difference(set(dfPost['FullName']).union(set(dfPost['BackName']))))) & ~(dfPre['Q5a'].isin(Intersection_ID)))
        if(np.sum(PreRemove) != 0):
            dfPre = dfPre.drop(labels = dfPre[PreRemove].index, axis = 0)

        PostRemove = (dfPost['FullName'].isin(set(dfPost['FullName']).difference(set(dfPre['FullName']).union(set(dfPre['BackName'])))) & ~(dfPost['Q5a'].isin(Intersection_ID)))
        if(np.sum(PostRemove) != 0):
            dfPost = dfPost.drop(labels = dfPost[PostRemove].index, axis = 0)

        if(Where == 'Local'):
            print('PRE not in POST: {}'.format(PreRemove.sum()))
            print('POST not in PRE: {}'.format(PostRemove.sum()))

            print("Matched (Pre): " + str(len(dfPre.index)))
            print("Matched (Post): " + str(len(dfPost.index)))

    try:
        assert(len(dfPre.index) == len(dfPost.index))
    except:
        try:
            dfPre = dfPre[dfPre['Q5a'].isin(set(dfPost['Q5a'])) | dfPre['FullName'].isin(set.union(set(dfPost['FullName']), set(dfPost['BackName'])))].reset_index(drop = True)
            dfPost = dfPost[dfPost['Q5a'].isin(set(dfPre['Q5a'])) | dfPost['FullName'].isin(set.union(set(dfPre['FullName']), set(dfPre['BackName'])))].reset_index(drop = True)
            assert(len(dfPre.index) == len(dfPost.index))
        except:
            dfPre = dfPre[dfPre['Q5a'].isin(set(dfPost['Q5a'])) | dfPre['FullName'].isin(set(dfPost['FullName']))].reset_index(drop = True)
            dfPost = dfPost[dfPost['Q5a'].isin(set(dfPre['Q5a'])) | dfPost['FullName'].isin(set(dfPre['FullName']))].reset_index(drop = True)

            dfPre.to_csv('PreError.csv', index = False)
            dfPost.to_csv('PostError.csv', index = False)

            print(len(dfPre.index))
            print(len(dfPost.index))

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
