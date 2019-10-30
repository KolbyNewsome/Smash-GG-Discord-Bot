import json
import Cogs.Gigi.utility.DataValidation as DataValidation
import Cogs.Gigi.utility.Queries as Queries
from Cogs.Gigi.objects.Player import Player
from discord.ext import tasks, commands

class PlayerList(object):
    """
    PlayerList is a list that stores Player objects
    as defined in Player.py. A PlayerList for each
    server Gigi is run in is stored in its own json
    file to recall between executions.
    """

    def __init__(self, guild, channelList=None, blockList=None):
        self.guild = guild
        self.serverName = guild.name
        self.players = []
        self.channelList = channelList
        self.blockList = blockList
        self.queryList = set()
    
    def jsonifyList(self):
        '''Puts PlayerList object into a JSONable format.'''
        jsonList = [player.jsonifyPlayer() for player in self.players]
        return {
            "serverName": self.serverName,
            "channelList": self.channelList,
            "blockList": self.blockList,
            "playerList": jsonList
        }

    def print_players(self):
        if self.players == []:
            return "Player List is empty."
        else:
            message = ""
            for player in self.players:
                gamerTag = player.get_gamer_tag()
                tournySlug = player.get_tourny_slug()
                attendeeId = player.get_attendee_id()
                playerId = player.get_player_id()
                playerUrl = "https://smash.gg/tournament/{0}/attendee/{1}".format(tournySlug, attendeeId)
                message += "{0} @ {1} - Player ID: {2}\n{3}\n".format(gamerTag, tournySlug, playerId, playerUrl)
            return message.rstrip()
            
    def player_info(self, gamerTag: str, tournySlug: str):
        '''Gets player's name, tournament, player Id, and corresponding Smash.GG pages.'''
        player = self.get_player(gamerTag, tournySlug)
        if isinstance(player, str): #Player not found
            return False
        else:
            playerTag = player.get_gamer_tag()
            playerTourny = player.get_tourny_slug()
            playerId = player.get_player_id()
            attendeeId = player.get_attendee_id()
            gameList = player.get_game_list()

            playerUrl = "https://smash.gg/tournament/{0}/attendee/{1}".format(playerTourny, attendeeId)
            message = "Player ID: {0}\n{1}\n".format(playerId, playerUrl)
            for game, entrantId in gameList.items():
                gameUrl = "https://smash.gg/tournament/{0}/event/{1}/entrant/{2}".format(playerTourny, game, entrantId)
                message += "{0} - {1}\n".format(game, gameUrl)
            return message

    def add_player(self, player: object):
        if player not in self.players:
            self.players.append(player)
            self.update_query_list()
            return "Success"
        else:
            return "{0} @ {1} is already in the list.".format(player.gamerTag, player.tournySlug)
            #Just in case you were wondering why not just make this a set so you don't have to check for this:
            #https://stackoverflow.com/questions/3942303/how-does-a-python-set-check-if-two-objects-are-equal-what-methods-does-an-o

    def delete_player(self, gamerTag: str, tournySlug: str):
        player = self.get_player(gamerTag, tournySlug)
        if isinstance(player, str): #Player not found
            return player
        else:
            self.players = [player for player in self.players if not (player.get_gamer_tag().lower() == gamerTag and player.get_tourny_slug() == tournySlug)]
            self.update_query_list()
            return "Success"

    def delete_tourny(self, tournySlug: str):
        tournament = self.get_tourny(tournySlug) #You just need to find one tournament in this case
        if isinstance(tournament, str): #Tournament not found
            return tournament
        else:
            self.players = [player for player in self.players if player.get_tourny_slug() != tournySlug]
            self.update_query_list()
            return "Success"
    
    def clear_list(self):
        self.players.clear()
        self.update_query_list()

    #AUTO-QUEUE
    def check_queue(self, client):
        message = ""
        dataList = dict()
        idList = []

        #Each tournament being watched will have its data stored in a dictionary
        #The correct data will then be passed to Player.py's queue_status function to see if player is
        #in the stream queue.
        for tournySlug in self.queryList: 
            #Smash.GG query + validation
            query = Queries.streamQueueQuery
            input = {"slug": tournySlug}
            result = client.execute(query, input)
            data = json.loads(result)
            #data = Queries.streamQueueTestResult #For testing
            validation = DataValidation.stream_queue_validate_data(data)
            if validation != "Valid":
                #print("{0} - {1}".format(tournySlug, validation))
                continue
            else:
                dataList[tournySlug] = data

        #If dataList is empty, Gigi will consider the stream queue as empty
        if not dataList:
            return [message, idList]

        #Run through each player in the list
        #player.queue_status will return a message status[0] and the player's alert list status[1]
        #If no players are in the queue, message will go unmodified and GigiCog will know this was the case
        for player in self.players:
            tournySlug = player.get_tourny_slug()
            try:
                data = dataList[tournySlug]
            except Exception as error:
                continue
            status = player.queue_status(data)
            if status[1] is not None:
                message += status[0]
                #Convert keys from the alertlist back into ints so they are proper searchable IDs
                for key in status[1]:
                    idList.append(int(key))

        return [message, idList]

    #UTILITY FUNCTIONS
    def get_player(self, gamerTag: str, tournySlug: str):
        for player in self.players:
            if gamerTag == player.get_gamer_tag().lower() and tournySlug == player.get_tourny_slug():
                return player
        return "{0} @ {1} was not found in the list.".format(gamerTag, tournySlug)

    def get_tourny(self, tournySlug: str):
        for player in self.players:
            if tournySlug == player.get_tourny_slug():
                return player
        return "Tournament {0} was not found in the list.".format(tournySlug)

    def get_players_by_tournies(self, tournySlug: str):
        '''Get specific player across multiple tournaments.'''
        players = []
        for player in self.players:
            if tournySlug == player.get_tourny_slug():
                players.append(player)
        return "Tournament {0} was not found in the list.".format(tournySlug)

    def get_tournies_by_players(self, gamerTag: str):
        '''Get multiple tournaments if a specific player is entered.'''
        tournaments = []
        for player in self.players:
            if gamerTag == player.get_gamer_tag():
                tournaments.append(player)
        return "{0} was not found in the list.".format(gamerTag)

    def update_query_list(self):
        '''
        PlayerList keeps track of each tournament being watched so that
        it can easily request the stream queue for each, as opposed to having
        every player object request the stream queue instead. Used for the automated
        queuing functions auto_queue/check_queue.
        '''
        self.queryList.clear()
        for player in self.players:
            tournySlug = player.get_tourny_slug()
            self.queryList.add(tournySlug)

    #GETTERS
    def get_guild(self):
        return self.guild

    def get_players(self):
        return self.players

    def get_channel_list(self):
        return self.channelList
    
    def get_block_list(self):
        return self.blockList