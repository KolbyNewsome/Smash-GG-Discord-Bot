
#Find specific player and all their events
playerQuery = """
query PlayerQuery($slug: String, $gamerTag: String) {
    tournament(slug: $slug){
		id
		name
    participants(query:{
      filter: {
        gamerTag: $gamerTag
      }
    }){
      nodes{
        gamerTag
        playerId
        id
        entrants {
          id
          event{
            name
          }
        }
      }
    }
  }	
}
"""

#Find all of a tournament's streams and associated games (if applicable)
tournamentStreamQuery = """
query TournamentStreams($slug:String!){
  tournament(slug:$slug){
    name
    streams {
      id
      streamSource
      streamName
      streamGame
    }
  }
}
"""

#Check a tournament's stream queue
streamQueueQuery = """
query StreamQueueOnTournament($slug:String!){
  tournament(slug:$slug){
    name
    streamQueue{
      stream{
        streamSource
        streamName
      }
      sets{
        event {
          name
        }
        startedAt
        fullRoundText
        id
        slots {
          entrant {
            name
            id
          }
        }
      }
    }
  }
}
"""

#Get specific player's played sets and scores in specific tournament
playerSetsQuery = """
query PlayerSetsInTournament($slug: String, $playerId: [ID]) {
  tournament(slug: $slug) {
    events {
      name
      sets(
        filters:{
        	playerIds: $playerId
      	}
      ){
        nodes{
          fullRoundText
          displayScore
        }
      }
    }
  }
}
"""

#Get specific player's most recent sets
recentSetsQuery = """
query SetsByPlayer($playerId: ID!) {
  player(id: $playerId) {
    id
    gamerTag
    recentSets{
      event{
        name
        videogame {
          name
        }
        tournament{
          name
        }
      }
      displayScore
      fullRoundText
    }
  }
}
"""

#Test data
streamQueueTest = {
    "actionRecords": [],
    "data": {
        "tournament": {
            "name": "DreamHack Montreal 2019",
            "streamQueue": [
                {
                    "sets": [
                        {
                            "event": {
                                "name": "Mortal Kombat 11"
                            },
                            "startedAt": 15324,
                            "fullRoundText": "Winners Round 1",
                            "id": 22976957,
                            "slots": [
                                {
                                    "entrant": {
                                        "name": "@w1nter_warz",
                                        "id": 3607699
                                    }
                                },
                                {
                                    "entrant": {
                                        "name": "AZ MortySeinfeld",
                                        "id": 22
                                    }
                                }
                            ]
                        },
                        {
                            "event": {
                                "name": "Mortal Kombat 11"
                            },
                            "startedAt": 15324,
                            "fullRoundText": "Winners Round 2",
                            "id": 22976973,
                            "slots": [
                                {
                                    "entrant": {
                                        "name": "sooneo",
                                        "id": 23
                                    }
                                },
                                {
                                    "entrant": {
                                        "name": "BxA | Lord_V_Noodles",
                                        "id": 24
                                    }
                                }
                            ]
                        },
                    ],
                    "stream": {
                        "streamName": "netherrealm",
                        "streamSource": "TWITCH"
                    }
                }
            ]
        }
    },
    "extensions": {
        "cacheControl": {
            "hints": [
                {
                    "maxAge": 300,
                    "path": [
                        "tournament"
                    ],
                    "scope": "PRIVATE"
                }
            ],
            "version": 1
        },
        "queryComplexity": 124
    }
}

doublequery = {
  "actionRecords": [],
  "data": {
    "tournament": {
      "name": "CEOtaku 2019",
      "streamQueue": [
        {
          "stream": {
            "streamSource": "TWITCH",
            "streamName": "ceogaming"
          },
          "sets": [
            {
              "event": {
                "name": "Skullgirls 2nd Encore"
              },
              "startedAt": 24344,
              "fullRoundText": "Losers Quarter-Final",
              "id": 23553754,
              "slots": [
                {
                  "entrant": {
                    "name": "ATK_Mode | Swiftfox-Dash",
                    "id": 3682969
                  }
                },
                {
                  "entrant": {
                    "name": "LZ | Mr Peck",
                    "id": 3407649
                  }
                }
              ]
            },
            {
              "event": {
                "name": "Skullgirls 2nd Encore"
              },
              "startedAt": 243441,
              "fullRoundText": "Losers Quarter-Final",
              "id": 23553755,
              "slots": [
                {
                  "entrant": {
                    "name": "Echo Fox | dekillsage",
                    "id": 3406459
                  }
                },
                {
                  "entrant": {
                    "name": "KPB | PME",
                    "id": 3461281
                  }
                }
              ]
            },
            {
              "event": {
                "name": "Skullgirls 2nd Encore"
              },
              "startedAt": 243442,
              "fullRoundText": "Winners Final",
              "id": 23553749,
              "slots": [
                {
                  "entrant": {
                    "name": "Echo Fox | SonicFox",
                    "id": 3806280
                  }
                },
                {
                  "entrant": {
                    "name": "RW | Cloud",
                    "id": 3420950
                  }
                }
              ]
            },
          ]
        }
      ]
    }
  },
  "extensions": {
    "cacheControl": {
      "version": 1,
      "hints": [
        {
          "path": [
            "tournament"
          ],
          "maxAge": 300,
          "scope": "PRIVATE"
        }
      ]
    },
    "queryComplexity": 376
  },
  "actionRecords": []
}
