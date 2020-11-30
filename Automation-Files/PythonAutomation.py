# -*- coding: utf-8 -*-
#!c:/Python/python3_6.exe -u

import os
import sys
import traceback
import csv
import pandas as pd
import re
import time
import sched
import datetime
import requests
try: import simplejson as json
except ImportError: import json
import zipfile
import pycurl
from urllib.request import Request, urlopen
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import numpy as np
import ReportGen

# Setting user Parameters
global apiToken, DataCenter, CPERLEmail, UserEmail, ChangeURL
admin_info = pd.read_csv('Admin_Info.csv', index_col = False, header = 0).T[0] # get sensitive admininstration info
apiToken = admin_info['API'] # change token for different Qualtrics account
SharedCole = admin_info['SharedCole']
SharedUsers = [SharedCole]
DataCenter = 'cornell'
baseURL = "https://{0}.qualtrics.com/API/v3/responseexports/".format(DataCenter)
ChangeURL = "https://{0}.qualtrics.com/jfe/form/SV_cAqEOkCAV8mTNSR".format(DataCenter)

CPERLEmail = 'cperl@cornell.edu'
UserEmail = 'as-phy-edresearchlab@cornell.edu' # dummy email used to access mail client
EmailPassword = admin_info['EmailPassword']

# main exceution body which repaets every hour
def main():
    InstructorSurveyControl()
    CourseChangesControl()
    PreSurveyControl()
    MidSurveyControl()
    PostSurveyControl()
    ReportControl()
    print("Waiting...")
    s = sched.scheduler(time.time, time.sleep)
    def runprogram(sc):
        try:
            print("Automation executed at: " + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
            if(int(time.strftime("%H",time.localtime())) == 16):
                SendStatusEmail()
            InstructorSurveyControl()
            CourseChangesControl()
            PreSurveyControl()
            MidSurveyControl()
            PostSurveyControl()
            ReportControl()
            sc.enter(3600, 1, runprogram, (sc,))
            print("Waiting...")
        # If an error occurs somewhere in here, print to screen, but run again in one hour
        except Exception as e:
            print("Error at: " + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            tb = traceback.extract_tb(exc_tb)[-1]
            print(exc_type, tb[2], tb[1])
            sc.enter(3600, 1, runprogram, (sc,))
            print("Waiting...")
    s.enter(3600, 1, runprogram, (s,))
    s.run()
    return 0

def InstructorSurveyControl():
    # check course information survey, downloaded from qualtrics...if new entries exist, add them to the master data file, create surveys, and send pre
    # survey
    print("Checking CIS...")
    os.chdir("C:/PLIC") # Main Survey Directory
    with open("MasterCourseData.csv",'r', newline = '\n') as f:
        MasterData = list(csv.reader(f))
        NumRows = len(MasterData)
        global LastAccess
        LastAccess = time.strftime("%d-%b-%Y %H:%M:%S %Z",time.localtime())
        MasterData[0][1] = LastAccess

    with open("MasterCourseData.csv",'w') as f:
        FileWriter = csv.writer(f)
        FileWriter.writerows(MasterData)

    SurveyID = "SV_5bVFmY2ZpC7zA4l" # Course Information Survey ID
    DownloadResponses(SurveyID) # pull data from Qualtrics

    InstructorsDF = pd.read_csv("Course_Information_Survey.csv", skiprows = [1, 2])
    InfoDummyDF = pd.read_csv('Course_Information_Survey.csv', skiprows = [2]) # Keep Header...we're only going to take one row from this to keep in the course's folder for specific info

    with open("MasterCourseData.csv",'a') as f0:
        MasterDataWriter = csv.writer(f0) # Write new entries in online Qualtrics survey to local Master Data file
        for Index, Instructor in InstructorsDF.iterrows():
            if((InstructorsDF.loc[Index, 'Finished'] == 0) | (pd.isnull(InstructorsDF.loc[Index, 'Q11_v2']))): # Check if they actually finished the online survey and gave a post-survey date
                continue
            MasterDataRow = 2
            PreviouslyRecorded = False
            while(MasterDataRow < NumRows):
                if(InstructorsDF.loc[Index, 'ResponseID'] == MasterData[MasterDataRow][0]): # ResponseID stored in column zero in .csv file
                    PreviouslyRecorded = True
                    break
                else:
                    MasterDataRow += 1

            if(not PreviouslyRecorded):
                # use regex to replace any non-alphanumeric characters with underscores...cause instructors fill forms with weird stuff
                ID = InstructorsDF.loc[Index, 'ResponseID']
                FirstName = re.sub('[^0-9a-zA-Z]+', '_', InstructorsDF.loc[Index, 'Q1'])
                print(FirstName)
                LastName = re.sub('[^0-9a-zA-Z]+', '_', InstructorsDF.loc[Index, 'Q2'])
                Email = InstructorsDF.loc[Index, 'Q3']
                School = re.sub('[^0-9a-zA-Z]+', '_', InstructorsDF.loc[Index, 'Q4'])
                CourseName = re.sub('[^0-9a-zA-Z]+', '_', InstructorsDF.loc[Index, 'Q5'])
                CourseNumber = re.sub('[^0-9a-zA-Z]+', '_', str(InstructorsDF.loc[Index, 'Q6']))
                NumStudents = InstructorsDF.loc[Index, 'Q8']
                if(pd.notnull(InstructorsDF.loc[Index, 'Q10_v2'])):
                    if((len(InstructorsDF.loc[Index, 'Q10_v2']) < 10) | ('/' in InstructorsDF.loc[Index, 'Q10_v2'])):
                        InstructorsDF.loc[Index, 'Q10_v2'] = FixDates(InstructorsDF.loc[Index, 'Q10_v2'])
                    try:
                        PreCloseDate = datetime.datetime.strptime(InstructorsDF.loc[Index, 'Q10_v2'], "%m-%d-%Y") # catch all for date errors
                    except:
                        PreCloseDate = datetime.datetime.now() + datetime.timedelta(days = 14)
                    if(PreCloseDate < datetime.datetime.now()): # If the date is from the middle ages, set the close dates to something in the future
                        PreCloseDate = PreCloseDate + datetime.timedelta(days = 14)
                if(pd.notnull(InstructorsDF.loc[Index, 'Q41_v2'])):
                    if((len(InstructorsDF.loc[Index, 'Q41_v2']) < 10) | ('/' in InstructorsDF.loc[Index, 'Q41_v2'])):
                        InstructorsDF.loc[Index, 'Q41_v2'] = FixDates(InstructorsDF.loc[Index, 'Q41_v2'])
                    try:
                        MidCloseDate = datetime.datetime.strptime(InstructorsDF.loc[Index, 'Q41_v2'], "%m-%d-%Y")
                    except:
                        MidCloseDate = datetime.datetime.now() + datetime.timedelta(days = 30)
                    if(MidCloseDate < datetime.datetime.now()):
                        MidCloseDate = MidCloseDate + datetime.timedelta(days = 30)
                if((len(InstructorsDF.loc[Index, 'Q11_v2']) < 10) | ('/' in InstructorsDF.loc[Index, 'Q11_v2'])):
                    InstructorsDF.loc[Index, 'Q11_v2'] = FixDates(InstructorsDF.loc[Index, 'Q11_v2'])
                try:
                    PostCloseDate = datetime.datetime.strptime(InstructorsDF.loc[Index, 'Q11_v2'], "%m-%d-%Y")
                except:
                    PostCloseDate = datetime.datetime.now() + datetime.timedelta(days = 60)
                if(PostCloseDate < datetime.datetime.now()):
                    PostCloseDate = PostCloseDate + datetime.timedelta(days = 60)
                CourseYear = PostCloseDate.strftime("%Y")
                if(InstructorsDF.loc[Index, 'Q12'] == 1):
                    CreditOffered = True
                else:
                    CreditOffered = False
                InstructorsDF.loc[Index, 'Q12'] = CreditOffered
                if(pd.notnull(InstructorsDF.loc[Index, 'Q45'])):
                    NumSurveys = int(InstructorsDF.loc[Index, 'Q45'])
                else:
                    NumSurveys = int(InstructorsDF.loc[Index, 'Q40'] + 1)

                Type = int(InstructorsDF.loc[Index, 'Q7'])
                if(Type == 1):
                    Type = 'Intro - Algebra'
                elif(Type == 2):
                    Type = 'Intro - Calculus'
                elif(Type == 3):
                    Type = 'Sophomore'
                elif(Type == 4):
                    Type = 'Junior'
                elif(Type == 5):
                    Type = 'Senior'
                InstructorsDF.loc[Index, 'Q7'] = Type

                SemQuart = int(InstructorsDF.loc[Index, 'Q9'])
                if (SemQuart == 1):
                    SemQuart = "Semesters"
                    Season = int(InstructorsDF.loc[Index, 'Q9a'])
                    if(Season == 1):
                        Season = "Fall"
                    elif(Season == 2):
                        Season = "Spring"
                    elif(Season == 3):
                        Season = "Summer"
                    elif(Season == 4):
                        Season = "Year"
                    InstructorsDF.loc[Index, 'Q9a'] = Season
                elif (SemQuart == 2):
                    SemQuart = "Quarters"
                    Season = int(InstructorsDF.loc[Index, 'Q9b'])
                    if(Season == 1):
                        Season = "Fall"
                    elif(Season == 2):
                        Season = "Winter"
                    elif(Season == 3):
                        Season = "Spring"
                    elif(Season == 4):
                        Season = "Summer"
                    elif(Season == 5):
                        Season = "Year"
                    InstructorsDF.loc[Index, 'Q9b'] = Season
                InstructorsDF.loc[Index, 'Q9'] = SemQuart

                if(InstructorsDF.loc[Index, 'Q61'] == 1): # we're using two versions of the survey now...its up to instructors
                    version = 'PLICSurvey.qsf'
                else:
                    version = 'PLICSurvey_v2.qsf'

                # Make Pre-, Mid-, and Post- surveys, send Pre-Survey, and update Master File with Pre-Survey sent time (if requested)
                PostSurveyID = MakeSurvey(School, CourseNumber, Season, CourseYear, LastName, 'POST', ID, version)
                PostCloseDate = PostCloseDate.strftime("%d-%b-%Y")

                if(NumSurveys == 3):
                    MidSurveyID = MakeSurvey(School, CourseNumber, Season, CourseYear, LastName, 'MID', ID, version)
                    for User in SharedUsers:
                        ShareSurvey(User, MidSurveyID) # share surveys with other interested users, defined in preamble
                    MidCloseDate = MidCloseDate.strftime("%d-%b-%Y")
                    MidSurveyMemo = np.nan
                    MidSurveySent = np.nan
                    MidSurveyReminder = np.nan
                    MidSurveyClosed = np.nan

                if(NumSurveys >= 2):
                    PreSurveyID = MakeSurvey(School, CourseNumber, Season, CourseYear, LastName, 'PRE', ID, version)
                    for User in SharedUsers:
                        ShareSurvey(User, PreSurveyID)
                    ActivateSurvey(PreSurveyID)
                    PreSurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + PreSurveyID
                    SendPreSurvey(ID, Email, FirstName, LastName, CourseName, CourseNumber, PreSurveyURL, PreCloseDate)
                    PreSurveySent = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())
                    PreCloseDate = PreCloseDate.strftime("%d-%b-%Y")
                    PreSurveyReminder = np.nan
                    PreSurveyClosed = np.nan

                    if(NumSurveys == 2):
                        MidSurveyID = np.nan
                        MidCloseDate = np.nan
                        MidSurveyMemo = np.nan
                        MidSurveySent = np.nan
                        MidSurveyReminder = np.nan
                        MidSurveyClosed = np.nan

                elif(NumSurveys == 1):
                    MidSurveyID = np.nan
                    MidCloseDate = np.nan
                    MidSurveyMemo = np.nan
                    MidSurveySent = np.nan
                    MidSurveyReminder = np.nan
                    MidSurveyClosed = np.nan

                    PreSurveyID = np.nan
                    PreCloseDate = np.nan
                    PreSurveySent = np.nan
                    PreSurveyReminder = np.nan
                    PreSurveyClosed = np.nan

                for User in SharedUsers:
                    ShareSurvey(User, PostSurveyID)

                SurveyCreationDate = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())

                # Write all data for new course to Master File for later reference
                csvUpdate = [ID, FirstName, LastName, Email, School, CourseName, CourseNumber, CourseYear, Season, Type, NumStudents, CreditOffered, SurveyCreationDate, NumSurveys, PreCloseDate, MidCloseDate, PostCloseDate, PreSurveyID,
                                PreSurveySent, PreSurveyReminder, PreSurveyClosed, MidSurveyID, MidSurveyMemo, MidSurveySent, MidSurveyReminder, MidSurveyClosed, PostSurveyID, '', '', '', '', '']
                MasterDataWriter.writerow(csvUpdate)

                # create a directory for that term's files if it doesn't exist
                TermDir = "C:/PLIC" + "//" + Season + str(CourseYear) + "Files"
                if not os.path.exists(TermDir):
                    os.mkdir(TermDir, 755)

                # create a directory for that course if it does not already exist
                CourseDir = 	School + '_' + str(CourseNumber) + '_' + LastName + '_' + ID
                CourseDir = TermDir + "//" + CourseDir
                if not os.path.exists(CourseDir):
                    os.mkdir(CourseDir, 755)

                # Individual course info provided by instructor
                InfoDummyDF.loc[[0, Index + 1], :].to_csv(CourseDir + '//' + Season + str(CourseYear) + '_' + School + '_' + str(CourseNumber) + '_' + LastName + '_CourseInfo.csv', index = False)

    os.remove('Course_Information_Survey.csv')

def CourseChangesControl():
    # check the online form for changing dates and update the necessary dates in the Master file
    print("Checking Changes...")
    MasterDF = pd.read_csv('MasterCourseData.csv', skiprows = [0], index_col = 'ID')

    ChangeDates_SurveyID = "SV_cAqEOkCAV8mTNSR"
    DownloadResponses(ChangeDates_SurveyID)
    ChangesDF = pd.read_csv("PLIC_Date_Changes.csv", skiprows = [1, 2])

    NumChanges = len(ChangesDF)

    ChangeLogDF = pd.read_csv('ChangeLog.csv')
    ChangesDF = ChangesDF[(~ChangesDF['ResponseID'].isin(ChangeLogDF['ResponseID'])) & (ChangesDF['Finished'] == 1)] # Get new changes to implement

    with open("ChangeLog.csv",'a') as f:
        ChangeLogWriter = csv.writer(f)

        for Index, Change in ChangesDF.iterrows():
            InstructorID = ChangesDF.loc[Index, 'Q1']
            print(InstructorID)
            # Log the online survey entries in the local copy of changes
            ChangeLogWriter.writerow([ChangesDF.loc[Index, 'ResponseID'], time.strftime("%d-%b-%Y %H:%M:%S", time.localtime()), ChangesDF.loc[Index, 'Q1'], ChangesDF.loc[Index, 'Q2_v2'], ChangesDF.loc[Index, 'Q9_v2'],
                                        ChangesDF.loc[Index, 'Q3_v2'], ChangesDF.loc[Index, 'Q4'], ChangesDF.loc[Index, 'Q8'], ChangesDF.loc[Index, 'Q5']])
            # If any incorrect IDs or dates are entered...move on...otherwise update the Master dataframe
            if(InstructorID not in MasterDF.index):
                continue
            if((pd.notnull(MasterDF.loc[InstructorID, 'Pre-Survey ID'])) & (pd.isnull(MasterDF.loc[InstructorID, 'Pre-Survey Closed'])) & (pd.notnull(ChangesDF.loc[Index, 'Q2_v2']))):
                try:
                    MasterDF.loc[InstructorID, 'Pre-Survey Close Date'] = datetime.datetime.strptime(ChangesDF.loc[Index, 'Q2_v2'], "%m-%d-%Y").strftime("%d-%b-%Y")
                except ValueError:
                    continue

                # Reset reminder email statuses if requested
                if(ChangesDF.loc[Index, 'Q4'] == 1):
                    MasterDF.loc[InstructorID, 'Pre-Survey Reminder'] = np.nan
                elif((ChangesDF.loc[Index, 'Q4'] == 2) and pd.isnull(MasterDF.loc[InstructorID, 'Pre-Survey Reminder'])):
                    MasterDF.loc[InstructorID, 'Pre-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            if((pd.notnull(MasterDF.loc[InstructorID, 'Mid-Survey ID'])) & (pd.isnull(MasterDF.loc[InstructorID, 'Mid-Survey Closed'])) & (pd.notnull(ChangesDF.loc[Index, 'Q9_v2']))):
                try:
                    MasterDF.loc[InstructorID, 'Mid-Survey Close Date'] = datetime.datetime.strptime(ChangesDF.loc[Index, 'Q9_v2'], "%m-%d-%Y").strftime("%d-%b-%Y")
                except ValueError:
                    continue

                if(ChangesDF.loc[Index, 'Q8'] == 1):
                    MasterDF.loc[InstructorID, 'Mid-Survey Reminder'] = np.nan
                elif((ChangesDF.loc[Index, 'Q8'] == 2) and pd.isnull(MasterDF.loc[InstructorID, 'Mid-Survey Reminder'])):
                    MasterDF.loc[InstructorID, 'Mid-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())


            if((pd.isnull(MasterDF.loc[InstructorID, 'Post-Survey Closed'])) & (pd.notnull(ChangesDF.loc[Index, 'Q3_v2']))):
                try:
                    MasterDF.loc[InstructorID, 'Post-Survey Close Date'] = datetime.datetime.strptime(ChangesDF.loc[Index, 'Q3_v2'], "%m-%d-%Y").strftime("%d-%b-%Y")
                except ValueError:
                    continue

                if(ChangesDF.loc[Index, 'Q5'] == 1):
                    MasterDF.loc[InstructorID, 'Post-Survey Reminder'] = np.nan
                elif((ChangesDF.loc[Index, 'Q5'] == 2) and pd.isnull(MasterDF.loc[InstructorID, 'Post-Survey Reminder'])):
                    MasterDF.loc[InstructorID, 'Post-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            # Send email to instructor letting them know that the dates have been changed
            ChangesEmailSend(InstructorID, MasterDF.loc[InstructorID, 'Email'], MasterDF.loc[InstructorID, 'First Name'], MasterDF.loc[InstructorID, 'Last Name'], MasterDF.loc[InstructorID, 'Course Name'],
                                MasterDF.loc[InstructorID, 'Course Number'], MasterDF.loc[InstructorID, 'Pre-Survey Close Date'], MasterDF.loc[InstructorID, 'Mid-Survey Close Date'],
                                MasterDF.loc[InstructorID, 'Post-Survey Close Date'])

    # Write Master dataframe to file
    with open("C:/PLIC/MasterCourseData.csv", 'w') as f:
        MasterDataWriter = csv.writer(f)
        MasterDataWriter.writerows([['Last Accessed:', LastAccess]])
    with open("C:/PLIC/MasterCourseData.csv", 'a') as f:
        MasterDF.to_csv(f, index = True)

    os.remove('PLIC_Date_Changes.csv')

def PreSurveyControl():
    # check current time relative to specified close dates by instructors and send reminders or close the survey as necessary -- pre-survey
    print("Checking Pre-Survey Data...")
    CurrentTime = datetime.datetime.now()
    MasterDF = pd.read_csv("C:/PLIC/MasterCourseData.csv", skiprows = [0])
    for Index, Course in MasterDF.iterrows():
        if((pd.notnull(MasterDF.loc[Index, 'Pre-Survey ID'])) & (pd.isnull(MasterDF.loc[Index, 'Pre-Survey Closed']))):
            # If Pre-Survey not closed, check what time it is and what to do
            PreID = MasterDF.loc[Index, 'Pre-Survey ID']
            SurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + PreID
            PreCloseDate = datetime.datetime.strptime(MasterDF.loc[Index, 'Pre-Survey Close Date'], "%d-%b-%Y")

            if(pd.isnull(MasterDF.loc[Index, 'Pre-Survey Sent'])):
                # Send Pre-Survey if it hasn't been done so already
                SendPreSurvey(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], SurveyURL, PreCloseDate)
                MasterDF.loc[Index, 'Pre-Survey Sent'] = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())

            elif((CurrentTime >= (PreCloseDate - datetime.timedelta(days = 4))) and pd.isnull(MasterDF.loc[Index, 'Pre-Survey Reminder'])):
                # Send Pre-Survey reminder if we haven't already
                NumStudents = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], PreID, DataType = 'NumberOnly')
                if(NumStudents == 0):
                    # If nobody has responded yet, give extra time and send a reminder
                    PreCloseDate = PreCloseDate + datetime.timedelta(days = 3)
                    MasterDF.loc[Index, 'Pre-Survey Close Date'] = PreCloseDate.strftime("%d-%b-%Y")
                    ZeroResponseEmail(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'PRE', SurveyURL, PreCloseDate)
                    MasterDF.loc[Index, 'Pre-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                else:
                    ReminderEmailSend(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'PRE', SurveyURL, PreCloseDate, NumStudents)
                    MasterDF.loc[Index, 'Pre-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            elif(CurrentTime >= (PreCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59))):
                # Close the Pre-Survey
                CloseSurvey(PreID)
                Responses = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], PreID, DataType = 'NumberOnly')
                MasterDF.loc[Index, 'Pre-Survey Closed'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                if(MasterDF.loc[Index, 'Number of Surveys'] == 3):
                    Next = 'MID'
                    NextSurveyClose = datetime.datetime.strptime(MasterDF.loc[Index, 'Mid-Survey Close Date'], "%d-%b-%Y")
                else:
                    Next = 'POST'
                    NextSurveyClose = datetime.datetime.strptime(MasterDF.loc[Index, 'Post-Survey Close Date'], "%d-%b-%Y")
                SendSurveyClose(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], Responses, 'PRE', Next, NextSurveyClose)
    with open("C:/PLIC/MasterCourseData.csv", 'w') as f:
        MasterDataWriter = csv.writer(f)
        MasterDataWriter.writerows([['Last Accessed:', LastAccess]])
    with open("C:/PLIC/MasterCourseData.csv", 'a') as f:
        MasterDF.to_csv(f, index = False)

def MidSurveyControl():
    # check current time relative to specified close dates by instructors and send reminders or close the survey as necessary -- mid-survey
    print("Checking Mid-Survey Data...")
    CurrentTime = datetime.datetime.now()
    MasterDF = pd.read_csv("C:/PLIC/MasterCourseData.csv", skiprows = [0])
    for Index, Course in MasterDF.iterrows():
        if((pd.notnull(MasterDF.loc[Index, 'Mid-Survey ID'])) & (pd.isnull(MasterDF.loc[Index, 'Mid-Survey Closed']))):
            MidID = MasterDF.loc[Index, 'Mid-Survey ID']
            SurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + MidID
            MidCloseDate = datetime.datetime.strptime(MasterDF.loc[Index, 'Mid-Survey Close Date'], "%d-%b-%Y")

            if(pd.isnull(MasterDF.loc[Index, 'Mid-Survey Sent']) and pd.isnull(MasterDF.loc[Index, 'Mid-Survey Memo']) and (CurrentTime >= MidCloseDate - datetime.timedelta(days = 16))):
                SendSurveyMemo(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], MidCloseDate, 'MID')
                MasterDF.loc[Index, 'Mid-Survey Memo'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            if(pd.isnull(MasterDF.loc[Index, 'Mid-Survey Sent'])):
                SendSurvey(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], SurveyURL, MidCloseDate, 'MID')
                MasterDF.loc[Index, 'Mid-Survey Sent'] = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())

            elif((CurrentTime >= (MidCloseDate - datetime.timedelta(days = 4))) and pd.isnull(MasterDF.loc[Index, 'Mid-Survey Reminder'])):
                NumStudents = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], MidID, DataType = 'NumberOnly')
                if(NumStudents == 0):
                    MidCloseDate = MidCloseDate + datetime.timedelta(days = 3)
                    MasterDF.loc[Index, 'Mid-Survey Close Date'] = MidCloseDate.strftime("%d-%b-%Y")
                    ZeroResponseEmail(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'MID', SurveyURL, MidCloseDate)
                    MasterDF.loc[Index, 'Mid-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                else:
                    ReminderEmailSend(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'MID', SurveyURL, MidCloseDate, NumStudents)
                    MasterDF.loc[Index, 'Mid-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            elif(CurrentTime >= (MidCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59))):
                CloseSurvey(MidID)
                Responses = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], MidID, DataType = 'NumberOnly')
                MasterDF.loc[Index, 'Mid-Survey Closed'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                SendSurveyClose(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], Responses, 'MID', 'POST', datetime.datetime.strptime(MasterDF.loc[Index, 'Post-Survey Close Date'], "%d-%b-%Y"))
    with open("C:/PLIC/MasterCourseData.csv", 'w') as f:
        MasterDataWriter = csv.writer(f)
        MasterDataWriter.writerows([['Last Accessed:', LastAccess]])
    with open("C:/PLIC/MasterCourseData.csv", 'a') as f:
        MasterDF.to_csv(f, index = False)

def PostSurveyControl():
    # check current time relative to specified close dates by instructors and send reminders or close the survey as necessary -- post-survey
    print("Checking Post-Survey Data...")
    CurrentTime = datetime.datetime.now()
    MasterDF = pd.read_csv("C:/PLIC/MasterCourseData.csv", skiprows = [0])
    for Index, Course in MasterDF.iterrows():
        if(pd.isnull(MasterDF.loc[Index, 'Post-Survey Closed'])):
            PostID = MasterDF.loc[Index, 'Post-Survey ID']
            SurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + PostID
            PostCloseDate = datetime.datetime.strptime(MasterDF.loc[Index, 'Post-Survey Close Date'], "%d-%b-%Y")

            if(pd.isnull(MasterDF.loc[Index, 'Post-Survey Sent']) and pd.isnull(MasterDF.loc[Index, 'Post-Survey Memo']) and (CurrentTime >= PostCloseDate - datetime.timedelta(days = 16))):
                SendSurveyMemo(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], PostCloseDate, 'POST')
                MasterDF.loc[Index, 'Post-Survey Memo'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            elif((CurrentTime >= PostCloseDate - datetime.timedelta(days = 14)) and pd.isnull(MasterDF.loc[Index, 'Post-Survey Sent'])):
                if(pd.isnull(MasterDF.loc[Index, 'Post-Survey Memo'])):
                    MasterDF.loc[Index, 'Post-Survey Memo'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                ActivateSurvey(PostID)
                SendSurvey(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], SurveyURL, PostCloseDate, 'POST')
                MasterDF.loc[Index, 'Post-Survey Sent'] = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())

            elif((CurrentTime >= (PostCloseDate - datetime.timedelta(days = 4))) and pd.isnull(MasterDF.loc[Index, 'Post-Survey Reminder'])):
                NumStudents = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], PostID, DataType = 'NumberOnly')
                if (NumStudents == 0):
                    PostCloseDate = PostCloseDate + datetime.timedelta(days = 3)
                    MasterDF.loc[Index, 'Post-Survey Close Date'] = PostCloseDate.strftime("%d-%b-%Y")
                    ZeroResponseEmail(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'POST', SurveyURL, PostCloseDate)
                    MasterDF.loc[Index, 'Post-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                else:
                    ReminderEmailSend(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'POST', SurveyURL, PostCloseDate, NumStudents)
                    MasterDF.loc[Index, 'Post-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            elif(CurrentTime >= (PostCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59))):
                CloseSurvey(PostID)
                MasterDF.loc[Index, 'Post-Survey Closed'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
    with open("C:/PLIC/MasterCourseData.csv", 'w') as f:
        MasterDataWriter = csv.writer(f)
        MasterDataWriter.writerows([['Last Accessed:', LastAccess]])
    with open("C:/PLIC/MasterCourseData.csv", 'a') as f:
        MasterDF.to_csv(f, index = False)

def ReportControl():
    # score any surveys that have closed, construct summary reports, and send reports and class lists to instructors as requested
    print("Checking Report Data...")
    MasterDF = pd.read_csv("C:/PLIC/MasterCourseData.csv", skiprows = [0])
    for Index, Course in MasterDF.iterrows():
        if(pd.isnull(MasterDF.loc[Index, 'Report Sent']) and pd.notnull(MasterDF.loc[Index, 'Post-Survey Closed'])):
            Path = "C:/PLIC/" + MasterDF.loc[Index, 'Season'] + str(MasterDF.loc[Index, 'Course Year']) + "Files/" + MasterDF.loc[Index, 'School'] + '_' + str(MasterDF.loc[Index, 'Course Number']) + '_' + MasterDF.loc[Index, 'Last Name'] + '_' + MasterDF.loc[Index, 'ID']
            os.chdir(Path)
            DownloadResponses(MasterDF.loc[Index, 'Post-Survey ID'])
            PostSurveyName = GetSurveyName(MasterDF.loc[Index, 'Post-Survey ID'])
            PostDF = pd.read_csv(PostSurveyName + '.csv', skiprows = [1, 2]) # rows 1 and 2 just have descriptive text
            MasterDF.loc[Index, 'Report Sent'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
            if PostDF.empty:
                continue
            NumSurveys = MasterDF.loc[Index, 'Number of Surveys']
            PDFName = Path + "/" + MasterDF.loc[Index, 'Season'] + str(MasterDF.loc[Index, 'Course Year']) + '_' + MasterDF.loc[Index, 'School'] + '_' + str(MasterDF.loc[Index, 'Course Number']) + '_' + MasterDF.loc[Index, 'Last Name'] + '_Report'
            print(PDFName)

            if('Q152_21' not in PostDF.columns):
                if(NumSurveys >= 2): # all these conditions just handle various different combinations of three surveys or less
                    DownloadResponses(MasterDF.loc[Index, 'Pre-Survey ID'])
                    PreSurveyName = GetSurveyName(MasterDF.loc[Index, 'Pre-Survey ID'])
                    PreDF = pd.read_csv(PreSurveyName + '.csv', skiprows = [1, 2])
                    if(NumSurveys == 3):
                        DownloadResponses(MasterDF.loc[Index, 'Mid-Survey ID'])
                        MidSurveyName = GetSurveyName(MasterDF.loc[Index, 'Mid-Survey ID'])
                        MidDF = pd.read_csv(MidSurveyName + '.csv', skiprows = [1, 2])
                        if((len(PreDF.index) >= 3) and (len(MidDF.index) >= 3)): # if fewer than 3 students took an assessment we don't send the data
                            ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], MasterDF.loc[Index, 'ID'], 'C:/PLIC/', PRE = PreDF, MID = MidDF, POST = PostDF)
                        elif((len(PreDF.index) >= 3) and (len(MidDF.index) < 3)):
                            ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], MasterDF.loc[Index, 'ID'], 'C:/PLIC/', PRE = PreDF, POST = PostDF)
                        elif((len(PreDF.index) < 3) and (len(MidDF.index) >= 3)):
                            ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], MasterDF.loc[Index, 'ID'], 'C:/PLIC/', MID = MidDF, POST = PostDF)
                        else:
                            ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], MasterDF.loc[Index, 'ID'], 'C:/PLIC/', POST = PostDF)
                    elif(len(PreDF.index) >= 3):
                        ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], MasterDF.loc[Index, 'ID'], 'C:/PLIC/', PRE = PreDF, POST = PostDF)
                    else:
                        ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], MasterDF.loc[Index, 'ID'], 'C:/PLIC/', POST = PostDF)
                else:
                    ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], MasterDF.loc[Index, 'ID'], 'C:/PLIC/', POST = PostDF)

            os.chdir(Path)
            if(MasterDF.loc[Index, 'Credit Offered']): # If the instructor is offering credit include a list of names and IDs of those who completed each of the surveys
                PostNamesDF = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'Post-Survey ID'], DataType = 'Names')
                PostNamesDF.columns = ['Post-Survey IDs', 'Post-Survey Last Names', 'Post-Survey First Names']
                if((NumSurveys >= 2) and (len(PreDF.index) >= 3)):
                    PreNamesDF = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'Pre-Survey ID'], DataType = 'Names')
                    PreNamesDF.columns = ['Pre-Survey IDs', 'Pre-Survey Last Names', 'Pre-Survey First Names']
                    if((NumSurveys == 3) and (len(MidDF.index) >= 3)):
                        MidNamesDF = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'Mid-Survey ID'], DataType = 'Names')
                        MidNamesDF.columns = ['Mid-Survey IDs', 'Mid-Survey Last Names', 'Mid-Survey First Names']
                        NamesDF = PreNamesDF.merge(MidNamesDF, how = 'outer', left_on = ['Pre-Survey Last Names', 'Pre-Survey First Names'], right_on = ['Mid-Survey Last Names', 'Mid-Survey First Names'])
                        NamesDF = NamesDF.merge(PostNamesDF, how = 'outer', left_on = ['Pre-Survey Last Names', 'Pre-Survey First Names'], right_on = ['Post-Survey Last Names', 'Post-Survey First Names'])
                    else:
                        NamesDF = PreNamesDF.merge(PostNamesDF, how = 'outer', left_on = ['Pre-Survey Last Names', 'Pre-Survey First Names'], right_on = ['Post-Survey Last Names', 'Post-Survey First Names'])
                    if(PreDF.empty):
                        NamesDF = NamesDF.drop(columns = ['Pre-Survey IDs', 'Pre-Survey Last Names', 'Pre-Survey First Names'])
                else:
                    NamesDF = PostNamesDF.copy()
                NamesDF = NamesDF.fillna('')
                NamesDF['PostName'] = NamesDF['Post-Survey Last Names'] + NamesDF['Post-Survey First Names']
                if('Pre-Survey Last Names'in NamesDF.columns):
                    NamesDF['PreName'] = NamesDF['Pre-Survey Last Names'] + NamesDF['Pre-Survey First Names']
                    NamesDF = NamesDF.sort_values(by = ['PostName', 'PreName'])
                    NamesDF = NamesDF.drop(labels = ['PreName', 'PostName'], axis = 1)
                else:
                    NamesDF = NamesDF.sort_values(by = 'PostName')
                    NamesDF = NamesDF.drop(labels = 'PostName', axis = 1)
                NamesFileName = MasterDF.loc[Index, 'Season'] + str(MasterDF.loc[Index, 'Course Year']) + '_' + MasterDF.loc[Index, 'School'] + '_' + str(MasterDF.loc[Index, 'Course Number']) +'_' + MasterDF.loc[Index, 'Last Name'] + '_Names.csv'
                NamesDF.to_csv(NamesFileName, index = False)
                if('Q152_21' not in PostDF.columns):
                    SendReport(MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], PDFName + '.pdf', CreditOffered = True, NamesFile = NamesFileName)
                else:
                    SendReport(MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], PDFName + '.pdf', CreditOffered = True, NamesFile = NamesFileName, NewFormatMessage = True)
            else:
                SendReport(MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], PDFName + '.pdf', NewFormatMessage = True)
            MasterDF.loc[Index, 'Report Sent'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
    with open("C:/PLIC/MasterCourseData.csv", 'w') as f:
        MasterDataWriter = csv.writer(f)
        MasterDataWriter.writerows([['Last Accessed:', LastAccess]])
    with open("C:/PLIC/MasterCourseData.csv", 'a') as f:
        MasterDF.to_csv(f, index = False)

def MakeSurvey(Institution, Number, Semester, Year, InstructorLast, SurveyType, Instructor_ID, version):
    """Make a Qualtrics surveys.

    Keyword arguments:
    Institution -- name of institution administering the survey
    Number -- course number of the course where the survey is administered
    Semester -- semester that a survey was administered
    Year -- year that the survey is administered
    InstructorLast -- instructor's last name
    SurveyType -- which Bio-MAPS assessment to create a survey for
    Instructor_ID -- ResponseID on the course information survey for the class
    version -- which version of the PLIC to use
    """

    baseURL = "https://{0}.qualtrics.com/API/v3/surveys".format(DataCenter)
    headers = {
        "x-api-token": apiToken,
        }

    files = {
        'file': (version, open(version, 'rb'), 'application/vnd.qualtrics.survey.qsf')
        }

    data = {
        "name": Semester + str(Year) + '_' + Institution + '_' + str(Number) +'_' + InstructorLast + '_' + SurveyType + '_' + Instructor_ID,
        }
    response = requests.post(baseURL, files=files, data=data, headers=headers)
    StringResponse = json.dumps(response.json())
    jsonResponse = json.loads(StringResponse)
    SurveyID = jsonResponse['result']['id']
    return SurveyID

def ActivateSurvey(SurveyID):
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
        "isActive": True,
        }

    response = requests.put(baseUrl, json=data, headers=headers)

def CloseSurvey(SurveyID):
    # combine with ActivateSurvey in future versions
    """Close a Qualtrics survey.

    Keyword arguments:
    SurveyID -- ID of the survey to close
    """

    baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(DataCenter, SurveyID)
    headers = {
        "content-type": "application/json",
        "x-api-token": apiToken,
        }

    data = {
        "isActive": False,
        }

    response = requests.put(baseUrl, json=data, headers=headers)

def SendPreSurvey(ID, InstructorEmail, InstructorFirst, InstructorLast, Course, Code, SurveyLink, SurveyCloseDate):
    # send pre-survey to instructor
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = InstructorEmail
    msg['Cc'] = CPERLEmail
    msg['Subject'] = " PLIC Pre-Instruction Survey Link"

    SurveyCloseDate = (SurveyCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

    text = """
            Dear Dr. {First} {Last},\n \n

            Thank you again for completing the course information survey. Below is
            the link for the pre-instruction survey for your course, {Course} ({Code}): \n \n
            {Survey}\n \n
            Please share this link with your students on the first day of class. \n \n
            In order to get the best data, we recommend that students complete the
            PLIC within the first week of class. Accordingly, we recommend that
            you distribute the link to your students at least 7 days before the close
            date listed below.  \n \n
            The date the survey is currently set to close is: \n
            {Close} EST\n
            If you would like to change the dates that the PRE- and/or POST-surveys
            will stop accepting responses from students, please complete the form here
            with your unique ID({Identifier}):\n\n

            {ChangeURL}\n\n

            Let us know by replying to this email if you have any questions about
            this process. \n \n

            Thank you, \n
            Cornell Physics Education Research Lab \n
            This message was sent by an automated system. \n
            """.format(Close = SurveyCloseDate, First = InstructorFirst, Last = InstructorLast, Survey = SurveyLink, Course = Course.replace("_", " "), Code = Code, Identifier = ID, ChangeURL = ChangeURL)

    html = """\
	<html>
	  <head></head>
	  <body>
		<p>Dear Dr. {First} {Last},<br><br>

		   Thank you again for completing the course information survey. Below is
           the link for the pre-instruction survey for your course, {Course} ({Code}):<br><br>
		   {Survey}<br><br>
		   Please share this link with your students on the first day of class. <br><br>
		   In order to get the best data, we recommend that students complete the
           PLIC within the first week of class. Accordingly, we recommend that
           you distribute the link to your students at least 7 days before the close
           date listed below.<br><br>
		   The date the survey is currently set to close is: <br>
		   {Close} EST<br>
           If you would like to change the dates that the PRE- and/or POST-surveys
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):<br><br>

           {ChangeURL}<br><br>

           Let us know by replying to this email if you have any questions about
           this process. <br><br>

		   Thank you,<br>
           Cornell Physics Education Research Lab <br>
		   This message was sent by an automated system.
		</p>
	  </body>
	</html>
	""".format(Close = SurveyCloseDate, First = InstructorFirst, Last = InstructorLast, Survey = SurveyLink, Course = Course.replace("_", " "), Code = Code, Identifier = ID, ChangeURL = ChangeURL)


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
    server.sendmail(CPERLEmail, [InstructorEmail, CPERLEmail], msg.as_string())
    server.quit()

def SendSurveyClose(ID, InstructorEmail, InstructorFirst, InstructorLast, Course, Code, NumberResponses, PreMid, MidPost, SurveyClose):
    # send notice to instructor that a survey has closed and remind them when the next survey will be active
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = InstructorEmail
    msg['Subject'] = "PLIC {}-Instruction Survey Now Closed".format(PreMid)

    PostSurveyOpen = (SurveyClose - datetime.timedelta(days = 14)).strftime("%d-%b-%Y %H:%M:%S")

    text = """
            Dear Dr. {First} {Last},\n \n

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
            this process. \n \n

            Thank you, \n
            Cornell Physics Education Research Lab \n
            This message was sent by an automated system. \n
            """.format(First = InstructorFirst, Last = InstructorLast, Survey = PreMid, Course = Course.replace("_", " "), Code = Code, Num = NumberResponses, NextSurvey = MidPost, TimeOpen = PostSurveyOpen, Identifier = ID, ChangeURL = ChangeURL)

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
            with your unique ID({Identifier}):\n\n

            {ChangeURL}\n\n

            Let us know by replying to this email if you have any questions about
            this process. \n \n

		   Thank you,<br>
           Cornell Physics Education Research Lab <br>
		   This message was sent by an automated system.
		</p>
	  </body>
	</html>
	""".format(First = InstructorFirst, Last = InstructorLast, Survey = PreMid, Course = Course.replace("_", " "), Code = Code, Num = NumberResponses, NextSurvey = MidPost, TimeOpen = PostSurveyOpen, Identifier = ID, ChangeURL = ChangeURL)


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
    server.sendmail(CPERLEmail, InstructorEmail, msg.as_string())
    server.quit()

def ZeroResponseEmail(ID, InstructorFirst, InstructorLast, InstructorEmail, CourseName, Code, SurveyType, SurveyLink, SurveyCloseDate):
    # send a reminder to instructors letting them know that no one has responded to the survey yet
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = InstructorEmail
    msg['Subject'] = "There have been zero responses to the PLIC"

    SurveyCloseDate = (SurveyCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

    # Create the body of the message (a plain-text and an HTML version).
    text = """
           Dear Dr. {First} {Last},\n \n

           This is a reminder from the CPERL team about the PLIC {Survey}-survey.
           Currently there are no responses to the survey for your course: {Course} ({Code}). \n \n
           We have extended the close date for the survey to: {Close} EST.\n \n
           If you have not already done so, please send out the link to your class. \n \n
           Here is another link to the survey: \n
           {Link} \n \n

           If you would like to change the date that the survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):\n\n

           {ChangeURL}\n\n

           Let us know by replying to this email if you have any questions about
           this process. \n \n

           Thank you, \n
           Cornell Physics Education Research Lab \n
           This message was sent by an automated system. \n
           """.format(First = InstructorFirst, Last = InstructorLast, Survey = SurveyType, Course = CourseName.replace("_", " "), Code = Code, Close = SurveyCloseDate, Link = SurveyLink, Identifier = ID, ChangeURL = ChangeURL)

    html = """\
    <html>
      <head></head>
      <body>
        Dear Dr. {First} {Last},<br> <br>

           This is a reminder from the CPERL team about the PLIC {Survey}-survey.
           Currently there are no responses to the survey for your course: {Course} ({Code}) <br> <br>
           We have extended the close date for the survey to: {Close} EST. <br> <br>
           If you have not already done so, please send out the link to your class. <br> <br>
           Here is another link to the survey: <br>
           {Link} <br> <br>

           If you would like to change the date that the survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):<br><br>

           {ChangeURL}<br><br>

           Let us know by replying to this email if you have any questions about
           this process. <br><br>

           Thank you, <br>
           Cornell Physics Education Research Lab <br> <br>
           This message was sent by an automated system. <br>
        </p>
      </body>
    </html>
    """.format(First = InstructorFirst, Last = InstructorLast, Survey = SurveyType, Course = CourseName.replace("_", " "), Code = Code, Close = SurveyCloseDate, Link = SurveyLink, Identifier = ID, ChangeURL = ChangeURL)

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
    server.sendmail(CPERLEmail, InstructorEmail, msg.as_string())
    server.quit()

def ReminderEmailSend(ID, InstructorFirst, InstructorLast, InstructorEmail, CourseName, Code, SurveyType, SurveyLink, SurveyCloseDate, NumResponses):
    # send an email to instructors reminding them about the survey and letting them know how many students have responded so far
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = InstructorEmail
    msg['Subject'] = "Reminder for the PLIC survey"

    SurveyCloseDate = (SurveyCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

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
		   """.format(First = InstructorFirst, Last = InstructorLast, Survey = SurveyType, Close = SurveyCloseDate, Link = SurveyLink, Responses = NumResponses, Course = CourseName.replace("_", " "), Code = Code, Identifier = ID, ChangeURL = ChangeURL)

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
    """.format(First = InstructorFirst, Last = InstructorLast, Survey = SurveyType, Close = SurveyCloseDate, Link = SurveyLink, Responses = NumResponses, Course = CourseName.replace("_", " "), Code = Code, Identifier = ID, ChangeURL = ChangeURL)

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
    server.sendmail(CPERLEmail, InstructorEmail, msg.as_string())
    server.quit()

def SendSurveyMemo(ID, InstructorFirst, InstructorLast, InstructorEmail, CourseName, Code, SurveyCloseDate, MidPost):
    # send a notice to instructors that their next survey will go active soon
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = InstructorEmail
    msg['Subject'] = "PLIC {}-Survey Memo".format(MidPost)

    SurveyOpenDate = (SurveyCloseDate - datetime.timedelta(days = 14)).strftime("%d-%b-%Y %H:%M:%S")
    SurveyCloseDate = (SurveyCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

    # Create the body of the message (a plain-text and an HTML version).
    text = """
           Dear Dr. {First} {Last},\n \n

           Thank you again for participating in the PLIC. You will receive the link
           to the {Survey}-instruction survey for your course, {Course} ({Code}) on the
           following date:\n
           {Open} EST\n
           This link will remain active remain active until: \n
           {Close} EST\n
           If you would like to change the date that the post-survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):\n\n

           {ChangeURL}\n\n

           Let us know by replying to this email if you have any questions about
           this process. \n \n

           Thank you, \n
           Cornell Physics Education Research Lab \n \n
           This message was sent by an automated system. \n
           """.format(First = InstructorFirst, Last = InstructorLast, Survey = MidPost, Course = CourseName.replace("_", " "), Code = Code, Open = SurveyOpenDate, Close = SurveyCloseDate, Identifier = ID, ChangeURL = ChangeURL)

    html = """\
    <html>
      <head></head>
      <body>
        <p>Dear Dr. {First} {Last},<br><br>

           Thank you again for participating in the PLIC. You will receive the link
           to the {Survey}-instruction survey for your course, {Course} ({Code}) on the
           following date:<br>
           {Open} EST<br>
           This link will remain active remain active until: <br>
           {Close} EST<br>
           If you would like to change the date that the post-survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):<br><br>

           {ChangeURL}<br><br>

           Let us know by replying to this email if you have any questions about
           this process. <br><br>

           Thank you,<br>
           Cornell Physics Education Research Lab <br> <br>
           This message was sent by an automated system.
        </p>
      </body>
    </html>
    """.format(First = InstructorFirst, Last = InstructorLast, Survey = MidPost, Course = CourseName.replace("_", " "), Code = Code, Open = SurveyOpenDate, Close = SurveyCloseDate, Identifier = ID, ChangeURL = ChangeURL)

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
    server.sendmail(CPERLEmail, InstructorEmail, msg.as_string())
    server.quit()


def SendSurvey(ID, InstructorFirst, InstructorLast, InstructorEmail, CourseName, Code, SurveyLink, SurveyCloseDate, MidPost):
    # send mid- or post-survey to instructors
    # combine with send pre-survey in future versions
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = InstructorEmail
    msg['Cc'] = CPERLEmail
    msg['Subject'] = "PLIC {}-Survey link".format(MidPost)

    SurveyCloseDate = (SurveyCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

    # Create the body of the message (a plain-text and an HTML version).
    text = """
		   Dear Dr. {First} {Last},\n \n

		   Thank you again for participating in the PLIC. Below is the link to the {Survey}-instruction
           survey for your course, {Course} ({Code}):\n \n
		   {SurveyLink}\n \n
		   Please share this link with your students at least 7 days before the close
           date listed below. \n \n
		   This link is currently active and will remain active until: \n
		   {Close} EST\n
           If you would like to change the date that the post-survey
           will stop accepting responses from students, please complete the form here
           with your unique ID({Identifier}):\n\n

           {ChangeURL}\n\n

           Let us know by replying to this email if you have any questions about
           this process. \n \n

		   Thank you, \n
		   Cornell Physics Education Research Lab \n \n
		   This message was sent by an automated system. \n
		   """.format(First = InstructorFirst, Last = InstructorLast, Survey = MidPost, Course = CourseName.replace("_", " "), Code = Code, SurveyLink = SurveyLink, Close = SurveyCloseDate, Identifier = ID, ChangeURL = ChangeURL)

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
		   Cornell Physics Education Research Lab <br> <br>
		   This message was sent by an automated system.
        </p>
	  </body>
    </html>
    """.format(First = InstructorFirst, Last = InstructorLast, Survey = MidPost, Course = CourseName.replace("_", " "), Code = Code, SurveyLink = SurveyLink, Close = SurveyCloseDate, Identifier = ID, ChangeURL = ChangeURL)

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
    server.sendmail(CPERLEmail, [InstructorEmail, CPERLEmail], msg.as_string())
    server.quit()

def SendReport(InstructorFirst, InstructorLast, InstructorEmail, CourseName, Code, ReportFile, CreditOffered = False, NamesFile = None, NewFormatMessage = False):
    # send a report of summary statistics with a list of students who completed the survey
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = InstructorEmail
    #msg['To'] = CPERLEmail
    msg['Cc'] = CPERLEmail
    msg['Subject'] = "PLIC Report"

    if(not NewFormatMessage):
    	# Create the body of the message (a plain-text and an HTML version).
        text = """
    		   Dear Dr. {First} {Last},\n \n

    		   Thank you again for participating in the PLIC. Please find attached a copy of the report summarizing the PLIC
    		   results for your course, {Course} ({Code}). Additionally, if you indicated to us that you are offering students credit
               for completing the survey we have included a CSV file with their names here.\n\n
    		   We are continuing to test and improve our new report generation system, so please let us know by replying to this
    		   email if you have any questions, comments, or suggestions regarding this new report format.\n \n

    		   Thank you, \n
    		   Cornell Physics Education Research Lab \n \n
    		   This message was sent by an automated system. \n
    		   """.format(First = InstructorFirst, Last = InstructorLast, Course = CourseName.replace("_", " "), Code = Code)

        html = """\
    	<html>
    	  <head></head>
    	  <body>
    		<p>Dear Dr. {First} {Last},<br><br>
    		   Thank you again for participating in the PLIC. Please find attached a copy of the report summarizing the PLIC
    		   results for your course, {Course} ({Code}). Additionally, if you indicated to us that you are offering students credit
               for completing the survey we have included a CSV file with their names here.<br><br>
    		   We are continuing to test and improve our new report generation system, so please let us know by replying to this
    		   email if you have any questions, comments, or suggestions regarding this new report format. <br><br>

    		   Thank you,<br>
    		   Cornell Physics Education Research Lab<br> <br>
    		   This message was sent by an automated system.
    		</p>
    	  </body>
    	</html>
    	""".format(First = InstructorFirst, Last = InstructorLast, Course = CourseName.replace("_", " "), Code = Code)
    else:
    	# Create the body of the message (a plain-text and an HTML version).
        text = """
    		   Dear Dr. {First} {Last},\n \n

    		   Thank you again for participating in the PLIC. We are currently analyzing data collected with this new format
               and developing a scoring method. We will share results from your class with you as soon as we have finished
               that analysis. If you indicated to us that you are offering students credit for completing the survey we
               have included a CSV file with their names here.\n\n

               We are continuing to test and improve our new report generation system, so please let us know by replying to this
    		   email if you have any questions, comments, or suggestions regarding this new report format.\n \n

    		   Thank you, \n
    		   Cornell Physics Education Research Lab \n \n
    		   This message was sent by an automated system. \n
    		   """.format(First = InstructorFirst, Last = InstructorLast)

        html = """\
    	<html>
    	  <head></head>
    	  <body>
    		<p>Dear Dr. {First} {Last},<br><br>
    		   Thank you again for participating in the PLIC. We are currently analyzing data collected with this new format
               and developing a scoring method. We will share results from your class with you as soon as we have finished
               that analysis. If you indicated to us that you are offering students credit for completing the survey we
               have included a CSV file with their names here.<br><br>
    		   We are continuing to test and improve our new report generation system, so please let us know by replying to this
    		   email if you have any questions, comments, or suggestions regarding this new report format. <br><br>

    		   Thank you,<br>
    		   Cornell Physics Education Research Lab<br> <br>
    		   This message was sent by an automated system.
    		</p>
    	  </body>
    	</html>
    	""".format(First = InstructorFirst, Last = InstructorLast)


    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    if(not NewFormatMessage):
        f_pdf = open(ReportFile, 'rb')
        att_pdf = MIMEApplication(f_pdf.read(), _subtype = "pdf")
        f_pdf.close()
        att_pdf.add_header('Content-Disposition', 'attachment', filename = ReportFile)
        msg.attach(att_pdf)

    if(CreditOffered == True):
        f_csv = open(NamesFile, 'rb')
        att_csv = MIMEApplication(f_csv.read(), _subtype="csv")
        f_csv.close()
        att_csv.add_header('Content-Disposition', 'attachment', filename = NamesFile)
        msg.attach(att_csv)

    server = smtplib.SMTP(host = 'smtp.office365.com', port = 587)
    server.starttls()
    server.login(UserEmail, EmailPassword)
    server.sendmail(CPERLEmail, [InstructorEmail, CPERLEmail], msg.as_string())
    #server.sendmail(CPERLEmail, CPERLEmail, msg.as_string())
    server.quit()

def ChangesEmailSend(ID, InstructorEmail, InstructorFirst, InstructorLast, CourseName, Code, PreClose, MidClose, PostClose):
    # when instructors request to change the close date of their survey, send an email confirmation
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Changes to Survey Dates"
    msg['From'] = CPERLEmail
    msg['To'] = InstructorEmail

    if(pd.notnull(PreClose)):
        PreClose = datetime.datetime.strptime(PreClose, "%d-%b-%Y")
        PreClose = (PreClose + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")
    else:
        PreClose = 'Not Available'

    if(pd.notnull(MidClose)):
        MidClose = datetime.datetime.strptime(MidClose, "%d-%b-%Y")
        MidClose = (MidClose + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")
    else:
        MidClose = 'Not Available'

    PostClose = datetime.datetime.strptime(PostClose, "%d-%b-%Y")
    PostClose = (PostClose + datetime.timedelta(hours = 23, minutes = 59, seconds = 59)).strftime("%d-%b-%Y %H:%M:%S")

	# Create the body of the message (a plain-text and an HTML version).
    text = """
		   Dear Dr. {First} {Last},\n \n

		   Thank you again for participating in the PLIC. Changes were recently made to the pre- and/or post-survey close dates
           for your class, {Course} ({Code}). These surveys are currently set to close for students at the following times:\n\n

           PRE -- {PreClose}\n
           MID -- {MidClose}\n
           POST -- {PostClose}\n\n

           If you would like to change these dates again, please fill out the form again with your unique ID ({Identifier}):\n\n
           {ChangeURL}\n\n


		   Thank you, \n
		   Cornell Physics Education Research Lab \n \n
		   This message was sent by an automated system. \n
		   """.format(First = InstructorFirst, Last = InstructorLast, Course = CourseName.replace("_", " "), Code = Code, PreClose = PreClose, MidClose = MidClose, PostClose = PostClose, Identifier = ID, ChangeURL = ChangeURL)

    html = """\
	<html>
	  <head></head>
	  <body>
		<p>Dear Dr. {First} {Last},<br><br>

		   Thank you again for participating in the PLIC. Changes were recently made to the pre- and/or post-survey close dates
           for your class, {Course} ({Code}). These surveys are currently set to close for students at the following times:<br><br>

           PRE -- {PreClose}<br>
           MID -- {MidClose}<br>
           POST -- {PostClose}<br><br>

           If you would like to change these dates again, please fill out the form again with your unique ID ({Identifier}):<br><br>
           {ChangeURL}<br><br>


		   Thank you, <br>
		   Cornell Physics Education Research Lab <br><br>
		   This message was sent by an automated system. <br>
		</p>
	  </body>
	</html>
   """.format(First = InstructorFirst, Last = InstructorLast, Course = CourseName.replace("_", " "), Code = Code, PreClose = PreClose, MidClose = MidClose, PostClose = PostClose, Identifier = ID, ChangeURL = ChangeURL)


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
    server.sendmail(CPERLEmail, InstructorEmail, msg.as_string())
    server.quit()

def SendStatusEmail():
    # send email to admin account confirming that things are running okay
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "PLIC Automation Status"
    msg['From'] = CPERLEmail
    msg['To'] = CPERLEmail

    StatusTime = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())

    # Create the body of the message (a plain-text and an HTML version).
    text = """
		   Hey there,\n\n

           Everything's running nicely as of {CurrentTime}. \n\n

		   This message was sent by an automated system. \n
		   """.format(CurrentTime = StatusTime)

    html = """\
    <html>
	  <head></head>
	  <body>
        <p>Hey there,<br><br>

            Everything's running nicely as of {CurrentTime}.\n\n

		   This message was sent by an automated system.
        </p>
	  </body>
    </html>
    """.format(CurrentTime = StatusTime)

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
    server.quit()

def GetResponseData(SchoolName, CourseNumber, InstructorName, Semester, Year, ResponseID, SurveyID, DataType):
    """Download responses to survey from Qualtrics.

    Keyword arguments:
    SchoolName -- name of institution administering the survey
    CourseNumber -- course number where survey is administered
    InstructorName -- instructor's last name
    Semester -- semester that the survey was administered
    Year -- year that the survey was administered
    ResponseID -- ResponseID from the course information survey for the class
    SurveyID -- ID of survey for which data is requested
    DataType -- get names or numbers
    """

    path = "C:/PLIC/" + Semester + str(Year) + "Files/" + SchoolName + '_' + str(CourseNumber) + '_' + InstructorName + '_' + ResponseID

    os.chdir(path)
    DownloadResponses(SurveyID)
    Survey_Name = GetSurveyName(SurveyID)
    StudentDF = pd.read_csv(Survey_Name + '.csv', skiprows = [1, 2])

    if(DataType == 'NumberOnly'):
        NumStudents = len(StudentDF.index)
        return NumStudents

    elif(DataType == 'Names'):
        NamesDF = StudentDF.loc[:, ['Q5a', 'Q5b', 'Q5c']].dropna(how = 'all')
        NamesDF = NamesDF.reset_index(drop = True)
        NCNamesDF = StudentDF.loc[:, ['QNC1a', 'QNC1b', 'QNC1c']].dropna(how = 'all')
        NCNamesDF = NCNamesDF.reset_index(drop = True)
        NCNamesDF.columns = ['Q5a', 'Q5b', 'Q5c']
        NamesDF = pd.concat([NamesDF, NCNamesDF], join = 'inner')
        NamesDF = NamesDF.reset_index(drop = True)
        NamesDF = NamesDF.replace(1, '')
        NamesDF = NamesDF.apply(lambda x: x.astype(str).str.lower())
        return NamesDF

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

def DownloadResponses(SurveyID):
    """Download responses to a Qualtrics survey.

    Keyword arguments:
    SurveyID -- ID of survey
    """

    # Setting static parameters
    FileFormat = "csv"

    requestCheckProgress = 0
    headers = {
        "content-type": "application/json",
        "x-api-token": apiToken,
        }

    # Step 1: Creating Data Export
    downloadRequestUrl = baseURL
    downloadRequestPayload = '{"format":"' + FileFormat + '","surveyId":"' + SurveyID + '"}'
    downloadRequestResponse = requests.request("POST", downloadRequestUrl, data=downloadRequestPayload, headers=headers)
    progressId = downloadRequestResponse.json()["result"]["id"]

    # Step 2: Checking on Data Export Progress and waiting until export is ready
    while requestCheckProgress < 100:
      requestCheckUrl = baseURL + progressId
      requestCheckResponse = requests.request("GET", requestCheckUrl, headers=headers)
      requestCheckProgress = requestCheckResponse.json()["result"]["percentComplete"]

    # Step 3: Downloading file
    requestDownloadUrl = baseURL + progressId + '/file'
    requestDownload = requests.request("GET", requestDownloadUrl, headers=headers, stream=True)

    # Step 4: Unziping file
    with open("RequestFile.zip", "wb") as f:
        for chunk in requestDownload.iter_content(chunk_size=1024):
          f.write(chunk)
    try:
        zipfile.ZipFile("RequestFile.zip").extractall()
        os.remove("RequestFile.zip")
    except zipfile.BadZipfile:
        print("Bad Zip File, trying again...")
        os.remove("RequestFile.zip")
        DownloadResponses(SurveyID)

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

    x = requests.post('https://{0}.qualtrics.com/API/v3/surveys/{1}/permissions/collaborations'.format(DataCenter, SurveyID), headers=headers, data=json.dumps(data))

def FixDates(Date):
    """Do some date processing.

    Keyword arguments:
    Date -- a string representing a date
    """


    Dates = re.findall(r'[0-9]+', Date)
    if(len(Dates[0]) < 2):
        Dates[0] = '0' + str(Dates[0])
    if(len(Dates[1]) < 2):
        Dates[1] = '0'+ str(Dates[1])
    if(len(Dates[2]) < 4):
        Dates[2] = '20'+ str(Dates[2])
    NewDate = Dates[0] + '-' + Dates[1] + '-' + Dates[2]
    return NewDate

if __name__ == '__main__':
	main()
