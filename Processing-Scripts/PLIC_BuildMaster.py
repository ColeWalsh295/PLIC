import os
import sys
import numpy as np
import pandas as pd
from glob import glob
os.chdir('C:/Users/Cole/Documents/GitHub/PLIC/Automation-Files/')
from PythonAutomation import DownloadResponses
import Valid_Matched
import Scoring
import datetime

os.chdir('C:/Users/Cole/Documents/DATA/PLIC_DATA/')
Weights = pd.read_excel('Weights_May2019.xlsx').transpose()[0]
Basedf = pd.read_csv('PLIC_May2019.csv', nrows = 1) # current PLIC version
MainSurveys_Folder = 'SurveysMay2019/' # where are current version surveys
Questions = ['Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 'Q3b', 'Q3d', 'Q3e', 'Q4b']

def GetAllData(df, mainDirectory, startDate = None, endDate = None, Completed = True):
    """Download and validate all surveys within a given date range.

    Keyword arguments:
    df -- pandas dataframe of master PLIC data file with instructor responses
    mainDirectory -- directory to download PLIC data
    startDate -- beginning of date range of survey close dates to download (format = %m/%d/%Y)
    endDate -- end of date range of survey close dates to download (format = %m/%d/%Y)
    Completed -- binary; whether to retrieve only data where all surveys have closed
    """

    df['Pre-Survey Closed'] = pd.to_datetime(df['Pre-Survey Closed'])
    df['Post-Survey Closed'] = pd.to_datetime(df['Post-Survey Closed'])
    if(startDate is not None):
        if Completed:
            df = df.loc[df['Post-Survey Closed'] > datetime.datetime.strptime(startDate, '%m/%d/%Y')]
        else:
            df = df.loc[(df['Pre-Survey Closed'] > datetime.datetime.strptime(startDate, '%m/%d/%Y')) | (df['Post-Survey Closed'] > datetime.datetime.strptime(startDate, '%m/%d/%Y'))]
    if(endDate is not None):
        if Completed:
            df = df.loc[df['Post-Survey Closed'] < datetime.datetime.strptime(endDate, '%m/%d/%Y')]
        else:
            df = df.loc[(df['Pre-Survey Closed'] < datetime.datetime.strptime(endDate, '%m/%d/%Y')) | (df['Post-Survey Closed'] < datetime.datetime.strptime(endDate, '%m/%d/%Y'))]


    df = df.reset_index(drop = True)
    for Index, Class in df.iterrows():
        TermDir = mainDirectory + "/" + str(Class['Season']) + str(Class['Course Year'])
        if not os.path.exists(TermDir):
            os.mkdir(TermDir, 755)
            os.mkdir(TermDir + '/PRE')
            os.mkdir(TermDir + '/POST')

        try: # some surveys are not accessible to the new CDER account. Remove this except statement once all surveys are transferred to CDER
            if(Class['Pre-Survey ID'] != ''):
                os.chdir(TermDir + '/PRE')
                DownloadResponses(Class['Pre-Survey ID'])
            os.chdir(TermDir + '/POST')
            DownloadResponses(Class['Post-Survey ID'])
            print(Class['ID'])
        except:
            continue

    return 0

def ConcatValidSurveys(FileList, ValidLocation, ValidFileName):
    """Validate and concatenate surveys.

    Keyword arguments:
    FileList -- list of files to read, validate, and concatenate
    ValidLocation -- path to where individual validated surveys should be written
    ValidFileName -- file name of concatenated valid surveys to write
    """

    if not os.path.exists(ValidLocation):
        os.mkdir(ValidLocation)

    dfs = []
    for f in FileList:
        Class_ID = 'R_' + f.split('_')[-2]
        df = pd.read_csv(f, skiprows = [1], dtype = {'Q5a':'object'})
        df['Class_ID'] = Class_ID
        df = Valid_Matched.Validate(df, 'POST') # use strict validation for all surveys, we'll add back some pretests
        df = df.drop_duplicates(subset = ['Q5b', 'Q5c'])
        if('Survey' not in df.columns):
            df['Survey'] = 'C' # if no open-response surveys, set all surveys to C for closed-response

        # during open-response coding, there were some people who used entries other than 0s or 1s, so we need to fix that
        Items = [c for c in df.columns for Q in Questions if Q in c and 'TEXT' not in c and 'l' not in c and '_' in c]
        df[Items] = df[Items].fillna('0').astype(str).apply(lambda x: x.str.replace('^(?!0*$).*$',
                                                                                    '1')).astype(float).replace(0, np.nan)

        df.to_csv(ValidLocation + f.replace('\\', '/').split('/')[-1].split('.')[0] + '_Valid.csv', index = False)
        dfs.append(df)

    df = pd.concat(dfs, axis = 0)
    df.to_csv('Collective_Surveys/' + ValidFileName, index = False)

    return(df)

def ConcatMatchedSurveys(PreFileList, PostFileList, PreMatchedLocation, PostMatchedLocation, PreCollectiveSurveyName,
                         PostCollectiveSurveyName):
    """Filter surveys for matched responses and write to file.

    Keyword arguments:
    PreFileList -- list of raw pretest surveys
    PostFileList -- list of raw posttest surveys
    PreMatchedLocation -- file path to write matched pretest surveys
    PostMatchedLocation -- file path to write matched posttest surveys
    PreCollectiveSurveyName -- file name of concatenated matched pretests to write to
    PostCollectiveSurveyName -- file name of concatenated matched posttests to write to
    """

    if not os.path.exists(PreMatchedLocation):
        os.mkdir(PreMatchedLocation)
    if not os.path.exists(PostMatchedLocation):
        os.mkdir(PostMatchedLocation)

    Predfs = []
    Postdfs = []
    for f_pre in PreFileList:
        for f_post in PostFileList:
            if(f_pre.split('_')[-2] != f_post.split('_')[-2]): # find the post file to match with the pre file
                continue
            print(f_pre)
            Class_ID = 'R_' + f_pre.split('_')[-2] # Split of the underscore at the end for the new format
            try: # if the surveys don't match, we'll pass
                NPre, NPost, dfPre, dfPost = Valid_Matched.ValMat(PRE = pd.read_csv(f_pre, skiprows = [1], dtype = {'Q5a':'object'}),
                                                                  POST = pd.read_csv(f_post, skiprows = [1], dtype = {'Q5a':'object'}))
            except:
                continue
            if('Survey' not in dfPre.columns): # if no open-response surveys, denote all surveys as closed-response
                dfPre['Survey'] = 'C'
            if('Survey' not in dfPost.columns):
                dfPost['Survey'] = 'C'
            dfPre['Class_ID'] = Class_ID
            dfPost['Class_ID'] = Class_ID
            Predfs.append(dfPre)
            Postdfs.append(dfPost)

            dfPre.to_csv(PreMatchedLocation + f_pre.replace('\\', '/').split('/')[-1].split('.')[0] + '_ValMat.csv',
                           index = False)
            dfPost.to_csv(PostMatchedLocation + f_post.replace('\\', '/').split('/')[-1].split('.')[0] + '_ValMat.csv',
                            index = False)

            break

    dfPre_Matched = pd.concat(Predfs, join = 'outer', axis = 0).reset_index(drop = True)
    dfPost_Matched = pd.concat(Postdfs, join = 'outer', axis = 0).reset_index(drop = True)

    dfPre_Matched.to_csv('Collective_Surveys/PRE_Valid_Matched/' + PreCollectiveSurveyName, index = False)
    dfPost_Matched.to_csv('Collective_Surveys/POST_Valid_Matched/' + PostCollectiveSurveyName, index = False)

    return(dfPre_Matched, dfPost_Matched)

def ConsentAtPost(PRE_Valid_File, PRE_Valid_Matched_File):
    """Add consenting students at posttest to the valid pretest file.

    Keyword arguments:
    PRE_Valid_File -- file name of valid pretest file
    PRE_Valid_Matched_File -- file name of corresponding valid matched dataset file
    """

    Valid_df = pd.read_csv(PRE_Valid_File, dtype = {'Q5a':'object'})
    Matched_df = pd.read_csv(PRE_Valid_Matched_File, dtype = {'Q5a':'object'})

    # Add Pre-Surveys from matched set to overall set who provided consent at posttest
    ActualllyValidPre = Matched_df[~Matched_df['V1'].isin(Valid_df['V1'])]
    Total_Valid_df = pd.concat([Valid_df, ActualllyValidPre], join = 'inner', axis = 0)

    Total_Valid_df.to_csv(PRE_Valid_File, index = False)

    return(Total_Valid_df)

def MergeSurveys(PRE_Matched_File, POST_Matched_File, FileName):
    """Merge pre and post matched files together.

    Keyword arguments:
    PRE_Matched_File -- file name of matched pre file
    POST_Matched_File -- file name of matched post file
    FileName -- file name of merged matched file to write to
    """

    PRE_df = pd.read_csv(PRE_Matched_File, dtype = {'Q5a':'object'})
    POST_df = pd.read_csv(POST_Matched_File, dtype = {'Q5a':'object'})

    PRE_df_S = Scoring.CalcScore(PRE_df, Weights)
    POST_df_S = Scoring.CalcScore(POST_df, Weights)

    PRE_df_S = PRE_df_S.rename(columns = {'TotalScores':'PreScores'})
    POST_df_S = POST_df_S.rename(columns = {'TotalScores':'PostScores'})

    PRE_df_S['FullName'] = PRE_df_S['Q5b'].str.lower().str.replace(' ', '') + PRE_df_S['Q5c'].str.lower().str.replace(' ', '')
    POST_df_S['FullName'] = POST_df_S['Q5b'].str.lower().str.replace(' ', '') + POST_df_S['Q5c'].str.lower().str.replace(' ', '')
    POST_df_S['BackName'] = POST_df_S['Q5c'].str.lower().str.replace(' ', '') + POST_df_S['Q5b'].str.lower().str.replace(' ', '')

    # merge on forward and backwards names, and IDs, then drop duplicate matches
    Full_df = pd.merge(left = PRE_df_S, right = POST_df_S, how = 'inner', on = ['Class_ID', 'FullName'])
    Back_df = pd.merge(left = PRE_df_S, right = POST_df_S, how = 'inner', left_on = ['Class_ID', 'FullName'],
                   right_on = ['Class_ID', 'BackName'])
    ID_df = pd.merge(left = PRE_df_S, right = POST_df_S, how = 'inner', on = ['Class_ID',
                                                                              'Q5a']).rename(columns = {'Q5a':'Q5a_x'})
    ID_df['Q5a_y'] = ID_df['Q5a_x'] # create duplicate ID column for merging with names dataframes

    Merged_df = pd.concat([Full_df, Back_df, ID_df], axis = 0,
                          join = 'inner').drop_duplicates().drop(columns = ['BackName']).reset_index(drop = True)

    if('Q4b' in Merged_df.columns): # if there are open-response surveys in one of pre or post, then they'll be in pre
        Merged_df = Merged_df.rename(columns = {'Q1b':'Q1b_x', 'Q1d':'Q1d_x', 'Q1e':'Q1e_x', 'Q2b':'Q2b_x', 'Q2d':'Q2d_x',
                                                'Q2e':'Q2e_x', 'Q3b':'Q3b_x', 'Q3d':'Q3d_x', 'Q3e':'Q3e_x', 'Q4b':'Q4b_x'})

    Merged_df.to_csv('Collective_Surveys/Merged/' + FileName, index = False)

    return(Merged_df)

def MergePlusMissing(MergedFile, ValidPRE_File, ValidPOST_File, CompleteFileName):
    """Add students that only took one survey to merged file.

    Keyword arguments:
    MergedFile -- file name of merged dataset
    ValidPRE_File -- file name of all valid pretest surveys corresponding to merged dataset
    ValidPOST_File -- file name of all valid posttest surveys corresponding to merged dataset
    CompleteFileName -- file name of merged dataset with additional one survey students to write to
    """

    Merged_df = pd.read_csv('Collective_Surveys/Merged/' + MergedFile)

    PRE_df = pd.read_csv('Collective_Surveys/PRE_Valid/' + ValidPRE_File)
    POST_df = pd.read_csv('Collective_Surveys/POST_Valid/' + ValidPOST_File)

    PRE_df_S = Scoring.CalcScore(PRE_df, Weights).rename(columns = {'TotalScores':'PreScores'})
    POST_df_S = Scoring.CalcScore(POST_df, Weights).rename(columns = {'TotalScores':'PostScores'})

    Unmatched_PRE = PRE_df_S[~PRE_df_S['V1'].isin(Merged_df['V1_x'])]
    Unmatched_POST = POST_df_S[~POST_df_S['V1'].isin(Merged_df['V1_y'])]

    Unmatched_PRE.columns = [c + '_x' if c != 'Class_ID' and c != 'PreScores' else c for c in Unmatched_PRE.columns]
    Unmatched_POST.columns = [c + '_y' if c != 'Class_ID' and c != 'PostScores' else c for c in Unmatched_POST.columns]

    Complete_df = pd.concat([Merged_df, Unmatched_PRE, Unmatched_POST], axis = 0, join = 'outer')
    Complete_df = Complete_df[Merged_df.columns]
    Complete_df.to_csv('Collective_Surveys/Complete/' + CompleteFileName, index = False)

    return(Complete_df)

def ConcatSurveys(Semester, Year):
    """Concatenate a set of raw surveys.

    Keyword arguments:
    Semester -- which semester to concatenate surveys for
    Year -- which year to concatenate surveys for
    """

    PreFiles = glob(MainSurveys_Folder + Semester + Year + '/PRE/*.csv')
    PostFiles = glob(MainSurveys_Folder + Semester + Year + '/POST/*.csv')

    PREValid = ConcatValidSurveys(PreFiles, MainSurveys_Folder + Semester + Year + '/PRE/Valid/',
                                  'PRE_Valid/' + Semester + Year + '_PRE_Valid.csv')
    POSTValid = ConcatValidSurveys(PostFiles, MainSurveys_Folder + Semester + Year + '/POST/Valid/',
                                   'POST_Valid/' + Semester + Year + '_POST_Valid.csv')

    PREValMat, POSTValMat = ConcatMatchedSurveys(PreFiles, PostFiles,
                                                 MainSurveys_Folder + Semester + Year + '/PRE/Valid/Matched/',
                                                 MainSurveys_Folder + Semester + Year + '/POST/Valid/Matched/',
                                                 Semester + Year + '_PRE_ValMat.csv',
                                                 Semester + Year + '_POST_ValMat.csv')

    PREValid = ConsentAtPost('Collective_Surveys/PRE_Valid/' + Semester + Year + '_PRE_Valid.csv',
                             'Collective_Surveys/PRE_Valid_Matched/' + Semester + Year + '_PRE_ValMat.csv')

    return(PREValMat, POSTValMat)

def CompleteConcat(FolderName):
    """Concatenate a set of surveys already concatenated at semester and year level.

    Keyword arguments:
    FolderName -- path to folder containing surveys concatenated at semester and year level
    """

    Files = [f for f in glob('Collective_Surveys/' + FolderName + '/*') if 'Concat' not in f]

    dfs = [pd.read_csv(f) for f in Files]
    df = pd.concat(dfs, join = 'outer', axis = 0)
    df.to_csv('Collective_Surveys/' + FolderName + '/' + FolderName + '_Concat.csv', index = False)

    return(df)

def AddCourseInfo(Students_FILE, Courses_FILE):
    """Merge course information with student response dataset.

    Keyword arguments:
    Students_FILE -- file name of dataset of students' responses (with Class_ID)
    Courses_FILE -- file name of course information survey
    """

    df_students = pd.read_csv(Students_FILE)
    df_courses = pd.read_csv(Courses_FILE, skiprows = [1])

    df_courses['Q6'] = df_courses['Q6'].str.extract('(\d+)').fillna('').astype(str).squeeze()
    df_courses['anon_course_id'] = (df_courses['Q6'] + df_courses['Q4'].apply(str)).astype('category').cat.codes
    df_courses['anon_institution_id'] = df_courses['Q4'].astype('category').cat.codes

    df_courses = df_courses.rename(columns = {'Q7':'Lab_level', 'Q4':'Institution', 'Q19':'Institution_type', 'Q27':'Lab_purpose'})
    df_courses['Lab_level'] = df_courses['Lab_level'].map({1:'Intro-Algebra', 2:'Intro-Calculus', 3:'Sophomore', 4:'Junior', 5:'Senior', 6:'HighSchool',
                                                            7:'Graduate'})
    df_courses['Institution_type'] = df_courses['Institution_type'].map({1:'2 year college', 2:'4 year college', 3:'Masters granting institution',
                                                                            4:'PhD granting institution', 5:'HighSchool'})
    df_courses['Lab_purpose'] = df_courses['Lab_purpose'].map({1:'Reinforce concepts', 2:'Develop lab skills', 3:'Both about equally'})

    df = df_students.merge(df_courses, left_on = 'Class_ID', right_on = 'V1', how = 'left').drop_duplicates(subset = ['V1_x', 'V1_y'])

    df['anon_student_id'] = (df['Q5b_y'].fillna(df['Q5b_x']).apply(str).str.lower() +
                                df['Q5c_y'].fillna(df['Q5c_x']).apply(str).str.lower()).str.replace('\W', '')
    df['anon_student_id'] = (df['anon_student_id'] + '-' + df['anon_institution_id'].astype(str)).astype('category').cat.codes

    df.to_csv('./Collective_Surveys/Complete/Complete_Concat_CourseInfo.csv', index = False)

    return(df)

def Identify(file, header_file, file_out, Class_ID = None):
    """Create identifiable data file to be sent to instructor or uploaded to PLIC dashboard.

    Keyword arguments:
    file -- master csv file containing matched students' pre and posttest scores
    header_file -- csv file containing header information
    file_out -- name of outputted csv file
    Class_ID -- Class_ID of specific class that idenntifiable data is requested for; if retrieving data for dashboard, set as None
    """

    Questions = ['Q1B', 'Q1D', 'Q1E', 'Q2B', 'Q2D', 'Q2E', 'Q3B', 'Q3D', 'Q3E', 'Q4B']

    df = pd.read_csv(file)
    if(Class_ID is not None):
        df = df.loc[df['Class_ID'] == Class_ID, :]

    dfOther = pd.read_csv(file)
    dfOther_Pre = dfOther.loc[dfOther['Survey_x'] == 'C', [col + 's_x' for col in Questions]]
    dfOther_Post = dfOther.loc[dfOther['Survey_y'] == 'C', [col + 's_y' for col in Questions]]
    dfOther_Pre.columns = dfOther_Pre.columns.str.replace(r's_x$', 's')
    dfOther_Post.columns = dfOther_Post.columns.str.replace(r's_y$', 's')
    dfOther = pd.concat([dfOther_Pre, dfOther_Post], axis = 0, join = 'inner').reset_index(drop = True)

    df_Pre = df.loc[df['Survey_x'] == 'C', [col + 's_x' for col in Questions]].reset_index()
    df_Post = df.loc[df['Survey_y'] == 'C', [col + 's_y' for col in Questions]].reset_index()
    df_Pre.columns = df_Pre.columns.str.replace(r's_x$', 's')
    df_Post.columns = df_Post.columns.str.replace(r's_y$', 's')
    pre_scores = Scoring.CalcFactorScores(dfOther, df_Pre).rename(columns = {'models':'models_PRE', 'methods':'methods_PRE', 'actions':'actions_PRE'}).set_index(pd.Index(df_Pre['index']))
    post_scores = Scoring.CalcFactorScores(dfOther, df_Post).rename(columns = {'models':'models_POST', 'methods':'methods_POST', 'actions':'actions_POST'}).set_index(pd.Index(df_Post['index']))
    df = pd.concat([df, pre_scores, post_scores], axis = 1, join = 'outer')

    df['ID'] = df['Q5a_y'].fillna(df['Q5a_x'])
    df['LastName'] = df['Q5b_y'].fillna(df['Q5b_x'])
    df['FirstName'] = df['Q5c_y'].fillna(df['Q5c_x'])

    df = SetGender(df)
    df = SetURM(df)
    df = SetMajor(df)
    df = SetClassStanding(df)

    df.columns = df.columns.str.replace(r's_x$', '_PRE')
    df.columns = df.columns.str.replace(r's_y$', '_POST')
    if(Class_ID is None):
        df.columns = df.columns.str.replace(r'_x$', '_PRE')
        df.columns = df.columns.str.replace(r'_y$', '_POST')
    df = df.rename(columns = {'PreScores':'TotalScores_PRE', 'PostScores':'TotalScores_POST'})

    if(Class_ID is not None):
        df = df.drop(columns = ['Gender', 'Major', 'URM_Status', 'Class_Standing'])
        df.headers = pd.read_csv(header_file)
        df = pd.concat([df.headers, df], join = 'inner')
    df.to_csv(file_out, index = False)
    return df

def Deidentify(file_id, file_out):
    # legacy; remove in future version since we can provide identifiable data now
    def CrossTab(df):
        df_tab = df.loc[:, ['Class_ID', 'Gender', 'URM_Status', 'Major', 'Class_Standing']]

        tab = pd.crosstab(df_tab['Class_ID'], [df_tab['Gender'], df_tab['URM_Status'], df_tab['Major'], df_tab['Class_Standing']])
        tab['Class_Standing_Available'] = [False if 1 in row else True for row in tab.values.tolist()]
        tab['Major_Available'] = [False if 1 in row else True for row in tab.values.tolist()]
        tab['URM_Available'] = [False if 1 in row else True for row in tab.values.tolist()]
        tab['Gender_Available'] = [False if 1 in row else True for row in tab.values.tolist()]

        for ID, Row in tab.iterrows():
            if((Row['Class_Standing_Available'] * Row['Major_Available'] * Row['URM_Available'] *
                Row['Gender_Available']).values[0]):
                continue
            if(not Row['Class_Standing_Available'].values[0]):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['Gender'], [df_class['URM_Status'], df_class['Major']])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['Major_Available', 'URM_Available', 'Gender_Available']] = True
                    continue
            if(not Row['Major_Available'].values[0]):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['Gender'], [df_class['URM_Status'], df_class['Class_Standing']])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['Class_Standing_Available', 'URM_Available', 'Gender_Available']] = True
                    continue
            if(not Row['URM_Available'].values[0]):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['Gender'], [df_class['Major'], df_class['Class_Standing']])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['Class_Standing_Available', 'Major_Available', 'Gender_Available']] = True
                    continue
            elif(not Row['Gender_Available'].values[0]):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['URM_Status'], [df_class['Major_Status'], df_class['Class_Standing']])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['Class_Standing_Available', 'Major_Available', 'URM_Available']] = True
                    continue
            if((not Row['Class_Standing_Available'].values[0]) * (not Row['Major_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['Gender'], df_class['URM_Status'])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['URM_Available', 'Gender_Available']] = True
                    continue
            if((not Row['Class_Standing_Available'].values[0]) * (not Row['URM_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['Gender'], df_class['Major'])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['Major_Available', 'Gender_Available']] = True
                    continue
            elif((not Row['Class_Standing_Available'].values[0]) * (not Row['Gender_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['URM_Status'], df_class['Major'])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['Major_Available', 'URM_Available']] = True
                    continue
            if((not Row['Major_Available'].values[0]) * (not Row['URM_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['Gender'], df_class['Class_Standing'])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['Class_Standing_Available', 'Gender_Available']] = True
                    continue
            if((not Row['Major_Available'].values[0]) * (not Row['Gender_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['URM_Status'], df_class['Class_Standing'])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['Class_Standing_Available', 'URM_Available']] = True
                    continue
            if((not Row['URM_Available'].values[0]) * (not Row['Gender_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                tab_class = pd.crosstab(df_class['Major'], df_class['Class_Standing'])
                if(1 not in tab_class.values):
                    tab.loc[ID, ['Class_Standing_Available', 'Major_Available']] = True
                    continue
            if((not Row['Class_Standing_Available'].values[0]) * (not Row['Major_Available'].values[0]) *
                 (not Row['URM_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                if(1 not in df_class['Gender'].value_counts().values):
                    tab.loc[ID, 'Gender_Available'] = True
                    continue
            if((not Row['Class_Standing_Available'].values[0]) * (not Row['Major_Available'].values[0]) *
                 (not Row['Gender_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                if(1 not in df_class['URM_Status'].value_counts().values):
                    tab.loc[ID, 'URM_Available'] = True
                    continue
            if((not Row['Class_Standing_Available'].values[0]) * (not Row['URM_Available'].values[0]) *
                 (not Row['Gender_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                if(1 not in df_class['Major'].value_counts().values):
                    tab.loc[ID, 'Major_Available'] = True
                    continue
            if((not Row['Major_Available'].values[0]) * (not Row['URM_Available'].values[0]) *
                 (not Row['Gender_Available'].values[0])):
                df_class = df_tab.loc[df['Class_ID'] == ID, :]
                if(1 not in df_class['Class_Standing'].value_counts().values):
                    tab.loc[ID, 'Class_Standing_Available'] = True
                    continue

        tab = tab[['Class_Standing_Available', 'Major_Available', 'URM_Available', 'Gender_Available']].reset_index()
        tab.columns = tab.columns.droplevel(level = [1, 2,3])
        df_out = df.merge(tab, how = 'left', on = 'Class_ID')
        return(df_out)

    def CountValues(df):

        df_Tab = pd.crosstab(df['Class_ID'], df['Gender'])
        df_Tab['Gender_Available'] = [False if 1 in v else True for v in df_Tab.values.tolist()]

        df_Tab_dummy = pd.crosstab(df['Class_ID'], df['URM_Status'])
        df_Tab_dummy['URM_Available'] = [False if 1 in v else True for v in df_Tab_dummy.values.tolist()]
        df_Tab = df_Tab.merge(df_Tab_dummy, how = 'left', on = 'Class_ID')

        df_Tab_dummy = pd.crosstab(df['Class_ID'], df['Major'])
        df_Tab_dummy['Major_Available'] = [False if 1 in v else True for v in df_Tab_dummy.values.tolist()]
        df_Tab = df_Tab.merge(df_Tab_dummy, how = 'left', on = 'Class_ID')

        df_Tab_dummy = pd.crosstab(df['Class_ID'], df['Class_Standing'])
        df_Tab_dummy['Class_Standing_Available'] = [False if 1 in v else True for v in df_Tab_dummy.values.tolist()]
        df_Tab = df_Tab.merge(df_Tab_dummy, how = 'left', on = 'Class_ID')

        df_Tab = df_Tab[['Gender_Available', 'URM_Available', 'Major_Available', 'Class_Standing_Available']].reset_index()
        return df_Tab

    df = pd.read_csv(file_id)

    df = SetMajor(df)
    df = SetGender(df)
    df = SetURM(df)
    df = SetClassStanding(df)

    df['Matched'] = df[['Survey_x', 'Survey_y']].transform(lambda x: pd.notnull(x['Survey_x']) * pd.notnull(x['Survey_y']), axis = 1)
    df['N_Matched'] = df.groupby('Class_ID')['Matched'].transform(np.sum)

    df['PreOnly'] = df[['Survey_x', 'Survey_y']].transform(lambda x: pd.notnull(x['Survey_x']) * pd.isnull(x['Survey_y']), axis = 1)
    df['N_PreOnly'] = df.groupby('Class_ID')['PreOnly'].transform(np.sum)

    df['PostOnly'] = df[['Survey_x', 'Survey_y']].transform(lambda x: pd.isnull(x['Survey_x']) * pd.notnull(x['Survey_y']), axis = 1)
    df['N_PostOnly'] = df.groupby('Class_ID')['PostOnly'].transform(np.sum)

    df['Download_Available'] = df[['N_PreOnly', 'N_PostOnly', 'N_Matched']].transform(lambda x: (x['N_PreOnly'] != 1) *
                                                                                      (x['N_PostOnly'] != 1) *
                                                                                      (x['N_Matched'] != 1), axis = 1)

    df['Matched_Available'] = df['N_Matched'] > 1
    df['Valid_Available'] = (df['N_PreOnly'] + df['N_Matched'] != 1) & (df['N_PostOnly'] + df['N_Matched'] != 1)
    df = df.drop(columns = ['PreOnly', 'PostOnly', 'Matched', 'N_PreOnly', 'N_PostOnly', 'N_Matched'])

    df_preOnly = df.loc[pd.notnull(df['Survey_x']) & pd.isnull(df['Survey_y']), :]
    df_postOnly = df.loc[pd.isnull(df['Survey_x']) & pd.notnull(df['Survey_y']), :]
    df_matchOnly = df.loc[pd.notnull(df['Survey_x']) & pd.notnull(df['Survey_y']), :]

    assert(len(df_preOnly) + len(df_postOnly) + len(df_matchOnly) == len(df))

    df_preOnlyTab = CrossTab(df_preOnly)
    df_postOnlyTab = CrossTab(df_postOnly)
    df_matchTab = CrossTab(df_matchOnly)
    df_Tab = pd.concat([df_preOnlyTab, df_postOnlyTab, df_matchTab], axis = 0, join = 'outer').reset_index(drop = True)

    df_Tab['Gender_Available_Download'] = (df_Tab.groupby('Class_ID')['Gender_Available'].transform('nunique') == 1) & \
    (df_Tab['Gender_Available'] == True)
    df_Tab['URM_Available_Download'] = (df_Tab.groupby('Class_ID')['URM_Available'].transform('nunique') == 1) & \
    (df_Tab['URM_Available'] == True)
    df_Tab['Major_Available_Download'] = (df_Tab.groupby('Class_ID')['Major_Available'].transform('nunique') == 1) & \
    (df_Tab['Major_Available'] == True)
    df_Tab['Class_Standing_Available_Download'] = (df_Tab.groupby('Class_ID')['Class_Standing_Available'].transform('nunique') == 1) & \
    (df_Tab['Class_Standing_Available'] == True)

    df_Tab = df_Tab.drop(columns = ['Gender_Available', 'URM_Available', 'Major_Available', 'Class_Standing_Available'])

    df_pre = df_Tab.loc[pd.notnull(df_Tab['Survey_x']), :]
    df_Final = df_Tab.merge(CountValues(df_pre), how ='left',
                            on = 'Class_ID').rename(columns = {'Gender_Available':'Gender_Available_Pre',
                                                               'URM_Available':'URM_Available_Pre',
                                                               'Major_Available':'Major_Available_Pre',
                                                               'Class_Standing_Available':'Class_Standing_Available_Pre'})

    df_post = df_Tab.loc[pd.notnull(df_Tab['Survey_y']), :]
    df_Final = df_Final.merge(CountValues(df_post), how ='left',
                            on = 'Class_ID').rename(columns = {'Gender_Available':'Gender_Available_Post',
                                                               'URM_Available':'URM_Available_Post',
                                                               'Major_Available':'Major_Available_Post',
                                                               'Class_Standing_Available':'Class_Standing_Available_Post'})

    df_Final = df_Final.merge(CountValues(df_matchOnly), how ='left',
                            on = 'Class_ID').rename(columns = {'Gender_Available':'Gender_Available_Match',
                                                               'URM_Available':'URM_Available_Match',
                                                               'Major_Available':'Major_Available_Match',
                                                               'Class_Standing_Available':'Class_Standing_Available_Match'})

    df_Final['Gender_Available_Valid'] = df_Final['Gender_Available_Pre'].fillna(True) & df_Final['Gender_Available_Post'].fillna(True)
    df_Final['URM_Available_Valid'] = df_Final['URM_Available_Pre'].fillna(True) & df_Final['URM_Available_Post'].fillna(True)
    df_Final['Major_Available_Valid'] = df_Final['Major_Available_Pre'].fillna(True) & df_Final['Major_Available_Post'].fillna(True)
    df_Final['Class_Standing_Available_Valid'] = df_Final['Class_Standing_Available_Pre'].fillna(True) & df_Final['Class_Standing_Available_Post'].fillna(True)
    df_Final = df_Final.drop(columns = ['Gender_Available_Pre', 'Gender_Available_Post', 'URM_Available_Pre', 'URM_Available_Post',
                                        'Major_Available_Pre', 'Major_Available_Post', 'Class_Standing_Available_Pre',
                                        'Class_Standing_Available_Post'])

    df_Final.to_csv(file_out, index = False)

def SetMajor(df):
    df['Q6b'] = df['Q6b_y'].fillna(df['Q6b_x'])
    df['Q6b.i'] = df['Q6b.i_y'].fillna(df['Q6b.i_x'])

    conditions = [
        df['Q6b'] < 4,
        df['Q6b.i'] < 5
    ]

    output = [
        'Physics', 'Non-physics'
    ]

    df['Major'] = np.select(conditions, output, None)
    return df

def SetGender(df):
    conditions = [
        df['Q6e_1_y'] == 1,
        df['Q6e_2_y'] == 1,
        df['Q6e_1_x'] == 1,
        df['Q6e_2_x'] == 1
    ]

    output = [
        'Male', 'Female'
    ]

    df['Gender'] = np.select(conditions, np.tile(output, 2), None)
    return df

def SetURM(df):
    conditions = [
        df['Q6f_5_y'] == 1,
        df['Q6f_1_y'] == 1,
        df['Q6f_7_y'] == 1,
        df['Q6f_3_y'] == 1,
        df['Q6f_4_y'] == 1,
        df['Q6f_2_y'] == 1,
        df['Q6f_6_y'] == 1,
        df['Q6f_5_x'] == 1,
        df['Q6f_1_x'] == 1,
        df['Q6f_7_x'] == 1,
        df['Q6f_3_x'] == 1,
        df['Q6f_4_x'] == 1,
        df['Q6f_2_x'] == 1,
        df['Q6f_6_x'] == 1,
    ]

    output = ['URM'] * 5 + ['Majority'] * 2

    df['URM_Status'] = np.select(conditions, np.tile(output, 2), None)
    return df

def SetClassStanding(df):
    conditions = [
        df['Q6a_y'] == 1,
        df['Q6a_y'] > 1,
        df['Q6a_x'] == 1,
        df['Q6a_x'] > 1,
    ]

    output = ['Freshman', 'Beyond-first-year']

    df['Class_Standing'] = np.select(conditions, np.tile(output, 2), None)
    return df
