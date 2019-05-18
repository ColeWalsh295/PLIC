# -*- coding: utf-8 -*-
#!c:/Python/python3_6.exe -u

import pandas as pd
import requests
import zipfile
import json
import io

# Setting user Parameters
global DataCenter, baseURL, apiToken, CPERLEmail, UserEmail
# apiToken = API token for communicating with qualtrics
# SharedCole = User Id for a shared user
# SharedKatherine = User Id for a shared user
# SharedUsers = [SharedCole, SharedKatherine] # Users to share surveys with in Qualtrics from main account
DataCenter = 'cornell'
baseURL = "https://{0}.qualtrics.com/API/v3/responseexports/".format(DataCenter)
ChangeURL = "https://{0}.qualtrics.com/jfe/form/SV_9QDl20NjVC3w0uN".format(DataCenter)

CIS_SurveyID = "SV_5ouHoTGEF5FBqxD" # Instructor survey ID

CPERLEmail = 'cperl@cornell.edu' # Shared CPERL email address
UserEmail = 'as-phy-edresearchlab@cornell.edu' # User email address
# EmailPassword = User password

Master_df = pd.read_csv('MasterCourseData.csv') # Read in local master data file with dates information

CIS_Survey_Name = DownloadResponses(SurveyID) # Course Information Survey downloaded as Course_Information_Survey.csv (or whatever name is used in qualtrics)
CIS_df = pd.read_csv(CIS_Survey_Name, skiprows = [1, 2])

CIS_df = CIS_df.loc[~(CIS_df['ResponseID'].isin(Master_df['ID'])) & (CIS_df['Finished'] == 1) & pd.notnull(CIS_df['Q11_v2']), :] # Get new entries by instructors who completed the CIS online and provided a post-survey end date

def CleanNewData(df):
    df = df.rename(columns = {'ResponseID':'ID', 'Q1':'FirstName', 'Q2':'LastName', 'Q3':'Email', 'Q4':'School', 'Q5':'CourseName', 'Q6':'CourseNumber', 'Q8':'NumStudents'})

    # Use Regex to replace any non-alphanumeric characters with underscores...cause instructors fill forms with weird stuff
    df[['FirstName', 'LastName', 'School', 'CourseName', 'CourseNumber']] = df[['FirstName', 'LastName', 'School', 'CourseName', 'CourseNumber']].apply(lambda x: x.str.replace('[^0-9a-zA-Z]+', '_'))

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

def CheckDates(Series):
    Series[~Series.str.match('^(0[1-9]|1[012])[\/\-](0[1-9]|[12][0-9]|3[01])[\/\-]\d{4}$')].replace('/', '-')


    Dates = re.findall(r'[0-9]+', Date)
    if(len(Dates[0]) < 2):
        Dates[0] = '0' + str(Dates[0])
    if(len(Dates[1]) < 2):
        Dates[1] = '0'+ str(Dates[1])
    if(len(Dates[2]) < 4):
        Dates[2] = '20'+ str(Dates[2])
    NewDate = Dates[0] + '-' + Dates[1] + '-' + Dates[2]
    return NewDate


def DownloadResponses(SurveyID):
    # Setting user Parameters
    fileFormat = "csv"

    # Setting static parameters
    requestCheckProgress = 0
    progressStatus = "in progress"
    baseUrl = "https://{0}.qualtrics.com/API/v3/responseexports/".format(dataCenter)
    headers = {
        "content-type": "application/json",
        "x-api-token": apiToken,
        }

    # Step 1: Creating Data Export
    downloadRequestUrl = baseUrl
    downloadRequestPayload = '{"format":"' + fileFormat + '","surveyId":"' + surveyId + '"}'
    downloadRequestResponse = requests.request("POST", downloadRequestUrl, data=downloadRequestPayload, headers=headers)
    progressId = downloadRequestResponse.json()["result"]["id"]

    # Step 2: Checking on Data Export Progress and waiting until export is ready

    isFile = None

    while requestCheckProgress < 100 and progressStatus is not "complete" and isFile is None:
        requestCheckUrl = baseUrl + progressId
        requestCheckResponse = requests.request("GET", requestCheckUrl, headers=headers)
        isFile = (requestCheckResponse.json()["result"]["file"])
        requestCheckProgress = requestCheckResponse.json()["result"]["percentComplete"]

    # Step 3: Downloading file
    requestDownloadUrl = baseUrl + progressId + '/file'
    requestDownload = requests.request("GET", requestDownloadUrl, headers=headers, stream=True)

    # Step 4: Unzipping the file
    try:
        zipfile.ZipFile(io.BytesIO(requestDownload.content)).extractall()
        os.remove("RequestFile.zip")
    except zipfile.BadZipfile:
        print("Bad Zip File, trying again...")
        os.remove("RequestFile.zip")
        DownloadResponses(SurveyID)

    return GetSurveyName(SurveyID)

def GetSurveyName(SurveyID):
    baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(DataCenter, SurveyID)
    headers = {
        "x-api-token": apiToken,
        }

    Req = Request(baseUrl, headers=headers)
    Response = urlopen(Req)
    SurveyName = json.load(Response)['result']['name']

    return SurveyName

if __name__ == '__main__':
	main()
