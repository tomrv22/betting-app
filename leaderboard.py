import os
import pandas as pd

# Read the Excel file into a DataFrame
df = pd.read_excel("excel_file.xlsx")

#this column rearrangement is important for the functions and the calculations
df = df[df.columns[[0,1,2,3,4,5,13,6,7,14,8,9,15,12,10,11,16,17]]]

def one_bet_cal(df, q):
    bet_col = q - 1
    answer_col = q
    user_col = q + 1
    flag_col = f'flag{q}'

    # Ensure numeric
    df.iloc[:, bet_col] = pd.to_numeric(df.iloc[:, bet_col], errors='coerce')

    # Step 1: Determine winners (correct answers)
    df[flag_col] = (df.iloc[:, answer_col] != df.iloc[:, user_col]).astype(float)  # 0 if correct, 1 if wrong

    # Step 2: Compute redistribution proportions for winners
    losers_mask = df[flag_col] == 1
    winners_mask = df[flag_col] == 0

    total_winner_bets = df.loc[winners_mask, df.columns[bet_col]].sum()
    total_loser_bets = df.loc[losers_mask, df.columns[bet_col]].sum()

    if total_winner_bets == 0 or total_loser_bets == 0:
        # No redistribution possible
        df[flag_col] = 0
        return df

    # Step 3: Calculate gain/loss
    df.loc[winners_mask, flag_col] = (
        total_loser_bets * df.loc[winners_mask, df.columns[bet_col]] / total_winner_bets
    )

    df.loc[losers_mask, flag_col] = -df.loc[losers_mask, df.columns[bet_col]]

    return df


def tuple_bet_cal(df, q_tuple):

    # Separate real answers
    real_answer_1 = df.iloc[:,16]
    real_answer_2 = df.iloc[:,17]

    # Ensure bet column is numeric
    bet_col = q_tuple[0] - 1
    df.iloc[:, bet_col] = pd.to_numeric(df.iloc[:, bet_col], errors='coerce')

    # Determine correctness (both answers must match)
    is_correct = (
        (df.iloc[:, q_tuple[0]] == real_answer_1) &
        (df.iloc[:, q_tuple[1]] == real_answer_2)
    )

    winners = is_correct
    losers = ~is_correct

    winner_bets = df.loc[winners, df.columns[bet_col]]
    loser_bets = df.loc[losers, df.columns[bet_col]]

    total_winner_bets = winner_bets.sum()
    total_loser_bets = loser_bets.sum()

    flag_col = f'flag{q_tuple[0]}_{q_tuple[1]}'
    df[flag_col] = 0.0  # initialize

    if total_winner_bets == 0 or total_loser_bets == 0:
        return df

    # Winners get share of losers' bets
    df.loc[winners, flag_col] = total_loser_bets * winner_bets / total_winner_bets

    # Losers lose their full bet
    df.loc[losers, flag_col] = -df.loc[losers, df.columns[bet_col]]

    return df


combined_leaderboard = pd.DataFrame()
for group_name, group_df in df.groupby('Title'):

    # 5,8,11,(14,15) these are the column indices of the bet responses
    leaderboard_df = one_bet_cal(group_df,5)
    leaderboard_df = one_bet_cal(group_df,8)
    leaderboard_df = one_bet_cal(group_df,11)
    leaderboard_df = tuple_bet_cal(group_df,(14,15))

    # 1. Identify all columns starting with 'flag'
    flag_cols = leaderboard_df.filter(regex="^flag").columns

    # 2. Create the 'gains & losses' column by summing these columns row-wise
    leaderboard_df["Gains & Losses"] = leaderboard_df[flag_cols].sum(axis=1)

    # 3. Drop the original 'flag' columns
    leaderboard_df.drop(columns=flag_cols, inplace=True)

    combined_leaderboard = pd.concat([combined_leaderboard, leaderboard_df])


# Extract datetime part and convert to datetime type
combined_leaderboard['match_datetime'] = pd.to_datetime(combined_leaderboard['Title'].str.split('@').str[1].str.strip())

# Find the latest datetime
latest_time = combined_leaderboard['match_datetime'].max()

# Filter rows with the latest datetime
latest_rows = combined_leaderboard[combined_leaderboard['match_datetime'] == latest_time]
latest_rows = latest_rows.drop(['match_datetime'], axis=1)

combined_leaderboard = combined_leaderboard.drop(['match_datetime'], axis=1)

final_leaderboard = combined_leaderboard.groupby('Email')['Gains & Losses'].sum().reset_index()
final_leaderboard


import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import google.auth.transport.requests
import requests

scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]

#leaderboard_df = leaderboard_df.drop(['Response ID'], axis=1)

print(os.getcwd())
creds = Credentials.from_service_account_file("credentials-sheets.json", scopes=scopes)

#prepare Dataframe for JSON dump post request
values = [  [latest_rows.columns.tolist()] + latest_rows.values.tolist(),
            [final_leaderboard.columns.tolist()] + final_leaderboard.values.tolist()    ]  # Include headers


# Refresh the token to get a new access token
creds.refresh(google.auth.transport.requests.Request())
sheet_id = ["1ShTSX6ZV4TxfklAiU2q1dnfJN94jHorJQkEe3T2Ga7A", "14tFqE4TRQIP4Od2XoF1G0IP6Nws2jLkfhfqEDk6L0hY"]

for p in range(len(sheet_id)):
        
    clear_range_name = "Sheet1"
    range_name = "Sheet1!A2"
    # Get the access token
    access_token = creds.token
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id[p]}/values/{range_name}?valueInputOption=RAW'

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Request body
    body = {
        'range': range_name,
        'majorDimension': 'ROWS',
        'values': values[p]
    }

    clear_url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id[p]}/values/{clear_range_name}:clear'


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
