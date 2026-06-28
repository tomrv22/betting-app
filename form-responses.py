from google.oauth2.service_account import Credentials
import google.auth.transport.requests
import requests
import json
import pandas as pd
from datetime import datetime
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

with open('latest-post-match.txt', 'r', encoding='utf-8') as file:
    lines =file.readlines()

for x in range(len(lines)):

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
    df = df[df['gametime']>= df['SubmitTime']]  # correct condition is gametime >= submittime
    df = df.drop(['gametime'], axis=1)

    # Sort by timestamp
    df = df.sort_values(by='SubmitTime')

    # Group by and keep the last timestamp in each group
    df = df.groupby(['Title', 'Email']).last().reset_index()


    line = lines[x].strip().split(',')
    result_dict = {'Title': line[2]+' (A) v/s '+line[3]+' (B) @ '+line[0],
                    'Winner': line[6],
                    'First scoring team': line[7],
                    'First scoring player': line[8],
                    'Team A FT goals': line[4],
                    'Team B FT goals': line[5]}

    df_truth = pd.DataFrame([result_dict])       

    merged_df = pd.merge(df, df_truth, on='Title', how='left')
    all_games  = pd.concat([all_games, merged_df], ignore_index=True)



    # Concatenate the df to the existing excel file containing responses from the previous games saved similarly; Excel file is newly created if this 
# is the first game

# Define the file path
file_path = 'excel_file.xlsx'

# Check if the file exists
if os.path.exists(file_path):
    # Read the existing Excel file
    existing_df = pd.read_excel(file_path).dropna()
    
    # Append the new DataFrame to the existing one and remove the duplicates if the same resposne is counted twice
    updated_df = pd.concat([existing_df, merged_df], ignore_index=True).drop_duplicates(subset=['Response ID'])
    
    # Save the updated DataFrame back to the Excel file
    updated_df.to_excel(file_path, index=False)
    print("Existing data updated with new DataFrame.")
else:
    # If the file doesn't exist, save the new DataFrame as a new Excel file
    merged_df.to_excel(file_path, index=False)
    print("New Excel file created with the DataFrame.")