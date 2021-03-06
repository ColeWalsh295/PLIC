# -*- coding: utf-8 -*-
#!c:/Python/python3_6.exe -u

import numpy as np
import pandas as pd
from urllib.request import Request, urlopen
import time
import requests
import zipfile
import json
import io
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import ReportGen
import os
import sys

# Setting user Parameters
global apiToken, MainFolder, DataCenter, baseURL, ChangeURL, CIS_SurveyID, ChangeDates_SurveyID, CPERLEmail, UserEmail, EmailPassword
admin_info = pd.read_csv('Admin_Info.csv', index_col = False, header = 0).T[0] # get sensitive admininstration info
apiToken = admin_info['API'] # change token for different Qualtrics account
SharedCole = admin_info['SharedCole']
SharedUsers = [SharedCole] # Users to share surveys with in Qualtrics from main account
MainFolder = 'C:/Users/Cole/Documents/GRA_Summer2019/Automation-Files_TestPLIC_Aug2019/'
DataCenter = 'cornell'
baseURL = "https://{0}.qualtrics.com/API/v3/responseexports/".format(DataCenter)
ChangeURL = "https://{0}.qualtrics.com/jfe/form/SV_9QDl20NjVC3w0uN".format(DataCenter)

CIS_SurveyID = "SV_5ouHoTGEF5FBqxD" # Course information survey survey ID
ChangeDates_SurveyID = "SV_9QDl20NjVC3w0uN" # Change date survey ID

CPERLEmail = 'cperl@cornell.edu' # Shared CPERL email address
UserEmail = 'as-phy-edresearchlab@cornell.edu' # dummy email used to access mail client
EmailPassword = admin_info['EmailPassword']

def main():
    Master_df = pd.read_csv('MasterCourseData.csv') # Read in local master data file with dates information

    CIS_Survey_Name = DownloadResponses(CIS_SurveyID) # Course Information Survey downloaded as Course_Information_Survey.csv (or whatever name is used in qualtrics)
    CIS_df = pd.read_csv(CIS_Survey_Name + '.csv', skiprows = [1, 2])

    # Get new entries by instructors who completed the CIS online and provided a post-survey end date (that's Q11_v2)
    CIS_df = CIS_df.loc[~(CIS_df['ResponseID'].isin(Master_df['ID'])) & (CIS_df['Finished'] == 1) & pd.notnull(CIS_df['Q11_v2']), :]
    CIS_df = CleanNewData(CIS_df) # these weird codes are difficult to work with so change them to more readable names

    if not CIS_df.empty:
        CIS_df['Post-Survey ID'] = CIS_df.apply(MakeSurvey, axis = 1, args = ('POST',))
        CIS_df['Mid-Survey ID'] = CIS_df.apply(lambda row: MakeSurvey(row, 'MID') if row['Mid-Survey Close Date'] != '' else '', axis = 1)
        CIS_df['Pre-Survey ID'] = CIS_df.apply(lambda row: MakeSurvey(row, 'PRE') if row['Pre-Survey Close Date'] != '' else '', axis = 1)
        CIS_df['Survey Creation Date'] = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())
        for User in SharedUsers:
            CIS_df['Post-Survey ID'].apply(ShareSurvey, args = (User,))
            CIS_df['Mid-Survey ID'].apply(lambda x: ShareSurvey(x['Mid-Survey ID'], User) if x['Mid-Survey ID'] != '' else -1)
            CIS_df['Pre-Survey ID'].apply(lambda x: ShareSurvey(x['Pre-Survey ID'], User) if x['Pre-Survey ID'] != '' else -1)
        Pre_df = CIS_df.loc[CIS_df['Pre-Survey ID'] != '', :]
        if not Pre_df.empty:
            Pre_df['Pre-Survey ID'].apply(ActivateSurvey)
            Pre_df.apply(SendPreSurvey, axis = 1)
            Pre_df['Pre-Survey Sent'] =  time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())
            CIS_df.update(Pre_df)

        Master_df = pd.concat([Master_df, CIS_df], axis = 0, join = 'outer').reset_index(drop = True).loc[:, Master_df.columns] # Concatenate old and new data...
        Master_df.to_csv('MasterCourseData.csv', index = False) #...and write it back to the master file

    ChangeDatesFile = DownloadResponses(ChangeDates_SurveyID)
    Changes_df = pd.read_csv(ChangeDatesFile + '.csv', skiprows = [1, 2]).rename(columns = {'Q1':'InstructorID'})
    MasterChanges_df = pd.read_csv('ChangeLog.csv')
    Changes_df = Changes_df[(~Changes_df['ResponseID'].isin(MasterChanges_df['ResponseID'])) & (Changes_df['Finished'] == 1)] # Get new changes to implement
    Changes_df = Master_df.merge(Changes_df.set_index('InstructorID'), left_on = 'ID', right_index = True, how = 'inner')

    if not Changes_df.empty:
        # Fix dates as necessary
        Changes_df = Changes_df.apply(ChangeDates, axis = 1, args = ('Pre',))
        Changes_df = Changes_df.apply(ChangeDates, axis = 1, args = ('Mid',))
        Changes_df = Changes_df.apply(ChangeDates, axis = 1, args = ('Post',))
        Changes_df.apply(ChangesEmailSend, axis = 1)

        Changes_df['Time Updated'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
        MasterChanges_df = pd.concat([MasterChanges_df, Changes_df], axis = 0, join = 'outer').loc[:, MasterChanges_df.columns]
        MasterChanges_df.to_csv('ChangeLog.csv', index = False)
        Master_df.update(Changes_df)
        Master_df = Master_df.replace('nan', np.nan)
        Master_df.to_csv('MasterCourseData.csv', index = False) #...and write it back to the master file

    Master_df = SurveyAdministration(Master_df, 'Pre') # Check survey reminders and close dates for PRE-survey
    Master_df = SurveyAdministration(Master_df, 'Mid') # Check survey reminders and close dates for MID-survey
    Master_df = SurveyAdministration(Master_df, 'Post') # Check survey reminders and close dates for POST-survey

    Report_df = Master_df.loc[(pd.isnull(Master_df['Report Sent'])) & (pd.notnull(Master_df['Post-Survey Closed']))] # Get classes that are ready to receive reports
    Report_df.apply(PrepareReport, axis = 1)
    Report_df['Report Sent'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
    Master_df.update(Report_df) # Update master file with sent reports...
    os.chdir(MainFolder)
    Master_df.to_csv('MasterCourseData.csv', index = False) #...and write it back to the master file

def CleanNewData(df):
    # change names of columns in dataframe of course information survey responses so that tehy're more readable
    df = df.rename(columns = {'ResponseID':'ID', 'Q1':'First Name', 'Q2':'Last Name', 'Q3':'Email', 'Q4':'School', 'Q5':'Course Name', 'Q6':'Course Number',
                                'Q8':'Number Of Students'})

    # Use Regex to replace any non-alphanumeric characters with underscores...cause instructors fill forms with weird stuff
    df[['First Name', 'Last Name', 'School', 'Course Name', 'Course Number']] = df[['First Name', 'Last Name', 'School', 'Course Name',
        'Course Number']].apply(lambda x: x.str.replace('[^0-9a-zA-Z]+', '_'))

    # Check and fix (if necessary) dates indicated
    df['Pre-Survey Close Date'] = CheckDates(df['Q10_v2'], 'PRE').apply(lambda x: x.strftime("%d-%b-%Y") if not pd.isnull(x) else '')
    df['Mid-Survey Close Date'] = CheckDates(df['Q41_v2'], 'MID').apply(lambda x: x.strftime("%d-%b-%Y") if not pd.isnull(x) else '')
    df['Post-Survey Close Date'] = CheckDates(df['Q11_v2'], 'POST')
    df['Course Year'] = df['Post-Survey Close Date'].dt.strftime('%Y')
    df['Post-Survey Close Date'] = df['Post-Survey Close Date'].apply(lambda x: x.strftime("%d-%b-%Y"))

    df['Credit Offered'] = df['Q12'] == 1
    df['Number of Surveys'] = df['Q45'].fillna(df['Q40'].fillna(0) + 1)
    df['Course Type'] = df['Q7'].astype(int).map({1:'Intro - Algebra', 2:'Intro - Calculus', 3:'Sophomore', 4:'Junior', 5:'Senior'})
    df['Season'] = df['Q9a'].astype(int).fillna(df['Q9b'].fillna(0).astype(int).map({2:6, 3:2, 4:3, 5:4})).map({1:'Fall', 2:'Spring', 3:'Summer', 4:'Year', 6:'Winter'}) # Map season to strings using quarter data to fill in semester data

    return df

def CheckDates(Series, Survey):
    # provide end dates for relevant surveys
    Delta = 14 if Survey == 'PRE' else 45 if Survey == 'MID' else 90
    try:
        Series_dt = pd.to_datetime(Series)
        Series_dt[Series_dt < datetime.datetime.now()] = datetime.datetime.now() + datetime.timedelta(days = Delta) # fix dates that are in the past
    except:
        Pattern = '^(0[1-9]|1[012])[\-](0[1-9]|[12][0-9]|3[01])[\-]\d{4}$' # Valid Datetime pattern

        # re-run function and set datetimes that don't match the valid pattern to a preset date
        Series[~Series.str.match(Pattern)] = (datetime.datetime.now() + datetime.timedelta(days = Delta)).strftime('%m-%d-%Y')
        CheckDates(Series, Survey)

    return Series_dt

def SurveyAdministration(df, Survey):
    Master_df = df.copy()
    Survey_df = df.loc[(pd.notnull(df[Survey + '-Survey ID'])) & (pd.isnull(Master_df[Survey + '-Survey Closed'])), :]
    CurrentTime = datetime.datetime.now()
    Survey_df['Close Date'] = pd.to_datetime(Survey_df[Survey + '-Survey Close Date'])

    if Survey != 'Pre':
        Survey_Memo_df = Survey_df.loc[(pd.isnull(Survey_df[Survey + '-Survey Sent'])) & (pd.isnull(Survey_df[Survey + '-Survey Memo'])) & (CurrentTime >= Survey_df['Close Date'] - datetime.timedelta(days = 16)), :] # Get only the classes that should now receive a momo
        if not Survey_Memo_df.empty:
            if Survey != 'Pre':
                Survey_Memo_df.apply(SendSurveyMemo, axis = 1, args = (Survey,)) # Send out appropriate memos alerting instructors to surveys that will be activated soon
                Survey_Memo_df[Survey + '-Survey Memo'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                Master_df.update(Survey_Memo_df) # Update master file with sent memos...
                Master_df.to_csv('MasterCourseData.csv', index = False)

    # Get only the classes that should now get their survey
    Survey_Send_df = Survey_df.loc[(CurrentTime >= Survey_df['Close Date'] - datetime.timedelta(days = 14)) & (pd.isnull(Survey_df[Survey + '-Survey Sent'])), :]
    if not Survey_Send_df.empty:
        Survey_Send_df.apply(ActivateSurvey)
        if Survey == 'Pre':
            Survey_Send_df.apply(SendPreSurvey, axis = 1)
        else:
            Survey_Send_df.apply(SendSurvey, axis = 1, args = (Survey,))
        Survey_Send_df[Survey + '-Survey Sent'] = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())
        Master_df.update(Survey_Send_df) # Update the master file with emailed survey times...
        Master_df.to_csv('MasterCourseData.csv', index = False)

    Survey_Reminder_df = Survey_df.loc[(CurrentTime >= (Survey_df['Close Date'] - datetime.timedelta(days = 4))) & (pd.isnull(Survey_df[Survey + '-Survey Reminder'])), :]
    if not Survey_Reminder_df.empty:
        Survey_Reminder_df['N_Students'] = Survey_Reminder_df.apply(GetNumberStudents, axis = 1, args = (Survey,))
        os.chdir(MainFolder)
        Survey_Reminder_df.apply(lambda row: ZeroResponseEmail(row, Survey) if row['N_Students'] == 0 else ReminderEmailSend(row, Survey), axis = 1)
        # Move back the close date if no one has responded yet
        Survey_Reminder_df['Close Date'] = Survey_Reminder_df.apply(lambda x: x['Close Date'] + datetime.timedelta(days = 3) if x['N_Students'] == 0 else x['Close Date'], axis = 1)
        Survey_Reminder_df[Survey + '-Survey Close Date'] = Survey_Reminder_df['Close Date'].dt.strftime('%d-%b-%Y')
        Survey_Reminder_df[Survey + '-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())
        Master_df.update(Survey_Reminder_df) # Update the master file with emailed survey reminder times...
        Master_df.to_csv('MasterCourseData.csv', index = False)

    Survey_Close_df = Survey_df.loc[CurrentTime >= Survey_df['Close Date'] + datetime.timedelta(hours = 23, minutes = 59, seconds = 59), :]
    if not Survey_Close_df.empty:
        Survey_Close_df[Survey + '-Survey ID'].apply(lambda x: ActivateSurvey(x, Active = False))
        Survey_Close_df['N_Students'] = Survey_Close_df.apply(GetNumberStudents, axis = 1, args = (Survey,))
        os.chdir(MainFolder)
        if Survey != 'Post':
            Survey_Close_df.apply(SendSurveyClose, axis = 1, args = (Survey,))
        Survey_Close_df[Survey + '-Survey Closed'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
        Master_df.update(Survey_Close_df) # Update the master file with survey close times...
        Master_df.to_csv('MasterCourseData.csv', index = False)

    return Master_df

def ChangeDates(Row, Survey):
    Dates = {'Pre':'Q2_v2', 'Mid':'Q9_v2', 'Post':'Q3_v2'}
    Reminders = {'Pre':'Q4', 'Mid':'Q8', 'Post':'Q5'}
    if(pd.notna(Row[Survey + '-Survey ID']) & pd.isna(Row[Survey + '-Survey Closed']) & pd.notna(Row[Dates[Survey]])):
        print(Survey)
        try:
            Row[Survey + '-Survey New Close Date'] = datetime.datetime.strptime(Row[Dates[Survey]], "%m-%d-%Y").strftime("%d-%b-%Y")
        except ValueError: # If an incorrectly formatted date is provided, ignore and move on
            return -1

        # Reset reminder email statuses if requested
        if(Row[Reminders[Survey]] == 1):
            Row[Survey + '-Survey Reminder Email'] = 1
            Row[Survey + '-Survey Reminder'] = 'nan'
        elif(Row[Reminders[Survey]] == 2 and pd.isna(Row[Survey + '-Survey Reminder'])):
            Row[Survey + '-Survey Reminder Email'] = 2
            Row[Survey + '-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

    return Row

def PrepareReport(Row, ErrorEmail = False):
    Path = MainFolder + Row['Season'] + str(int(Row['Course Year'])) + "Files/" + Row['School'] + '_' + str(Row['Course Number']) + '_' + Row['Last Name'] + '_' + Row['ID']
    os.chdir(Path)
    PostSurveyName = DownloadResponses(Row['Post-Survey ID'])
    print(Row['First Name'])

    if(Post_df.empty):
        ErrorEmail = True
        return -1
    PostNames_df = GetNamesdf(Post_df, 'Post')
    PDFName = Path + "/" + Row['Season'] + str(int(Row['Course Year'])) + '_' + Row['School'] + '_' + str(Row['Course Number']) + '_' + Row['Last Name'] + '_Report'
    print(PDFName)
    if(Row['Number of Surveys'] >= 2): # If there are at least 2 surveys, download the PRE-survey data
        PreSurveyName = DownloadResponses(Row['Pre-Survey ID'])
        Pre_df = SurveyToNewVersion(pd.read_csv(PreSurveyName + '.csv', skiprows = [1, 2]))
        PreNames_df = GetNamesdf(Pre_df, 'Pre')
        if(Row['Number of Surveys'] == 3):
            MidSurveyName = DownloadResponses(Row['Mid-Survey ID'])
            Mid_df = SurveyToNewVersion(pd.read_csv(MidSurveyName + '.csv', skiprows = [1, 2]))
            MidNames_df = GetNamesdf(Mid_df, 'Mid')
            Names_df = PreNames_df.merge(MidNames_df, how = 'outer', left_on = ['Pre-Survey Last Names', 'Pre-Survey First Names'], right_on = ['Mid-Survey Last Names', 'Mid-Survey First Names'])
            Names_df1 = Names_df.merge(PostNames_df, how = 'outer', left_on = ['Pre-Survey Last Names', 'Pre-Survey First Names'], right_on = ['Post-Survey Last Names', 'Post-Survey First Names'])
            Names_df = PreNames_df.merge(MidNames_df, how = 'outer', left_on = ['Pre-Survey Last Names', 'Pre-Survey First Names'], right_on = ['Mid-Survey Last Names', 'Mid-Survey First Names'])
            Names_df2 = Names_df.merge(PostNames_df, how = 'inner', left_on = ['Pre-Survey Last Names', 'Pre-Survey First Names'], right_on = ['Post-Survey First Names', 'Post-Survey Last Names'])
            Names_df = pd.concat([Names_df1, Names_df2], axis = 0)
            if((not Pre_df.empty) and (not Mid_df.empty) and (not Post_df.empty)): # different conditions when three surveys were planned
                ReportGen.Generate(PDFName, r'\textwidth', Row['Number Of Students'], Row['Course Type'], Row['ID'], MainFolder, PRE = Pre_df, MID = Mid_df, POST = Post_df)
            elif((not Pre_df.empty) and (not Post_df.empty)):
                ReportGen.Generate(PDFName, r'\textwidth', Row['Number Of Students'], Row['Course Type'], Row['ID'], MainFolder, PRE = Pre_df, POST = Post_df)
            else:
                ReportGen.Generate(PDFName, r'\textwidth', Row['Number Of Students'], Row['Course Type'], Row['ID'], MainFolder, POST = Post_df)

        else: # different conditions when 2 surveys were planned
            Names_df1 = PreNames_df.merge(PostNames_df, how = 'outer', left_on = ['Pre-Survey Last Names', 'Pre-Survey First Names'], right_on = ['Post-Survey Last Names', 'Post-Survey First Names'])
            Names_df2 = PreNames_df.merge(PostNames_df, how = 'inner', left_on = ['Pre-Survey Last Names', 'Pre-Survey First Names'], right_on = ['Post-Survey First Names', 'Post-Survey Last Names'])
            Names_df = pd.concat([Names_df1, Names_df2], axis = 0)
            if((not Pre_df.empty) and (not Post_df.empty)):
                ReportGen.Generate(PDFName, r'\textwidth', Row['Number Of Students'], Row['Course Type'], Row['ID'], MainFolder, PRE = Pre_df, POST = Post_df)
            else:
                ReportGen.Generate(PDFName, r'\textwidth', Row['Number Of Students'], Row['Course Type'], Row['ID'], MainFolder, POST = Post_df)
    else:
        Names_df = PostNames_df.copy()
        ReportGen.Generate(PDFName, r'\textwidth', Row['Number Of Students'], Row['Course Type'], Row['ID'], MainFolder, POST = Post_df)

    if(Row['Credit Offered']):
        Names_df = Names_df.fillna('')
        Names_df['PostName'] = Names_df['Post-Survey Last Names'] + Names_df['Post-Survey First Names']
        if('Mid-Survey Last Names' in Names_df.columns):
            Names_df['PreName'] = Names_df['Pre-Survey Last Names'] + Names_df['Pre-Survey First Names']
            Names_df['MidName'] = Names_df['Mid-Survey Last Names'] + Names_df['Mid-Survey First Names']
            Names_df = Names_df[((~Names_df.duplicated(subset = 'PreName', keep = 'last')) | (Names_df['PreName'].isnull()))
                & ((~Names_df.duplicated(subset = 'MidName', keep = 'last')) | (Names_df['MidName'].isnull()))
                & ((~Names_df.duplicated(subset = 'PostName', keep = 'last')) | (Names_df['PostName'].isnull()))]
            Names_df = Names_df.drop_duplicates(subset = ['PreName', 'MidName', 'PostName'], keep = 'last')
            Names_df = Names_df.sort_values(by = ['PostName', 'MidName', 'PreName'])
            Names_df = Names_df.drop(labels = ['PreName', 'MidName', 'PostName'], axis = 1)
        elif('Pre-Survey Last Names' in Names_df.columns):
            Names_df['PreName'] = Names_df['Pre-Survey Last Names'] + Names_df['Pre-Survey First Names']
            Names_df = Names_df[((~Names_df.duplicated(subset = 'PreName', keep = 'last')) | (Names_df['PreName'] == ''))
                & ((~Names_df.duplicated(subset = 'PostName', keep = 'last')) | (Names_df['PostName'] == ''))]
            Names_df = Names_df.sort_values(by = ['PostName', 'PreName'])
            Names_df = Names_df.drop(labels = ['PreName', 'PostName'], axis = 1)
        else:
            Names_df = Names_df.sort_values(by = 'PostName')
            Names_df = Names_df.drop(labels = 'PostName', axis = 1)
        NamesFileName = Row['Season'] + str(Row['Course Year']) + '_' + Row['School'] + '_' + str(Row['Course Number']) +'_' + Row['Last Name'] + '_Names.csv'
        Names_df.to_csv(NamesFileName, index = False)
        if ErrorEmail:
            SendErrorEmail(Row['First Name'], Row['Last Name'], Row['Email'], str(Row['Course Name']), str(Row['Course Number']), NamesFile = NamesFileName)
            return 0
        SendReport(Row['First Name'], Row['Last Name'], Row['Email'], str(Row['Course Name']), str(Row['Course Number']), PDFName + '.pdf', NamesFile = NamesFileName)
    else:
        if ErrorEmail:
            SendErrorEmail(Row['First Name'], Row['Last Name'], Row['Email'], str(Row['Course Name']), str(Row['Course Number']))
            return 0
        SendReport(Row['First Name'], Row['Last Name'], Row['Email'], str(Row['Course Name']), str(Row['Course Number']), PDFName + '.pdf')

    return 0

# def SurveyToNewVersion(df, CurrentVersion = MainFolder + 'PLIC_May2019.csv'):
#     df = df.drop(labels = 'Status', axis = 1)
#
#     df.columns = pd.read_csv(CurrentVersion).columns
#
#     return df

def DownloadResponses(SurveyID):
    """Download responses to a Qualtrics survey.

    Keyword arguments:
    SurveyID -- ID of survey
    """


    # Setting user Parameters
    fileFormat = "csv"

    # Setting static parameters
    requestCheckProgress = 0
    progressStatus = "in progress"
    headers = {
        "content-type": "application/json",
        "x-api-token": apiToken,
        }

    # Step 1: Creating Data Export
    downloadRequestUrl = baseURL
    downloadRequestPayload = '{"format":"' + fileFormat + '","surveyId":"' + SurveyID + '"}'
    downloadRequestResponse = requests.request("POST", downloadRequestUrl, data = downloadRequestPayload, headers = headers)
    progressId = downloadRequestResponse.json()["result"]["id"]

    # Step 2: Checking on Data Export Progress and waiting until export is ready

    isFile = None

    while requestCheckProgress < 100 and progressStatus is not "complete" and isFile is None:
        requestCheckUrl = baseURL + progressId
        requestCheckResponse = requests.request("GET", requestCheckUrl, headers = headers)
        isFile = (requestCheckResponse.json()["result"]["file"])
        requestCheckProgress = requestCheckResponse.json()["result"]["percentComplete"]

    # Step 3: Downloading file
    requestDownloadUrl = baseURL + progressId + '/file'
    requestDownload = requests.request("GET", requestDownloadUrl, headers = headers, stream = True)

    # Step 4: Unzipping the file
    try:
        zipfile.ZipFile(io.BytesIO(requestDownload.content)).extractall()
    except zipfile.BadZipfile:
        print("Bad Zip File, trying again...")
        DownloadResponses(SurveyID)

    return GetSurveyName(SurveyID)

def GetNumberStudents(Row, Survey):
    """Get number of students that have completed a survey.

    Keyword arguemts:
    Row -- a series object of one row from the course information survey
    Survey -- type of survey: Pre, Mid, or Post
    """

    # Move to the specific course directory to download responses
    TermDir = MainFolder + Row['Season'] + str(int(Row['Course Year'])) + "Files"
    if not os.path.exists(TermDir):
        os.mkdir(TermDir, 755)
    CourseDir = Row['School'] + '_' + str(Row['Course Number']) + '_' + Row['Last Name'] + '_' + Row['ID']
    CourseDir = TermDir + "//" + CourseDir
    if not os.path.exists(CourseDir):
        os.mkdir(CourseDir, 755)

    os.chdir(CourseDir)
    DownloadResponses(Row[Survey + '-Survey ID'])
    Survey_Name = GetSurveyName(Row[Survey + '-Survey ID'])
    StudentDF = pd.read_csv(Survey_Name + '.csv', skiprows = [1, 2])

    NumStudents = len(StudentDF.index)
    return NumStudents

def GetNamesdf(df, Survey):
    """Get names and IDs of students that have completed a survey.

    Keyword arguments:
    df -- dataframe of student responses to a survey
    Survey -- which survey to pull data from: Pre, Mid, or Post
    """

    Names_df = df.loc[:, ['Q5a', 'Q5b', 'Q5c']].dropna(how = 'all').reset_index(drop = True) # Get Names columns from dataframe
    NCNames_df = df.loc[:, ['QNC1a', 'QNC1b', 'QNC1c']].dropna(how = 'all').reset_index(drop = True).rename(columns = {'QNC1a':'Q5a', 'QNC1b':'Q5b', 'QNC1c':'Q5c'}) # Get non-consenting names from dataframe
    Names_df = pd.concat([Names_df, NCNames_df], axis = 0, join = 'inner').reset_index(drop = True).replace(1, '').apply(lambda x: x.astype(str).str.lower()) # Join the dataframes and convert everything to lower case
    Names_df.columns = [Survey + '-Survey IDs', Survey + '-Survey Last Names', Survey + '-Survey First Names'] # Set column names
    return Names_df

def GetSurveyName(SurveyID):
    """Get the name of a survey.

    Keyword arguments:
    SurveyID -- ID of survey
    """

    baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(DataCenter, SurveyID)
    headers = {
        "x-api-token": apiToken,
        }

    Req = Request(baseUrl, headers=headers)
    Response = urlopen(Req)
    SurveyName = json.load(Response)['result']['name']

    return SurveyName

def MakeSurvey(Row, Survey):
    """Make a Qualtrics survey.

    Keyword arguments:
    Row -- series object of one row from the course information survey
    Survey -- which survey to make a new survey for: Pre, Mid, or Post
    """

    baseURL = "https://{0}.qualtrics.com/API/v3/surveys".format(DataCenter)
    headers = {
        "x-api-token": apiToken,
        }

    files = {
        'file': ('PLICSurvey.qsf', open('PLICSurvey.qsf', 'rb'), 'application/vnd.qualtrics.survey.qsf')
        }

    data = {
        "name": Row['Season'] + str(Row['Course Year']) + '_' + Row['School'] + '_' + str(Row['Course Number']) +'_' + Row['Last Name'] + '_' + Survey + '_' + Row['ID'],
        }
    response = requests.post(baseURL, files = files, data = data, headers = headers)
    StringResponse = json.dumps(response.json())
    jsonResponse = json.loads(StringResponse)
    SurveyID = jsonResponse['result']['id']

    return SurveyID

def ShareSurvey(UserID, SurveyID):
    """Share a survey with another Qualtrics user.

    Keyword arguments:
    UserID -- ID of user to share the survey with
    SurveyID -- ID of survey to share
    """

    headers = {
        'x-api-token': apiToken,
        'content-type': 'application/json',
        }

    data = {
        "userId" : UserID,
        "permissions" : {
            "surveyDefinitionManipulation" : {
                "copySurveyQuestions" : True,
                "editSurveyFlow" : True,
                "useBlocks" : True,
                "useSkipLogic" : True,
                "useConjoint" : True,
                "useTriggers" : True,
                "useQuotas" : True,
                "setSurveyOptions" : True,
                "editQuestions" : True,
                "deleteSurveyQuestions" : True
                },
            "surveyManagement" : {
                "editSurveys" : True,
                "activateSurveys" : True,
                "deactivateSurveys" : True,
                "copySurveys" : True,
                "distributeSurveys" : True,
                "deleteSurveys" : True,
                "translateSurveys" : True
                },
            "response" : {
                "editSurveyResponses" : True,
                "createResponseSets" : True,
                "viewResponseId" : True,
                "useCrossTabs" : True
                },
            "result" : {
                "downloadSurveyResults" : True,
                "viewSurveyResults" : True,
                "filterSurveyResults" : True,
                "viewPersonalData" : True
                }
            }
        }

    requests.post('https://{0}.qualtrics.com/API/v3/surveys/{1}/permissions/collaborations'.format(DataCenter, SurveyID), headers=headers, data=json.dumps(data))

    return 0

def ActivateSurvey(SurveyID, Active = True):
    """Activate a Qualtrics survey.

    Keyword arguments:
    SurveyID -- ID of the survey to activate
    """

    baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(DataCenter, SurveyID)
    headers = {
        "content-type": "application/json",
        "x-api-token": apiToken,
        }

    data = {
        "isActive": Active,
        }

    response = requests.put(baseUrl, json=data, headers=headers)

    return 0

def SendSurveyMemo(Row, MidPost):
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail
    # msg['To'] = Row['Email']
    msg['Subject'] = "PLIC {}-Survey Memo".format(MidPost)

    SurveyOpenDate = (Row['Close Date'] - datetime.timedelta(days = 14)).strftime("%d-%b-%Y %H:%M:%S")
    SurveyCloseDate = (Row['Close Date'] + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

    # Create the body of the message (a plain-text and an HTML version).
    text = """
           Dear Dr. {First} {Last},\n\n

           Thank you again for participating in the PLIC. You will receive the link
           to the {Survey}-instruction survey for your course, {Course} ({Code}) on the
           following date:\n
           {Open} EST\n
           This link will remain active remain active until:\n
           {Close} EST\n
           If you would like to change the date that the post-survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):\n\n

           {ChangeURL}\n\n

           Let us know by replying to this email if you have any questions about
           this process.\n\n

           Thank you,\n
           Cornell Physics Education Research Lab\n\n
           This message was sent by an automated system.\n
           """.format(First = Row['First Name'], Last = Row['Last Name'], Survey = MidPost, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], Open = SurveyOpenDate, Close = SurveyCloseDate,
           Identifier = Row['ID'], ChangeURL = ChangeURL)

    html = """\
    <html>
      <head></head>
      <body>
        <p>Dear Dr. {First} {Last},<br><br>

           Thank you again for participating in the PLIC. You will receive the link
           to the {Survey}-instruction survey for your course, {Course} ({Code}) on the
           following date:<br>
           {Open} EST<br>
           This link will remain active remain active until:<br>
           {Close} EST<br>
           If you would like to change the date that the post-survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):<br><br>

           {ChangeURL}<br><br>

           Let us know by replying to this email if you have any questions about
           this process.<br><br>

           Thank you,<br>
           Cornell Physics Education Research Lab<br><br>
           This message was sent by an automated system.
        </p>
      </body>
    </html>
    """.format(First = Row['First Name'], Last = Row['Last Name'], Survey = MidPost, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], Open = SurveyOpenDate, Close = SurveyCloseDate,
    Identifier = Row['ID'], ChangeURL = ChangeURL)
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # The actual mail send
    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail, EmailPassword)
    server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    # server.sendmail(CPERLEmail, Row['Email'], msg.as_string())
    server.quit()

    return 0

def SendPreSurvey(Row):
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail
    # msg['To'] = Row['Email']
    msg['Cc'] = CPERLEmail
    msg['Subject'] = " PLIC Pre-Instruction Survey Link"

    SurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + Row['Pre-Survey ID']
    SurveyCloseDate = (pd.to_datetime(Row['Pre-Survey Close Date']) + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

    text = """
            Dear Dr. {First} {Last},\n\n

            Thank you again for completing the course information survey. Below is
            the link for the pre-instruction survey for your course, {Course} ({Code}):\n\n
            {Survey}\n\n
            Please share this link with your students on the first day of class. \n \n
            In order to get the best data, we recommend that students complete the
            PLIC within the first week of class. Accordingly, we recommend that
            you distribute the link to your students at least 7 days before the close
            date listed below.\n\n
            The date the survey is currently set to close is:\n
            {Close} EST\n
            If you would like to change the dates that the PRE- and/or POST-surveys
            will stop accepting responses from students, please complete the form here
            with your unique ID({Identifier}):\n\n

            {ChangeURL}\n\n

            Let us know by replying to this email if you have any questions about
            this process.\n\n

            Thank you,\n
            Cornell Physics Education Research Lab\n
            This message was sent by an automated system.\n
            """.format(Close = SurveyCloseDate, First = Row['First Name'], Last = Row['Last Name'], Survey = SurveyURL, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'],
            Identifier = Row['ID'], ChangeURL = ChangeURL)
    html = """\
	<html>
	  <head></head>
	  <body>
		<p>Dear Dr. {First} {Last},<br><br>

		   Thank you again for completing the course information survey. Below is
           the link for the pre-instruction survey for your course, {Course} ({Code}):<br><br>
		   {Survey}<br><br>
		   Please share this link with your students on the first day of class.<br><br>
		   In order to get the best data, we recommend that students complete the
           PLIC within the first week of class. Accordingly, we recommend that
           you distribute the link to your students at least 7 days before the close
           date listed below.<br><br>
		   The date the survey is currently set to close is:<br>
		   {Close} EST<br>
           If you would like to change the dates that the PRE- and/or POST-surveys
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):<br><br>

           {ChangeURL}<br><br>

           Let us know by replying to this email if you have any questions about
           this process.<br><br>

		   Thank you,<br>
           Cornell Physics Education Research Lab<br>
		   This message was sent by an automated system.
		</p>
	  </body>
	</html>
	""".format(Close = SurveyCloseDate, First = Row['First Name'], Last = Row['Last Name'], Survey = SurveyURL, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'],
    Identifier = Row['ID'], ChangeURL = ChangeURL)


    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail,EmailPassword)
    server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    # server.sendmail(CPERLEmail, [Row['Email'], CPERLEmail], msg.as_string())
    server.quit()

    return 0

def SendSurvey(Row, MidPost):
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail
    # msg['To'] = Row['Email']
    msg['Cc'] = CPERLEmail
    msg['Subject'] = "PLIC {}-Survey link".format(MidPost)

    SurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + Row[MidPost + '-Survey ID']
    SurveyCloseDate = (pd.to_datetime(Row[MidPost  + '-Survey Close Date']) + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

    # Create the body of the message (a plain-text and an HTML version).
    text = """
		   Dear Dr. {First} {Last},\n\n

		   Thank you again for participating in the PLIC. Below is the link to the {Survey}-instruction
           survey for your course, {Course} ({Code}):\n\n
		   {SurveyLink}\n\n
		   Please share this link with your students at least 7 days before the close
           date listed below.\n\n
		   This link is currently active and will remain active until:\n
		   {Close} EST\n
           If you would like to change the date that the post-survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):\n\n

           {ChangeURL}\n\n

           Let us know by replying to this email if you have any questions about
           this process.\n\n

		   Thank you, \n
		   Cornell Physics Education Research Lab\n\n
		   This message was sent by an automated system.\n
		   """.format(First = Row['First Name'], Last = Row['Last Name'], Survey = MidPost, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], SurveyLink = SurveyURL, Close = SurveyCloseDate,
           Identifier = Row['ID'], ChangeURL = ChangeURL)

    html = """\
    <html>
	  <head></head>
	  <body>
        <p>Dear Dr. {First} {Last},<br><br>

		   Thank you again for participating in the PLIC. Below is the link to the {Survey}-instruction
           survey for your course, {Course} ({Code}):<br><br>
		   {SurveyLink}<br><br>
		   Please share this link with your students at least 7 days before the close date listed below. <br><br>
		   This link is currently active and will remain active until:<br>
		   {Close} EST<br>
           If you would like to change the date that the post-survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):<br><br>

           {ChangeURL}<br><br>

           Let us know by replying to this email if you have any questions about
           this process. <br><br>

		   Thank you,<br>
		   Cornell Physics Education Research Lab<br><br>
		   This message was sent by an automated system.
        </p>
	  </body>
    </html>
    """.format(First = Row['First Name'], Last = Row['Last Name'], Survey = MidPost, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], SurveyLink = SurveyURL, Close = SurveyCloseDate,
    Identifier = Row['ID'], ChangeURL = ChangeURL)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # The actual mail send
    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail, EmailPassword)
    server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    # server.sendmail(CPERLEmail, [Row['Email'], CPERLEmail], msg.as_string())
    server.quit()

    return 0

def ReminderEmailSend(Row, Survey):
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail
    # msg['To'] = InstructorEmail
    msg['Subject'] = "Reminder for the PLIC survey"
    SurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + Row[Survey + '-Survey ID']
    SurveyCloseDate = (Row['Close Date'] + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

    # Create the body of the message (a plain-text and an HTML version).
    text = """
		   Dear Dr. {First} {Last},\n \n

           This is a reminder from the CPERL team about the PLIC {Survey}-survey for
           {Course} ({Code}) which will close on {Close} EST.\n \n
           So far there have been {Responses} responses to the survey.\n \n
           Here is another link to the survey: \n
		   {Link} \n \n

           If you would like to change the date that the survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):\n\n

           {ChangeURL}\n\n

           Let us know by replying to this email if you have any questions about
           this process. \n \n

		   Thank you, \n
		   Cornell Physics Education Research Lab \n \n
		   This message was sent by an automated system. \n
		   """.format(First = Row['First Name'], Last = Row['Last Name'], Survey = Survey, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], Identifier = Row['ID'], Responses = Row['N_Students'], Close = SurveyCloseDate, Link = SurveyURL, ChangeURL = ChangeURL)

    html = """\
    <html>
	  <head></head>
	  <body>
        <p>Dear Dr. {First} {Last}, <br><br>

            This is a reminder from the CPERL team about the PLIC {Survey}-survey
            for {Course} ({Code}) which will close on {Close} EST.<br><br>
            So far there have been {Responses} responses to the survey. <br><br>
            Here is another link to the survey: <br>
			{Link} <br>

            If you would like to change the date that the survey
            will stop accepting responses from students, please complete the form here
            with your unique ID({Identifier}):<br><br>

            {ChangeURL}<br><br>


            Let us know by replying to this email if you have any questions about
            this process. <br><br>

		   Thank you, <br>
		   Cornell Physics Education Research Lab <br><br>
		   This message was sent by an automated system.
		</p>
	  </body>
    </html>
    """.format(First = Row['First Name'], Last = Row['Last Name'], Survey = Survey, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], Identifier = Row['ID'], Responses = Row['N_Students'], Close = SurveyCloseDate, Link = SurveyURL, ChangeURL = ChangeURL)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # The actual mail send
    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail,EmailPassword)
    server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    # server.sendmail(CPERLEmail, InstructorEmail, msg.as_string())
    server.quit()

    return 0

def ZeroResponseEmail(Row, Survey):
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail
    # msg['To'] = Row['Email']
    msg['Subject'] = "There have been zero responses to the PLIC"

    SurveyURL = SurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + Row[Survey + '-Survey ID']
    SurveyCloseDate = (Row['Close Date'] + datetime.timedelta(days = 3, hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

    # Create the body of the message (a plain-text and an HTML version).
    text = """
           Dear Dr. {First} {Last},\n\n

           This is a reminder from the CPERL team about the PLIC {Survey}-survey.
           Currently there are no responses to the survey for your course: {Course} ({Code}).\n\n
           We have extended the close date for the survey to: {Close} EST.\n\n
           If you have not already done so, please send out the link to your class.\n\n
           Here is another link to the survey:\n
           {Link}\n\n

           If you would like to change the date that the survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):\n\n

           {ChangeURL}\n\n

           Let us know by replying to this email if you have any questions about
           this process.\n\n

           Thank you,\n
           Cornell Physics Education Research Lab\n
           This message was sent by an automated system.\n
           """.format(First = Row['First Name'], Last = Row['Last Name'], Survey = Survey, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], Close = SurveyCloseDate, Link = SurveyURL,
           Identifier = Row['ID'], ChangeURL = ChangeURL)

    html = """\
    <html>
      <head></head>
      <body>
        Dear Dr. {First} {Last},<br><br>

           This is a reminder from the CPERL team about the PLIC {Survey}-survey.
           Currently there are no responses to the survey for your course: {Course} ({Code})<br><br>
           We have extended the close date for the survey to: {Close} EST.<br><br>
           If you have not already done so, please send out the link to your class.<br><br>
           Here is another link to the survey:<br>
           {Link}<br><br>

           If you would like to change the date that the survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):<br><br>

           {ChangeURL}<br><br>

           Let us know by replying to this email if you have any questions about
           this process.<br><br>

           Thank you,<br>
           Cornell Physics Education Research Lab<br><br>
           This message was sent by an automated system.<br>
        </p>
      </body>
    </html>
    """.format(First = Row['First Name'], Last = Row['Last Name'], Survey = Survey, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], Close = SurveyCloseDate, Link = SurveyURL,
    Identifier = Row['ID'], ChangeURL = ChangeURL)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    #Email Credentials


    # The actual mail send
    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail, EmailPassword)
    server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    # server.sendmail(CPERLEmail, Row['Email'], msg.as_string())
    server.quit()

    return 0

def ChangesEmailSend(Row): # This function is called on a particular row so it looks different that the other email functions
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Changes to Survey Dates"
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail
    # msg['To'] = InstructorEmail

    if(pd.notnull(Row['Pre-Survey Close Date'])):
        PreClose = datetime.datetime.strptime(Row['Pre-Survey Close Date'], "%d-%b-%Y")
        PreClose = (PreClose + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")
    else:
        PreClose = 'Not Available'

    if(pd.notnull(Row['Mid-Survey Close Date'])):
        MidClose = datetime.datetime.strptime(Row['Mid-Survey Close Date'], "%d-%b-%Y")
        MidClose = (MidClose + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")
    else:
        MidClose = 'Not Available'

    PostClose = datetime.datetime.strptime(Row['Post-Survey Close Date'], "%d-%b-%Y")
    PostClose = (PostClose + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

	# Create the body of the message (a plain-text and an HTML version).
    text = """
		   Dear Dr. {First} {Last},\n\n

		   Thank you again for participating in the PLIC. Changes were recently made to the pre- and/or post-survey close dates
           for your class, {Course} ({Code}). These surveys are currently set to close for students at the following times:\n\n

           PRE -- {PreClose} EST\n
           MID -- {MidClose} EST\n
           POST -- {PostClose} EST\n\n

           If you would like to change these dates again, please fill out the form again with your unique ID ({Identifier}):\n\n
           {ChangeURL}\n\n


		   Thank you,\n
		   Cornell Physics Education Research Lab\n\n
		   This message was sent by an automated system.\n
		   """.format(First = Row['First Name'], Last = Row['Last Name'], Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], PreClose = PreClose, MidClose = MidClose, PostClose = PostClose, Identifier = Row['ID'], ChangeURL = ChangeURL)

    html = """\
	<html>
	  <head></head>
	  <body>
		<p>Dear Dr. {First} {Last},<br><br>

		   Thank you again for participating in the PLIC. Changes were recently made to the pre- and/or post-survey close dates
           for your class, {Course} ({Code}). These surveys are currently set to close for students at the following times:<br><br>

           PRE -- {PreClose} EST<br>
           MID -- {MidClose} EST<br>
           POST -- {PostClose} EST<br><br>

           If you would like to change these dates again, please fill out the form again with your unique ID ({Identifier}):<br><br>
           {ChangeURL}<br><br>


		   Thank you,<br>
		   Cornell Physics Education Research Lab<br><br>
		   This message was sent by an automated system.<br>
		</p>
	  </body>
	</html>
   """.format(First = Row['First Name'], Last = Row['Last Name'], Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], PreClose = PreClose, MidClose = MidClose, PostClose = PostClose, Identifier = Row['ID'], ChangeURL = ChangeURL)


    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail, EmailPassword)
    server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    # server.sendmail(CPERLEmail, InstructorEmail, msg.as_string())
    server.quit()

    return 0

def SendSurveyClose(Row, PreMid):
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail
    # msg['To'] = Row['Email']
    msg['Subject'] = "PLIC {}-Instruction Survey Now Closed".format(PreMid)

    if(Row['Number of Surveys'] == 3 and PreMid == 'Pre'):
        MidPost = 'Mid'
    else:
        MidPost = 'Post'

    PostSurveyOpen = (datetime.datetime.strptime(Row[MidPost + '-Survey Close Date'], '%d-%b-%Y') - datetime.timedelta(days = 14)).strftime("%d-%b-%Y %H:%M:%S")

    text = """
            Dear Dr. {First} {Last},\n\n

            Thank you again for participating in the PLIC. The {Survey}-instruction
            survey for your course, {Course} ({Code}), is now closed. {Num} students
            completed this iteration of the survey. If you are offering credit
            for completing this survey, their names will be provided at the
            conclusion of the post-instruction survey at the end of the course.\n\n

            The {NextSurvey}-instruction survey will be available for your students beginning
            at {TimeOpen}. We will send you a link to the survey at that time.\n

            If you would like to change the date that the {NextSurvey}-survey
            will stop accepting responses from students, please complete the form here
            with your unique ID({Identifier}):\n\n

            {ChangeURL}\n\n

            Let us know by replying to this email if you have any questions about
            this process.\n\n

            Thank you,\n
            Cornell Physics Education Research Lab\n
            This message was sent by an automated system.\n
            """.format(First = Row['First Name'], Last = Row['Last Name'], Survey = PreMid, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], Num = Row['N_Students'], NextSurvey = MidPost,
            TimeOpen = PostSurveyOpen, Identifier = Row['ID'], ChangeURL = ChangeURL)

    html = """\
	<html>
	  <head></head>
	  <body>
		<p>Dear Dr. {First} {Last},<br><br>

            Thank you again for participating in the PLIC. The {Survey}-instruction
            survey for your course, {Course} ({Code}), is now closed. {Num} students
            completed this iteration of the survey. If you are offering credit
            for completing this survey, their names will be provided at the
            conclusion of the post-instruction survey at the end of the course.<br><br>

            The {NextSurvey}-instruction survey will be available for your students beginning
            at {TimeOpen}. We will send you a link to the survey at that time.<br>

            If you would like to change the date that the {NextSurvey}-survey
            will stop accepting responses from students, please complete the form here
            with your unique ID({Identifier}):<br><br>

            {ChangeURL}<br><br>

            Let us know by replying to this email if you have any questions about
            this process.<br><br>

		   Thank you,<br>
           Cornell Physics Education Research Lab<br>
		   This message was sent by an automated system.
		</p>
	  </body>
	</html>
	""".format(First = Row['First Name'], Last = Row['Last Name'], Survey = PreMid, Course = Row['Course Name'].replace("_", " "), Code = Row['Course Number'], Num = Row['N_Students'], NextSurvey = MidPost,
    TimeOpen = PostSurveyOpen, Identifier = Row['ID'], ChangeURL = ChangeURL)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail,EmailPassword)
    server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    # server.sendmail(CPERLEmail, Row['Email'], msg.as_string())
    server.quit()

    return 0

def SendReport(InstructorFirst, InstructorLast, InstructorEmail, CourseName, Code, ReportFile, NamesFile = None): # Note that unlike other email send functions, this one takes values, not a series as arguments (again, it is called within another function)
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail
    # msg['To'] = InstructorEmail
    msg['Cc'] = CPERLEmail
    msg['Subject'] = "PLIC Report"

    # Create the body of the message (a plain-text and an HTML version).
    text = """
           Dear Dr. {First} {Last},\n\n

           Thank you again for participating in the PLIC. Please find attached a copy of the report summarizing the PLIC
           results for your course, {Course} ({Code}). Additionally, if you indicated to us that you are offering students credit
           for completing the survey we have included a CSV file with their names here.\n\n

           We have recently begun developing an online interactive dashboard where instructors can explore their data in more
           depth. The dashboard is currently available at:\n\n

           http://colewalsh295.shinyapps.io/PLIC-DataExplorer\n\n

           You can also download de-identified data from this dashboard (if you would like identifiable data from your class
           please reply to this email with a copy of Institutional Review Board approval from your institution).

           We are continuing to test this new dashboard to better improve user experiences, so please let us know by replying
           to this email if you have any questions, comments, or suggestions regarding this new dashboard and/or new report format.\n\n

           Thank you,\n
           Cornell Physics Education Research Lab\n\n
           This message was sent by an automated system.\n
           """.format(First = InstructorFirst, Last = InstructorLast, Course = CourseName.replace("_", " "), Code = Code)

    html = """\
    <html>
      <head></head>
      <body>
        <p>Dear Dr. {First} {Last},<br><br>

           Thank you again for participating in the PLIC. Please find attached a copy of the report summarizing the PLIC
           results for your course, {Course} ({Code}). Additionally, if you indicated to us that you are offering students credit
           for completing the survey we have included a CSV file with their names here.<br><br>

           We have recently begun developing an online interactive dashboard where instructors can explore their data in more
           depth. The dashboard is currently available at:<br><br>

           http://colewalsh295.shinyapps.io/PLIC-DataExplorer<br><br>

           You can also download de-identified data from this dashboard (if you would like identifiable data from your class
           please reply to this email with a copy of Institutional Review Board approval from your institution).

           We are continuing to test this new dashboard to better improve user experiences, so please let us know by replying
           to this email if you have any questions, comments, or suggestions regarding this new dashboard and/or new report format.

           Thank you,<br>
           Cornell Physics Education Research Lab<br><br>
           This message was sent by an automated system.
        </p>
      </body>
    </html>
    """.format(First = InstructorFirst, Last = InstructorLast, Course = CourseName.replace("_", " "), Code = Code)


    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    f_pdf = open(ReportFile, 'rb')
    att_pdf = MIMEApplication(f_pdf.read(), _subtype = "pdf")
    f_pdf.close()
    att_pdf.add_header('Content-Disposition', 'attachment', filename = ReportFile)
    msg.attach(att_pdf)

    if(NamesFile is not None):
        f_csv=open(NamesFile, 'rb')
        att_csv = MIMEApplication(f_csv.read(), _subtype="csv")
        f_csv.close()
        att_csv.add_header('Content-Disposition', 'attachment', filename = NamesFile)
        msg.attach(att_csv)

    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail, EmailPassword)
    server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    # server.sendmail(CPERLEmail, [InstructorEmail, CPERLEmail], msg.as_string())
    server.quit()

    return 0

def SendErrorEmail(InstructorFirst, InstructorLast, InstructorEmail, CourseName, Code, NamesFile = None): # Note that unlike other email send functions, this one takes values, not a series as arguments
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail
    # msg['To'] = InstructorEmail
    msg['Cc'] = CPERLEmail
    msg['Subject'] = "PLIC Report"

    # Create the body of the message (a plain-text and an HTML version).
    text = """
           Dear Dr. {First} {Last},\n\n

           Thank you again for participating in the PLIC. Unfortunately, fewer than 5 students took each survey so we are unable to
           provide a summary of your students' performance as the data may be identifiable. If you indicated to us that you are
           offering students credit for completing the survey we have included a CSV file with their names here. Additionally,
           if you would like to receive a report of your students' performance and/or identifiable data from your class please
           reply to this email with a copy of Institutional Review Board approval from your institution.\n\n

           Thank you,\n
           Cornell Physics Education Research Lab\n\n
           This message was sent by an automated system.\n
           """.format(First = InstructorFirst, Last = InstructorLast, Course = CourseName.replace("_", " "), Code = Code)

    html = """\
    <html>
      <head></head>
      <body>
        <p>Dear Dr. {First} {Last},<br><br>
           Thank you again for participating in the PLIC. Unfortunately, fewer than 5 students took each survey so we are unable to
           provide a summary of your students' performance as the data may be identifiable. If you indicated to us that you are
           offering students credit for completing the survey we have included a CSV file with their names here. Additionally,
           if you would like to receive a report of your students' performance and/or identifiable data from your class please
           reply to this email with a copy of Institutional Review Board approval from your institution.<br><br>

           Thank you,<br>
           Cornell Physics Education Research Lab<br><br>
           This message was sent by an automated system.
        </p>
      </body>
    </html>
    """.format(First = InstructorFirst, Last = InstructorLast, Course = CourseName.replace("_", " "), Code = Code)


    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    f_pdf = open(ReportFile, 'rb')
    att_pdf = MIMEApplication(f_pdf.read(), _subtype = "pdf")
    f_pdf.close()
    att_pdf.add_header('Content-Disposition', 'attachment', filename = ReportFile)
    msg.attach(att_pdf)

    if(NamesFile is not None):
        f_csv=open(NamesFile, 'rb')
        att_csv = MIMEApplication(f_csv.read(), _subtype="csv")
        f_csv.close()
        att_csv.add_header('Content-Disposition', 'attachment', filename = NamesFile)
        msg.attach(att_csv)

    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail, EmailPassword)
    server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    # server.sendmail(CPERLEmail, [InstructorEmail, CPERLEmail], msg.as_string())
    server.quit()

    return 0

if __name__ == '__main__':
	main()
