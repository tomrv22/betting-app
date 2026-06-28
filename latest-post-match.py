import requests
import json
import pandas as pd
from datetime import datetime

API_TOKEN = open('./betting-app/soccerdataapi-AUTH_TOKEN').read()

url = 'https://api.soccerdataapi.com/matches/?league_id=313&auth_token={}'.format(API_TOKEN)

#league_id = 310 for UCl, country_id = 4 for europe

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

def home_away_to_winner(team_type, has_penalties):
    if team_type == 'home':
        if has_penalties == False:
            team_type = 'Team A wins [within 90 min or ET]'     
        else:
            team_type = 'Team A wins on penalties' 

    elif team_type == 'away':
        if has_penalties == False:
            team_type = 'Team B wins [within 90 min or ET]'     
        else:
            team_type = 'Team B wins on penalties' 
    return team_type

def hom_away_to_scorer(team_type):
    if team_type == 'home':
        team_type = 'Team A'     

    elif team_type == 'away':
        team_type = 'Team B'     

    return team_type


def latest_post_match(results, matchid):
    post_match_list = []
    for match in results[0]['stage']:
        for item in match['matches']:
            # print(item)
            if item['status'] == 'finished' and item['id'] == int(matchid):
                # print(json.dumps(item, indent=4), "\n\n")
                player, team = find_first_goalscorer(item['events'])
                winner = item['winner']
                has_penalties = item['has_penalties']
                matchid = item['id']
                home_team = item['teams']['home']['name']
                away_team = item['teams']['away']['name']
                home_ft_goals = item['goals']['home_ft_goals']
                away_ft_goals = item['goals']['away_ft_goals']
                timestamp = datetime.strptime(item['date']+'T'+item['time'], "%d/%m/%YT%H:%M")
                winner = home_away_to_winner(winner, has_penalties)
                team = hom_away_to_scorer(team)

                json_dict = {'matchtime':timestamp,
                            'matchid': matchid,
                            'hometeam': home_team,
                            'awayteam': away_team,
                            'home_ft_goals': home_ft_goals,
                            'away_ft_goals': away_ft_goals,
                            'winner': winner,
                            'first_scoring_team': team,
                            'first_scoring_player': player}
                post_match_list.append(json_dict)
    df_post_match = pd.DataFrame(post_match_list)
    return df_post_match

with open('./betting-app/latest-pre-match.txt', 'r', encoding='utf-8') as file:
    content = file.readlines()

for x in range(int(len(content)/2)):
    df_post_match = latest_post_match(results, content[2*x].split(',')[1])

    # get all the columns of the first row of the dataframe (latest post-match finished game) as comma separated string for the txt file
    if not df_post_match.empty:
        text = ','.join(df_post_match.loc[0].astype(str))
        if x == 0:
            with open('./betting-app/latest-post-match.txt', 'w', encoding='utf-8') as file:
                file.write(text+'\n')
        else:
            with open('./betting-app/latest-post-match.txt', 'a', encoding='utf-8') as file:
                file.write(text+'\n')
    else:
        print("The game with ID:{} has not finished".format(content[2*x].split(',')[1]))