
class Player(object):
    """
    Player object to keep track of all their information
    related to a specific tournament.
    """
    def __init__(self, gamerTag: str, playerId: int, tournySlug: str, attendeeId: int, gameList: dict, alertList: dict):
        self.gamerTag = gamerTag
        self.playerId = playerId
        self.tournySlug = tournySlug
        self.attendeeId = attendeeId
        self.gameList = gameList
        self.alertList = alertList
        self.queueAppearances = set() #Keep track of this so bot doesn't keep pinging the same set multiple times in a row
        self.startTimes = set() #Same as above, but for when the match is ongoing as opposed to when the player is just in the stream queue
        
    def __eq__(self, Player):
        if self.gamerTag == Player.gamerTag and self.tournySlug == Player.tournySlug and self.attendeeId == Player.attendeeId:
            return True
        else:
            return False

    def jsonifyPlayer(self):
        '''Puts Player object into a JSONable format.'''
        return {
            "gamerTag": self.gamerTag,
            "playerId": self.playerId,
            "tournySlug": self.tournySlug,
            "attendeeId": self.attendeeId,
            "gameList": self.gameList,
            "alertList": self.alertList,
            #queueAppearances and startTimes will be reset every time list is loaded
        }

    def queue_status(self, data):
        '''
        Checks if player is in the stream queue.
        This function will return to PlayerList, which expects a message and the alert list.
        All errors or finding no players in the queue will resort in returning "None" in place of the alert list, with the message explaining why.
        '''
        #Parsing Smash.gg data for the tournament's stream queue
        try:
            message = "Not in stream queue."
            tourny = data["data"]["tournament"]["name"]
            streamQueue = data["data"]["tournament"]["streamQueue"]

            for stream in streamQueue:
                queuePosition = 1 #Check if player is at the top of the queue and and is likely coming up next
                #Decided that not everyone treats the stream queue like a... queue. Often goes out of order.
                streamUrl = "https://" + ".tv/".join([stream["stream"]["streamSource"], stream["stream"]["streamName"]])
                sets = stream["sets"]

                for slot in sets:
                    event = slot["event"]["name"]
                    startedAt = slot["startedAt"] if slot["startedAt"] is not None else None
                    fullRoundText = slot["fullRoundText"]
                    setId = slot["id"]
                    entrant1 = slot["slots"][0]["entrant"]
                    entrant2 = slot["slots"][1]["entrant"]

                    if entrant1 is not None and entrant2 is not None:
                        entrantName1 = entrant1["name"]
                        entrantId1 = entrant1["id"]
                        entrantName2 = entrant2["name"]
                        entrantId2 = entrant2["id"]

                        if entrantId1 in self.gameList.values() or entrantId2 in self.gameList.values():
                            #if setId not in self.queueAppearances and queuePosition < 2: #and/or... I dunno how well most people will update
                            if setId not in self.queueAppearances and startedAt == None and queuePosition <= 2:
                                print("Found {0} vs {1} - {2}, {3} @ {4}".format(entrantName1, entrantName2, event, fullRoundText, tourny))
                                message = "{0}\n".format(streamUrl)
                                message += "{0} vs {1} - {2}, {3} @ {4}\n".format(entrantName1, entrantName2, event, fullRoundText, tourny)
                                message += "Queue Position: {0}\n".format(queuePosition)
                                self.queueAppearances.add(setId)
                            elif startedAt not in self.startTimes and startedAt != None:
                                print("{0} vs {1} - {2}, {3} @ {4} should now be on stream.".format(entrantName1, entrantName2, event, fullRoundText, tourny))
                                message = "{0}\n".format(streamUrl)
                                message += "{0} vs {1} - {2}, {3} @ {4}\nshould now be on stream.\n".format(entrantName1, entrantName2, event, fullRoundText, tourny)
                                self.startTimes.add(startedAt)
                            """
                            else:
                                print("{0} vs {1} - {2}, {3} @ {4}...\nwas previously queued or is too low in the queue."
                                    .format(entrantName1, entrantName2, event, fullRoundText, tourny))
                            """
                    queuePosition += 1
                    #See note above on queuePosition

        except Exception as error:
            message = "Something went wrong getting information from {0} @ {1}'s automated query.".format(self.gamerTag, self.tournySlug)
            print(message)
            print(error)
            return [message, None]

        else:
            if message == "Not in stream queue.":
                return [message, None]
            else:
                return [message, self.alertList]

    #Getters
    def get_gamer_tag(self):
        return self.gamerTag.lower()
    
    def get_player_id(self):
        return self.playerId
        
    def get_tourny_slug(self):
        return self.tournySlug.lower()
    
    def get_attendee_id(self):
        return self.attendeeId

    def get_game_list(self):
        return self.gameList

    def get_alert_list(self):
        return self.alertList

    def get_queue_appearance(self):
        return self.queueAppearances