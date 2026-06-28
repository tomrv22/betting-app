import requests
import json
import pandas as pd
from datetime import datetime
import os

API_TOKEN = os.environ.get("API_TOKEN")

url = 'https://api.soccerdataapi.com/matches/?league_id=313&auth_token={}'.format(API_TOKEN)

#league_id = 310 for UCl, 326 for UEL, country_id = 4 for europe
#league_id = 313 for FIFA WC,

# headers = {'X-Auth-Token': API_TOKEN}

params = {
    'key': API_TOKEN,
}


response = requests.get(url)
print(response)
results = response.json()

# Pretty-print JSON
formatted_json = json.dumps(results, indent=4)
# print(formatted_json)
# print(results)

#Function to grab the first goal scoring team and player
def find_first_goalscorer(event_list):
    player = "NA"
    team = "NA"
    for event in event_list:
        if event['event_type']=='penalty_goal' or event['event_type']=='goal' or event['event_type']=='own_goal':
            player = event['player']['name']
            if event['event_type']=='own_goal' and event['team'] == 'away':
                team = 'home'
            elif event['event_type']=='own_goal' and event['team'] == 'home':
                team = 'away'
            else:
                team = event['team'] 
            break
    return player, team

def latest_pre_match(results):
    pre_match_list = []
    for match in results[0]['stage']:
        for item in match['matches']:
            # print(item['status'])
            if item['status'] == 'pre-match' and (item['date'].split('/')[2]=='2026'):
                # print(json.dumps(item, indent=4), "\n\n")
                player, team = find_first_goalscorer(item['events'])
                matchid = item['id']
                home_team = item['teams']['home']['name']
                away_team = item['teams']['away']['name']
                home_ft_goals = item['goals']['home_ft_goals']
                away_ft_goals = item['goals']['away_ft_goals']
                timestamp = datetime.strptime(item['date']+'T'+item['time'], "%d/%m/%YT%H:%M")
                json_dict = {'matchtime':timestamp,
                            'matchid': matchid,
                            'hometeam': home_team,
                            'awayteam': away_team,
                            'home_ft_goals': home_ft_goals,
                            'away_ft_goals': away_ft_goals,
                            'first_scoring_team': team,
                            'first_scoring_player': player}
                pre_match_list.append(json_dict)
    df_pre_match = pd.DataFrame(pre_match_list).sort_values('matchtime')
    return df_pre_match

df_pre_match = latest_pre_match(results).head(1)
print(df_pre_match)

def write_gamesandlineups_to_file(df_pre_match): #function updates the lates-pre-match.txt file based on simulatneous games
    N = len(df_pre_match)
    for n in range(N):
        lineup_url = 'https://api.soccerdataapi.com/match/?match_id={}&auth_token={}'.format(df_pre_match.iloc[n,1], API_TOKEN)
        lineup_response = requests.get(lineup_url)
        print(lineup_response)
        lineupJSON = lineup_response.json()
        # print(json.dumps(lineupJSON, indent=4))

        lineup = []
        for team in ['home', 'away']:
            for section in ['lineups', 'bench'] :
                for item in lineupJSON['lineups'][section][team]:
                    lineup.append(item['player']['name'])

        # get the first 4 columns of the first row of the dataframe (latest pre-match game) as comma separated string for the txt file
        text = ','.join(df_pre_match.iloc[n,0:4].astype(str))

    file_path = "latest-pre-match.txt"

    if n == 0:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text + "\n" + ",".join(lineup) + "\n")
    else:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(text + "\n" + ",".join(lineup) + "\n")


write_gamesandlineups_to_file(df_pre_match)