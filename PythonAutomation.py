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
# apiToken = API token for communicating with qualtrics
# SharedCole = User Id for a shared user
# SharedKatherine = User Id for a shared user
# SharedUsers = [SharedCole, SharedKatherine] # Users to share surveys with in Qualtrics from main account
DataCenter = 'cornell'
baseURL = "https://{0}.qualtrics.com/API/v3/responseexports/".format(DataCenter)
ChangeURL = "https://{0}.qualtrics.com/jfe/form/SV_9QDl20NjVC3w0uN".format(DataCenter)

CPERLEmail = 'cperl@cornell.edu' # Shared CPERL email address
UserEmail = 'as-phy-edresearchlab@cornell.edu' # User email address
# EmailPassword = User password

# Main Exceution body which repaets every hour
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

# Check information provided online by instructors
def InstructorSurveyControl():
    print("Checking CIS...")
    os.chdir("C:/PLIC") # Main Survey Directory
    with open("MasterCourseData.csv",'r', newline = '\n') as f: # Main Course Information Data
        MasterData = list(csv.reader(f))
        NumRows = len(MasterData)
        global LastAccess
        LastAccess = time.strftime("%d-%b-%Y %H:%M:%S %Z",time.localtime()) # Update last access time to current time
        MasterData[0][1] = LastAccess

    with open("MasterCourseData.csv",'w') as f: # Main Course Information Data
        FileWriter = csv.writer(f)
        FileWriter.writerows(MasterData)

    SurveyID = "SV_5ouHoTGEF5FBqxD" # Instructor survey ID
    DownloadResponses(SurveyID) # Course Information Survey downloaded as Course_Information_Survey.csv (or whatever name is used in qualtrics)

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

                # Parse data from Course Information Survey to fill Master Data File
                # Use Regex to replace any non-alphanumeric characters with underscores...cause instructors fill forms with weird stuff
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
                    PreCloseDate = datetime.datetime.strptime(InstructorsDF.loc[Index, 'Q10_v2'], "%m-%d-%Y")
                    if(PreCloseDate < datetime.datetime.now()): # If the date they enter is from the middle ages, set the close dates to something datetime can read
                        PreCloseDate = datetime.datetime.now()
                if(pd.notnull(InstructorsDF.loc[Index, 'Q41_v2'])):
                    if((len(InstructorsDF.loc[Index, 'Q41_v2']) < 10) | ('/' in InstructorsDF.loc[Index, 'Q41_v2'])):
                        InstructorsDF.loc[Index, 'Q41_v2'] = FixDates(InstructorsDF.loc[Index, 'Q41_v2'])
                    MidCloseDate = datetime.datetime.strptime(InstructorsDF.loc[Index, 'Q41_v2'], "%m-%d-%Y")
                    if(MidCloseDate < datetime.datetime.now()):
                        MidCloseDate = PreCloseDate + datetime.timedelta(days = 30)
                if((len(InstructorsDF.loc[Index, 'Q11_v2']) < 10) | ('/' in InstructorsDF.loc[Index, 'Q11_v2'])):
                    InstructorsDF.loc[Index, 'Q11_v2'] = FixDates(InstructorsDF.loc[Index, 'Q11_v2'])
                PostCloseDate = datetime.datetime.strptime(InstructorsDF.loc[Index, 'Q11_v2'], "%m-%d-%Y")
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

                # Make Pre-, Mid-, and Post- surveys, send Pre-Survey, and update Master File with Pre-Survey sent time (if requested)
                PostSurveyID = MakeSurvey(School, CourseNumber, Season, CourseYear, LastName, 'POST', ID)
                PostCloseDate = PostCloseDate.strftime("%d-%b-%Y")

                if(NumSurveys == 3):
                    MidSurveyID = MakeSurvey(School, CourseNumber, Season, CourseYear, LastName, 'MID', ID)
                    for User in SharedUsers:
                        ShareSurvey(User, MidSurveyID)
                    MidCloseDate = MidCloseDate.strftime("%d-%b-%Y")
                    MidSurveyMemo = np.nan
                    MidSurveySent = np.nan
                    MidSurveyReminder = np.nan
                    MidSurveyClosed = np.nan

                if(NumSurveys >= 2):
                    PreSurveyID = MakeSurvey(School, CourseNumber, Season, CourseYear, LastName, 'PRE', ID)
                    for User in SharedUsers: # Share surveys with other interested users
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

                # Create a directory for that term's files if it doesn't exist
                TermDir = "C:/PLIC" + "//" + Season + str(CourseYear) + "Files"
                if not os.path.exists(TermDir):
                    os.mkdir(TermDir, 755)

                # Create a file for that course if it does not already exist
                CourseDir = 	School + '_' + str(CourseNumber) + '_' + LastName + '_' + ID
                CourseDir = TermDir + "//" + CourseDir
                if not os.path.exists(CourseDir):
                    os.mkdir(CourseDir, 755)

                # Make a one line CSV file with the information for that particular course
                # NumberCols = len(InstructorsDF.columns)
                # CourseInfoDF= InstructorsDF.loc[Index, InstructorsDF.columns[[0] + range(11, NumberCols)]].to_frame().T
                # InfoDummyDF = pd.read_csv('Course_Information_Survey.csv', usecols = CourseInfoDF.columns, nrows = 1)
                # Result = pd.concat([InfoDummyDF, CourseInfoDF])
                # Result.to_csv(CourseDir + '//' + Season + str(CourseYear) + '_' + School + '_' + str(CourseNumber) + '_' + LastName + '_CourseInfo.csv', index = False)

                # Individual course info provided by instructor
                InfoDummyDF.loc[[0, Index + 1], :].to_csv(CourseDir + '//' + Season + str(CourseYear) + '_' + School + '_' + str(CourseNumber) + '_' + LastName + '_CourseInfo.csv', index = False)

    os.remove('Course_Information_Survey.csv')

# Check the online form for changing dates and update the necessary dates in the Master file
def CourseChangesControl():
    print("Checking Changes...")
    MasterDF = pd.read_csv('MasterCourseData.csv', skiprows = [0], index_col = 'ID')

    ChangeDates_SurveyID = "SV_9QDl20NjVC3w0uN"
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
    # Send Pre survey, reminders, or close the pre-survey
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
    # Send Pre survey, reminders, or close the pre-survey
    print("Checking Mid-Survey Data...")
    CurrentTime = datetime.datetime.now()
    MasterDF = pd.read_csv("C:/PLIC/MasterCourseData.csv", skiprows = [0])
    for Index, Course in MasterDF.iterrows():
        if((pd.notnull(MasterDF.loc[Index, 'Mid-Survey ID'])) & (pd.isnull(MasterDF.loc[Index, 'Mid-Survey Closed']))):
            # If Pre-Survey not closed, check what time it is and what to do
            MidID = MasterDF.loc[Index, 'Mid-Survey ID']
            SurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + MidID
            MidCloseDate = datetime.datetime.strptime(MasterDF.loc[Index, 'Mid-Survey Close Date'], "%d-%b-%Y")

            # Send a memo to instructors letting them know that the mid-survey is coming
            if(pd.isnull(MasterDF.loc[Index, 'Mid-Survey Sent']) and pd.isnull(MasterDF.loc[Index, 'Mid-Survey Memo']) and (CurrentTime >= MidCloseDate - datetime.timedelta(days = 16))):
                SendSurveyMemo(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], MidCloseDate, 'MID')
                MasterDF.loc[Index, 'Mid-Survey Memo'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            if(pd.isnull(MasterDF.loc[Index, 'Mid-Survey Sent'])):
                # Send Mid-Survey if it hasn't been done so already
                SendSurvey(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], SurveyURL, MidCloseDate, 'MID')
                MasterDF.loc[Index, 'Mid-Survey Sent'] = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())

            elif((CurrentTime >= (MidCloseDate - datetime.timedelta(days = 4))) and pd.isnull(MasterDF.loc[Index, 'Mid-Survey Reminder'])):
                # Send Mid-Survey reminder if we haven't already
                NumStudents = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], MidID, DataType = 'NumberOnly')
                if(NumStudents == 0):
                    # If nobody has responded yet, give extra time and send a reminder
                    MidCloseDate = MidCloseDate + datetime.timedelta(days = 3)
                    MasterDF.loc[Index, 'Mid-Survey Close Date'] = MidCloseDate.strftime("%d-%b-%Y")
                    ZeroResponseEmail(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'MID', SurveyURL, MidCloseDate)
                    MasterDF.loc[Index, 'Mid-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                else:
                    ReminderEmailSend(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'MID', SurveyURL, MidCloseDate, NumStudents)
                    MasterDF.loc[Index, 'Mid-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            elif(CurrentTime >= (MidCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59))):
                # Close the Mid-Survey
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
    print("Checking Post-Survey Data...")
    CurrentTime = datetime.datetime.now()
    MasterDF = pd.read_csv("C:/PLIC/MasterCourseData.csv", skiprows = [0])
    for Index, Course in MasterDF.iterrows():
        if(pd.isnull(MasterDF.loc[Index, 'Post-Survey Closed'])):
            # If post-survey not closed, check what time it is and what to do
            PostID = MasterDF.loc[Index, 'Post-Survey ID']
            SurveyURL = "https://{0}.qualtrics.com/jfe/form/".format(DataCenter) + PostID
            PostCloseDate = datetime.datetime.strptime(MasterDF.loc[Index, 'Post-Survey Close Date'], "%d-%b-%Y")

            # Send a memo to instructors letting them know that the post-survey is coming
            if(pd.isnull(MasterDF.loc[Index, 'Post-Survey Sent']) and pd.isnull(MasterDF.loc[Index, 'Post-Survey Memo']) and (CurrentTime >= PostCloseDate - datetime.timedelta(days = 16))):
                SendSurveyMemo(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], PostCloseDate, 'POST')
                MasterDF.loc[Index, 'Post-Survey Memo'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            # Send the post-survey if its time
            # if(pd.isnull(MasterDF.loc[Index, 'Post-Survey Sent'])):
            elif((CurrentTime >= PostCloseDate - datetime.timedelta(days = 14)) and pd.isnull(MasterDF.loc[Index, 'Post-Survey Sent'])):
                if(pd.isnull(MasterDF.loc[Index, 'Post-Survey Memo'])):
                    MasterDF.loc[Index, 'Post-Survey Memo'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                ActivateSurvey(PostID)
                SendSurvey(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], SurveyURL, PostCloseDate, 'POST')
                MasterDF.loc[Index, 'Post-Survey Sent'] = time.strftime("%d-%b-%Y %H:%M:%S",time.localtime())

            elif((CurrentTime >= (PostCloseDate - datetime.timedelta(days = 4))) and pd.isnull(MasterDF.loc[Index, 'Post-Survey Reminder'])):
                NumStudents = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], PostID, DataType = 'NumberOnly')
                if (NumStudents == 0):
                    # If nobody has responded yet, give extra time and send a reminder
                    PostCloseDate = PostCloseDate + datetime.timedelta(days = 3)
                    MasterDF.loc[Index, 'Post-Survey Close Date'] = PostCloseDate.strftime("%d-%b-%Y")
                    ZeroResponseEmail(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'POST', SurveyURL, PostCloseDate)
                    MasterDF.loc[Index, 'Post-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                else:
                    ReminderEmailSend(MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], 'POST', SurveyURL, PostCloseDate, NumStudents)
                    MasterDF.loc[Index, 'Post-Survey Reminder'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())

            # Close the post-survey
            elif(CurrentTime >= (PostCloseDate + datetime.timedelta(hours = 23, minutes = 59, seconds = 59))):
                CloseSurvey(PostID)
                MasterDF.loc[Index, 'Post-Survey Closed'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
    with open("C:/PLIC/MasterCourseData.csv", 'w') as f:
        MasterDataWriter = csv.writer(f)
        MasterDataWriter.writerows([['Last Accessed:', LastAccess]])
    with open("C:/PLIC/MasterCourseData.csv", 'a') as f:
        MasterDF.to_csv(f, index = False)

# Score the surveys, construct the reports, and send them out
def ReportControl():
    print("Checking Report Data...")
    MasterDF = pd.read_csv("C:/PLIC/MasterCourseData.csv", skiprows = [0])
    for Index, Course in MasterDF.iterrows():
        if(pd.isnull(MasterDF.loc[Index, 'Report Sent']) and pd.notnull(MasterDF.loc[Index, 'Post-Survey Closed'])):
            Path = "C:/PLIC/" + MasterDF.loc[Index, 'Season'] + str(MasterDF.loc[Index, 'Course Year']) + "Files/" + MasterDF.loc[Index, 'School'] + '_' + str(MasterDF.loc[Index, 'Course Number']) + '_' + MasterDF.loc[Index, 'Last Name'] + '_' + MasterDF.loc[Index, 'ID']
            os.chdir(Path)
            DownloadResponses(MasterDF.loc[Index, 'Post-Survey ID'])
            PostSurveyName = GetSurveyName(MasterDF.loc[Index, 'Post-Survey ID'])
            PostDF = pd.read_csv(PostSurveyName + '.csv', skiprows = [1, 2])
            if(PostDF.empty):
                MasterDF.loc[Index, 'Report Sent'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
                continue
            #PostDF = Converter(PostDF)
            #PostDF.to_csv(PostSurveyName + '.csv', index = False)
            NumSurveys = MasterDF.loc[Index, 'Number of Surveys']
            PDFName = Path + "/" + MasterDF.loc[Index, 'Season'] + str(MasterDF.loc[Index, 'Course Year']) + '_' + MasterDF.loc[Index, 'School'] + '_' + str(MasterDF.loc[Index, 'Course Number']) + '_' + MasterDF.loc[Index, 'Last Name'] + '_Report'
            print(PDFName)

            if(NumSurveys >= 2):
                DownloadResponses(MasterDF.loc[Index, 'Pre-Survey ID'])
                PreSurveyName = GetSurveyName(MasterDF.loc[Index, 'Pre-Survey ID'])
                PreDF = pd.read_csv(PreSurveyName + '.csv', skiprows = [1, 2])
                #PreDF = Converter(PreDF)
                #PreDF.to_csv(PreSurveyName + '.csv', index = False)
                if(NumSurveys == 3):
                    DownloadResponses(MasterDF.loc[Index, 'Mid-Survey ID'])
                    MidSurveyName = GetSurveyName(MasterDF.loc[Index, 'Mid-Survey ID'])
                    MidDF = pd.read_csv(MidSurveyName + '.csv', skiprows = [1, 2])
                    # MidDF = Converter(MidDF, 'MID')
                    #MidDF.to_csv(MidSurveyName + '.csv', index = False)
                    if((len(PreDF.index) >= 3) and (len(MidDF.index) >= 3)):
                        ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], Where = 'Automation', PRE = PreSurveyName + '.csv', MID = MidSurveyName +'.csv', POST = PostSurveyName + '.csv')
                    elif((len(PreDF.index) >= 3) and (len(MidDF.index) < 3)):
                        ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], Where = 'Automation', PRE = PreSurveyName +'.csv', POST = PostSurveyName + '.csv')
                    elif((len(PreDF.index) < 3) and (len(MidDF.index) >= 3)):
                        ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], Where = 'Automation', MID = MidSurveyName +'.csv', POST = PostSurveyName + '.csv')
                    else:
                        ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], Where = 'Automation', POST = PostSurveyName + '.csv')
                elif(len(PreDF.index) >= 3):
                    ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], Where = 'Automation', PRE = PreSurveyName +'.csv', POST = PostSurveyName + '.csv')
                else:
                    ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], Where = 'Automation', POST = PostSurveyName + '.csv')
            else:
                ReportGen.Generate(PDFName, r'\textwidth', MasterDF.loc[Index, 'Number Of Students'], MasterDF.loc[Index, 'Course Type'], Where = 'Automation', POST = PostSurveyName + '.csv')

            os.chdir(Path)
            if(MasterDF.loc[Index, 'Credit Offered']): # If the instructor is offering credit include a list of names and IDs of those who completed each of the surveys
                PostNamesDF = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'Post-Survey ID'], DataType = 'Names')
                PostNamesDF.columns = ['Post-Survey IDs', 'Post-Survey Last Names', 'Post-Survey First Names']
                if(NumSurveys >= 2):
                    PreNamesDF = GetResponseData(MasterDF.loc[Index, 'School'], MasterDF.loc[Index, 'Course Number'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Season'], MasterDF.loc[Index, 'Course Year'], MasterDF.loc[Index, 'ID'], MasterDF.loc[Index, 'Pre-Survey ID'], DataType = 'Names')
                    PreNamesDF.columns = ['Pre-Survey IDs', 'Pre-Survey Last Names', 'Pre-Survey First Names']
                    if((NumSurveys == 3) and not MidDF.empty):
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
                if(NumSurveys > 1):
                    NamesDF['PreName'] = NamesDF['Pre-Survey Last Names'] + NamesDF['Pre-Survey First Names']
                    NamesDF = NamesDF.sort_values(by = ['PostName', 'PreName'])
                    NamesDF = NamesDF.drop(labels = ['PreName', 'PostName'], axis = 1)
                else:
                    NamesDF = NamesDF.sort_values(by = 'PostName')
                    NamesDF = NamesDF.drop(labels = 'PostName', axis = 1)
                NamesFileName = MasterDF.loc[Index, 'Season'] + str(MasterDF.loc[Index, 'Course Year']) + '_' + MasterDF.loc[Index, 'School'] + '_' + str(MasterDF.loc[Index, 'Course Number']) +'_' + MasterDF.loc[Index, 'Last Name'] + '_Names.csv'
                NamesDF.to_csv(NamesFileName, index = False)
                SendReport(MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], PDFName + '.pdf', CreditOffered = True, NamesFile = NamesFileName)
            else:
                SendReport(MasterDF.loc[Index, 'First Name'], MasterDF.loc[Index, 'Last Name'], MasterDF.loc[Index, 'Email'], MasterDF.loc[Index, 'Course Name'], MasterDF.loc[Index, 'Course Number'], PDFName + '.pdf')
            MasterDF.loc[Index, 'Report Sent'] = time.strftime("%d-%b-%Y %H:%M:%S", time.localtime())
    with open("C:/PLIC/MasterCourseData.csv", 'w') as f:
        MasterDataWriter = csv.writer(f)
        MasterDataWriter.writerows([['Last Accessed:', LastAccess]])
    with open("C:/PLIC/MasterCourseData.csv", 'a') as f:
        MasterDF.to_csv(f, index = False)

def MakeSurvey(Institution, Number, Semester, Year, InstructorLast, SurveyType, Instructor_ID):
    baseURL = "https://{0}.qualtrics.com/API/v3/surveys".format(DataCenter)
    headers = {
        "x-api-token": apiToken,
        }

    files = {
        'file': ('PLICSurvey.qsf', open('PLICSurvey.qsf', 'rb'), 'application/vnd.qualtrics.survey.qsf')
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

def SendReport(InstructorFirst, InstructorLast, InstructorEmail, CourseName, Code, ReportFile, CreditOffered = False, NamesFile = None):
    msg = MIMEMultipart('alternative')
    msg['From'] = CPERLEmail
    msg['To'] = InstructorEmail
    #msg['To'] = CPERLEmail
    msg['Cc'] = CPERLEmail
    msg['Subject'] = "PLIC Report"

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

    if(CreditOffered == True):
        f_csv=open(NamesFile, 'rb')
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
    # Move to the specific course directory to download responses
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

def Converter(df):

    df_New = pd.read_csv('C:/PLIC/180202__PLIC__Working_version_3d_fix2.csv')

    df['Q3e_l'] = df['Q3c_l']

    df['Q3c'] = df['Q3d']
    df['Q3c_TEXT'] = df['Q3d_TEXT']

    df['Q3d_1'] = df['Q3e_1']
    df['Q3d_3'] = df['Q3e_3']
    df['Q3d_4'] = df['Q3e_4']
    df['Q3d_5'] = df['Q3e_5']
    df['Q3d_6'] = df['Q3e_6']
    df['Q3d_7'] = df['Q3e_7']
    df['Q3d_8'] = df['Q3e_8']
    df['Q3d_9'] = df['Q3e_9']
    df['Q3d_11'] = df['Q3e_11']
    df['Q3d_29'] = df['Q3e_29']
    df['Q3d_29_TEXT'] = df['Q3e_29_TEXT']
    df['Q3d_l'] = df['Q3e_l']

    df['Q3e_8'] = df['Q3c_8']
    df['Q3e_8_TEXT'] = df['Q3c_8_TEXT']
    df['Q3e_11'] = df['Q3c_11']
    df['Q3e_13'] = df['Q3c_13']
    df['Q3e_14'] = df['Q3c_14']
    df['Q3e_17'] = df['Q3c_17']
    df['Q3e_18'] = df['Q3c_18']
    df['Q3e_20'] = df['Q3c_20']
    df['Q3e_21'] = df['Q3c_21']
    df['Q3e_22'] = df['Q3c_22']
    df['Q3e_23'] = df['Q3c_23']
    df['Q3e_24'] = df['Q3c_24']
    df['Q3e_27'] = df['Q3c_27']
    df['Q3e_28'] = df['Q3c_28']
    df['Q3e_32'] = df['Q3c_32']
    df['Q3e_34'] = df['Q3c_34']
    df['Q3e_36'] = df['Q3c_36']
    df['Q3e_37'] = df['Q3c_37']
    df['Q3e_49'] = df['Q3c_49']

    df['Q6.0'] = np.nan
    df['Q6a'] = df['Q6']
    df['Q6a_TEXT'] = df['Q6_TEXT']
    df['Q6b'] = df['Q7'].map({1:1, 2:3, 3:4, 4:4, 5:4, 6:5})
    df['Q6b.i'] = df['Q7'].map({1:np.nan, 2:np.nan, 3:1, 4:3, 5:4, 6:np.nan})
    df['Q6b.i_TEXT'] = df['Q7_TEXT']
    df['Q6c_1'] = np.nan
    df['Q6c_2'] = np.nan
    df['Q6c_3'] = np.nan
    df['Q6c_4'] = np.nan
    df['Q6d'] = df['Q8']
    df['Q6e_1'] = df['Q9_1']
    df['Q6e_2'] = df['Q9_2']
    df['Q6e_3'] = df['Q9_3']
    df['Q6e_3_TEXT'] = df['Q9_3_TEXT']
    df['Q6e_4'] = df['Q9_4']
    df['Q6f_1'] = df['Q10_1']
    df['Q6f_2'] = df['Q10_2']
    df['Q6f_3'] = df['Q10_3']
    df['Q6f_4'] = df['Q10_4']
    df['Q6f_5'] = df['Q10_5']
    df['Q6f_6'] = df['Q10_6']
    df['Q6f_7'] = df['Q10_7']
    df['Q6f_7_TEXT'] = np.nan
    df['Q6f_8'] = df['Q10_8']
    df['Q6g_1'] = np.nan
    df['Q6g_2'] = np.nan
    df['Q6g_2_TEXT'] = np.nan
    df['Q6h'] = np.nan
    df['Q6i'] = df['Q11']
    df['Q6j_1'] = df['Q12_1']
    df['Q6j_2'] = df['Q12_2']

    df['Q7a_10'] = df['Q13']
    df['Q7a_11'] = df['Q14']
    df['Q7b_1'] = df['Q15_1']
    df['Q7b_2'] = df['Q15_2']
    df['Q7b_3'] = df['Q15_3']
    df['Q7b_4'] = df['Q15_4']
    df['Q7c_1'] = df['Q16_1']
    df['Q7c_2'] = df['Q16_2']
    df['Q7c_3'] = df['Q16_3']

    df['Unnamed: 253'] = np.nan

    df = pd.concat([df, pd.DataFrame(columns = ['Q7a_1', 'Q7a_2', 'Q7a_3', 'Q7a_4', 'Q7a_7', 'Q7a_8', 'Q7a_9', 'Q7a_12', 'Q7a_13',
                                                'Q7a_14', 'Q7c_4'])], axis = 1)

    df_Updated = pd.concat([df_New, df], axis = 0, join = 'inner')

    df_Updated = df_Updated.replace(0, np.nan)

    return df_Updated

def GetSurveyName(SurveyID):
    baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(DataCenter, SurveyID)
    headers = {
        "x-api-token": apiToken,
        }

    Req = Request(baseUrl, headers=headers)
    Response = urlopen(Req)
    SurveyName = json.load(Response)['result']['name']
    return SurveyName

def DownloadResponses(SurveyID):
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

def FixDates(Date):
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
