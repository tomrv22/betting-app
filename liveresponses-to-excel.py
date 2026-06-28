from google.oauth2.service_account import Credentials
import google.auth.transport.requests
import requests
import json
import pandas as pd
from datetime import datetime
import gspread
import os


# A google form was created manually from an account and the service account used in this app was given write permissions to this form
#The form_id of the form is below
form_id = ["1Ef78WAWKDD8p5bzf1L5ZW5h9LQUo7f3837ZopwGbn3Y"]

# form_id = ["1Ef78WAWKDD8p5bzf1L5ZW5h9LQUo7f3837ZopwGbn3Y",
#            "19zkfqDtxXcrWWqZsd57_eLPsByLmCNmzaeVfQSqyG9o", 
#             "1hFFiVLnKyGF5l0gLZT-mqOyty-B2AFGCnCcnYoUodG8",
#             "19yNmKoY25H5VTMwuXCs3mAtGJTzk41f6cyZC-z841gw"]

#SCOPES define the authorization permissions for the client (python app) on the application level. These permissions should be lower 
#than the permissions allowed on the project level for the service account
scopes = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly"
]

#CREDENTIALS created by pasiing the SCOPE with the credentials.json file containing client_id, client_private_key, project_id etc
creds = Credentials.from_service_account_file("credentials-forms.json", scopes=scopes)

# Refresh the token to get a new access token
creds.refresh(google.auth.transport.requests.Request())

# Get the access token
access_token = creds.token
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

all_games = pd.DataFrame()

with open('latest-pre-match.txt', 'r', encoding='utf-8') as file:
    lines =file.readlines()

for x in range(int(len(lines)/2)):

    responses_url = f"https://forms.googleapis.com/v1/forms/{form_id[x]}/responses"
    form_url = f"https://forms.googleapis.com/v1/forms/{form_id[x]}"

    # Fetch responses
    response = requests.get(responses_url, headers=headers)

    #CONVERT RESPONSES INTO A DATAFRAME

    # Parse JSON response
    data = response.json()

    # Extract responses
    responses = []
    for resp in data.get("responses", []):
        answers = resp.get("answers", {})
        row = {"Response ID": resp.get("responseId"), "Email": resp.get("respondentEmail", "N/A"), "SubmitTime": resp.get("lastSubmittedTime")[0:19] }  # Email if available
        
        for question_id, answer_data in answers.items():
            if "textAnswers" in answer_data:
                row[question_id] = answer_data["textAnswers"].get("answers", [{}])[0].get("value", "N/A")
        
        responses.append(row)

    # Convert to DataFrame
    df = pd.DataFrame(responses)


    form_struct = requests.get(form_url, headers=headers)


    #CHANGING HASHED COLUM<N NAMES TO QUESTION NAMES BY MATCHING HASHKEYS TO QUESTION ITEMS

    question_bank = []
    for item in form_struct.json()["items"]:
        if 'questionItem' in item:
            question_bank.append([item['title'], item['questionItem']['question']['questionId']])

    df1 = pd.DataFrame(question_bank)
    # Create a dictionary mapping old columns to new columns from df2
    rename_dict = pd.Series(df1[0].values, index=df1[1].values).to_dict()

    # Rename the columns in df1 using the rename_dict
    df.rename(columns=rename_dict, inplace=True)

    df['Title'] = form_struct.json()['info']['title']
    df = df.sort_index(axis=1)



    #Remove the old responses- df cleaning; This wrks because the questionIDs from the current state of the form would be replaced by actual text
    # questions and the questionIDs from the previous states of the form would still be without assignment. So when you delete these columns, the df
    # would contain only the responses from the current state
    df = df.loc[:, ~df.columns.str.match(r'^\d')]
    df = df.dropna() #drop duplicate NaN rows coming from previous responses

    #KEEP ONLY THE LAST VALID RESPONSE (before the game begins) PER EMAIL IN THE DATAFRAME
    
    #create a gametime column from the title; compare if the submission was mage before the game time; and then drop the gametimecolumn
    df['gametime'] = df['Title'].str.split('@').str[1].str.strip().str.replace(' ','T')
    #df = df[df['gametime']>= df['SubmitTime']]  # correct condition is gametime >= submittime

    #For adjustment late submits
    df = df[df['gametime']>= "19:05:00"]  # correct condition is gametime >= submittime
    df = df.drop(['gametime'], axis=1)

    # Sort by timestamp
    df = df.sort_values(by='SubmitTime')

    # Group by and keep the last timestamp in each group
    df = df.groupby(['Title', 'Email']).last().reset_index()

    all_games  = pd.concat([all_games, df], ignore_index=True)

#drop responseID
all_games = all_games.drop(['Response ID'], axis=1)

# print(all_games)
scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]

print(os.getcwd())
creds = Credentials.from_service_account_file("credentials-sheets.json", scopes=scopes)

#prepare Dataframe for JSON dump post request
values = [all_games.columns.tolist()] + all_games.values.tolist()  # Include headers


# Refresh the token to get a new access token
creds.refresh(google.auth.transport.requests.Request())
sheet_id = "1ShTSX6ZV4TxfklAiU2q1dnfJN94jHorJQkEe3T2Ga7A"
clear_range_name = "Sheet1"
range_name = "Sheet1!A2"
# Get the access token
access_token = creds.token
url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_name}?valueInputOption=RAW'

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Request body
body = {
    'range': range_name,
    'majorDimension': 'ROWS',
    'values': values
}

clear_url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{clear_range_name}:clear'


clear_response = requests.post(clear_url, headers=headers)
if clear_response.status_code == 200:
    print("Sheet cleared.")
else:
    print("Clear failed:", clear_response.text)

postresponse = requests.put(url= url, headers = headers, data=json.dumps(body))
# print(update_response.json())

# Check response
if postresponse.status_code == 200:
    print("Data posted successfully.")
else:
    print("Error:", postresponse.text)
