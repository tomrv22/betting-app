import gspread
import time
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import google.auth.transport.requests
import os
import requests
import json
from datetime import datetime, timezone

#SCOPES define the authorization permissions for the client (python app) on the application level. These permissions should be lower 
#than the permissions allowed on the project level for the service account
scopes = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly"
]

#CREDENTIALS created by pasiing the SCOPE with the credentials.json file containing client_id, client_private_key, project_id etc
creds = Credentials.from_service_account_file("./betting-app/credentials-forms.json", scopes=scopes)

# Refresh the token to get a new access token
creds.refresh(google.auth.transport.requests.Request())

# Get the access token
access_token = creds.token


headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}



# TO CREATE THE FORM WITH JUST TITLE FIRST, USE THE FOLLORING POST REQUEST

# url = "https://forms.googleapis.com/v1/forms"

# data = {
#     "info": {
#         "title": "My API Form"  # ✅ Only the title is allowed
#     }
# }

# response = requests.post(url, headers=headers, json=data)
# print(response.json()["formId"],response.json()["responderUri"])


with open('./betting-app/latest-pre-match.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

print(len(lines))
print(lines)

for x in range(int(len(lines)/2)):

    #TO UPDATE AN EXISTING FORM USE THE FOLLOWING POST REQUEST;

    # A google form was created manually from an account and the service account used in this app was given write permissions to this form
    #The form_id of the form is below
    form_id = ["1Ef78WAWKDD8p5bzf1L5ZW5h9LQUo7f3837ZopwGbn3Y"]

    # form_id = ["1Ef78WAWKDD8p5bzf1L5ZW5h9LQUo7f3837ZopwGbn3Y",
    #            "19zkfqDtxXcrWWqZsd57_eLPsByLmCNmzaeVfQSqyG9o", 
    #             "1hFFiVLnKyGF5l0gLZT-mqOyty-B2AFGCnCcnYoUodG8",
    #             "19yNmKoY25H5VTMwuXCs3mAtGJTzk41f6cyZC-z841gw"]

    update_url = f"https://forms.googleapis.com/v1/forms/{form_id[x]}:batchUpdate"
    form_url = f"https://forms.googleapis.com/v1/forms/{form_id[x]}"


    # Fetch the existing form structure
    fetch_response = requests.get(form_url, headers=headers)
    form_data = fetch_response.json()


    formitemIndices =[]
    for i in range(len(form_data.get("items", []))):
        formitemIndices.append(i)
    #reverse the list; The list is reversed because when the item indices are deleted from the first index, the second item gets assigned
    # the first index this would cause problems in further deletion. So we delete from behind by reversing the list
    formitemIndices = sorted(formitemIndices, reverse=True)

    #Delete all existing items starting from the last item to the first
    delete_requests = {"requests":[
        {"deleteItem": {"location": {"index": i}}}
        for i in formitemIndices

    ]}

    print(delete_requests)
    delete_response = requests.post(update_url, headers=headers, json=delete_requests)

    print(delete_response.json(),"\n\n\n")

    time.sleep(2) 

    print("Now update in progress \n\n")
    #Teams and lineups need to be called from football API

    Title = lines[x*2].strip().split(',') # strip to remove \n from the end and convert string to a comma separated list
    Teams = Title[2:]
    Teams.append(Title[0])
    lineup = lines[x*2+1].strip().split(',')
    

    # Teams = ["England", "Spain"] 
    # lineup = ["Bellingham", "Yamal", "Rice"]

    dropdown_options = [{"value": player} for player in lineup]
    scoreline_options = [{"value": x} for x in ['0','1','2','3','4','5','6','7','8','9','10']]

    print(Teams)

    update_data = {
        "requests":  [  
            {"updateFormInfo": {"info": {"title": "{} (A) v/s {} (B) @ {}".format(Teams[0],Teams[1],Teams[2])}, "updateMask": "title"}},
            {"createItem": {  # Question 1
                "item": {
                    "title": "[Q1]Result?",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "Team A wins [within 90 min or ET]"},
                                    {"value": "Team B wins [within 90 min or ET]"},
                                    {"value": "Team A wins on penalties"},
                                    {"value": "Team B wins on penalties"},
                                    {"value": "Draw"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 0}
            }},
            {"createItem": {  # Question 1 bet amount
                "item": {
                    "title": "[Q1]Bet amount?",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "0"},
                                    {"value": "250"},
                                    {"value": "500"},
                                    {"value": "1000"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 1}
            }},
            {"createItem": {
                    "item": {
                        "title": "Team Performance",
                        "description": "Predict the first goal scoring Team",
                        "pageBreakItem": {}
                    },
                    "location": {"index": 2}
                }
            },
            {"createItem": {  # Question 2
                "item": {
                    "title": "[Q2]Which Team scores the first goal? (own goals counted for opposition)",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "Team A"},
                                    {"value": "Team B"},
                                    {"value": "No goals"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 3}
            }},
            {"createItem": {  # Question 2 bet amount
                "item": {
                    "title": "[Q2]Bet amount?",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "0"},
                                    {"value": "250"},
                                    {"value": "500"},
                                    {"value": "1000"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 4}
            }},
            {"createItem": {
                    "item": {
                        "title": "Player Performance",
                        "description": "Predict the first goal scoring Player",
                        "pageBreakItem": {}
                    },
                    "location": {"index": 5}
                }
            },
            {"createItem": {  # Question 3
                "item": {
                    "title": "[Q3]Which player scores the first goal? (own goals included)",
                    "questionItem": {
                        "question": {
                            "required": True,
                                "choiceQuestion": {
                                    "type": "DROP_DOWN",
                                    "options": dropdown_options
                                }
                            }
                        }
                },
                "location": {"index": 6}
            }},
            {"createItem": {  # Question 3 bet amount
                "item": {
                    "title": "[Q3]Bet amount?",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "0"},
                                    {"value": "250"},
                                    {"value": "500"},
                                    {"value": "1000"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 7}
            }},
            {"createItem": {
                    "item": {
                        "title": "Scoreline Predition",
                        "description": "Valid till end of FT",
                        "pageBreakItem": {}
                    },
                    "location": {"index": 8}
                }},
            {"createItem": {  # Question 4
                "item": {
                    "title": "[Q4(a)]Team A total goals (till end of FT)",
                    "questionItem": {
                        "question": {
                            "required": True,
                                "choiceQuestion": {
                                    "type": "DROP_DOWN",
                                    "options": scoreline_options
                                }
                            }
                        }
                },
                "location": {"index": 9}
            }},
            {"createItem": {  # Question 4
                "item": {
                    "title": "[Q4(b)]Team B total goals (till end of FT)",
                    "questionItem": {
                        "question": {
                            "required": True,
                                "choiceQuestion": {
                                    "type": "DROP_DOWN",
                                    "options": scoreline_options
                                }
                            }
                        }
                },
                "location": {"index": 10}
            }},
            {"createItem": {  # Question 3 bet amount
                "item": {
                    "title": "[Q4]Bet amount?",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "0"},
                                    {"value": "250"},
                                    {"value": "500"},
                                    {"value": "1000"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 11}
            }}
        ]
    }

    #If passing too many items doesn't work, we could use service to pass them as chunk batch updates
    #---------------------------------------------------------------------------------------------------------


    # service = build('forms', 'v1', credentials=creds)

    # def chunk_requests(requests, chunk_size=10):
    #     for i in range(0, len(requests), chunk_size):
    #         yield requests[i:i + chunk_size]

    # for chunk in chunk_requests(update_data1["requests"], 10):
    #     service.forms().batchUpdate(formId=form_id, body={"requests": chunk}).execute()
    #---------------------------------------------------------------------------------------------------------

    #print(update_data)

    update_response = requests.post(update_url, headers=headers, json=update_data)

    fetch = requests.get(url= form_url, headers = headers)

    print(update_response.json(),"\n\n")
    print(fetch.json()['responderUri'])
    # print(json.dumps(fetch.json(), indent=4))
