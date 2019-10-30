import os, requests, json, discord
import Cogs.Gigi.utility.Queries as Queries
import Cogs.Gigi.utility.DataValidation as DataValidation
from dotenv import load_dotenv
from discord.ext import commands, tasks
from graphqlclient import GraphQLClient
from Cogs.Gigi.objects.PlayerList import PlayerList
from Cogs.Gigi.objects.Player import Player

class GigiCog(commands.Cog):
    '''
    GigiCog makes use of the Smash.gg API to provide information
    on players and the tournaments they are entered in such as
    recent sets played and stream urls. 
    An automatic task is run that checks if a player added to the
    player lists is at the top of a tournament's stream queue, and notifies the server if so. 
    '''
    load_dotenv()
    API_Key = os.getenv("SMASHGG_API_KEY")
    url = "https://api.smash.gg/gql/alpha"

    def __init__(self, bot):
        self.bot = bot
        self.playerLists = dict()
        self.splitter = ","
        self.client = GraphQLClient(GigiCog.url)
        self.client.inject_token("Bearer" + GigiCog.API_Key)
        self.load_serial_list()
        self.auto_queue.start()

    #DISCORD LISTENERS
    @commands.Cog.listener()
    async def on_ready(self):
        '''
        Initializes the player lists only upon starting the bot, not reconnections.
        '''
        self.load_serial_list()
        print("GigiCog is ready. Guild list:")
        for guild in self.bot.guilds:
            print(guild.name)
        print()
        return

    @commands.Cog.listener()
    async def on_message(self, message):
        text = message.content.lower()
        if "thanks" in text and "gigi" in text:
            await message.channel.send("You're welcome!")
        return
        
    #DISCORD COMMANDS
    #COMMAND CHECKS
    async def cog_check(self, ctx):
        '''
        Global check on every command to ensure Gigi only posts in allowed channels
        and does not respond to commands invoked by blocked users.
        '''
        playerList = self.get_list(ctx)
        channelList = playerList.get_channel_list()
        blockList = playerList.get_block_list()
        if ctx.channel.id not in channelList.values():
            #Case where all channels in a server are disabled and you need to reenable a channel for posting
            if ctx.message.content == "!enableposting":
                channelList[ctx.channel.name] = ctx.channel.id
                self.update_serial_list(ctx) 
                return True
            else:
                return False
        elif str(ctx.author.id) in blockList.keys():
            return False
        else:
            return True

    async def cog_command_error(self, ctx, error):
        #CheckFailure usually means a blocked user tried a command
        #Or Gigi was sent a command in the wrong channel
        errorType = type(error).__name__
        if errorType == "CheckFailure" or errorType == "CommandOnCooldown":
            print("{}: {}".format(errorType, error))
            return
        else:
            await ctx.send("Command was given invalid arguments. Type !help {0} for more info.".format(ctx.command))
            print("{}: {}".format(errorType, error))
        return

    #HELP COMMANDS
    @commands.command()
    @commands.cooldown(rate=1, per=120, type=commands.BucketType.guild)
    async def gigi(self, ctx):
        '''How to use Gigi.'''

        intro = "Add a player to the list with the !add command, and I will post a message whenever" \
        " that player appears in their tournament's stream queue or on stream. Note that" \
        " I will only work with tournaments hosted on Smash.gg, and not every tournament" \
        " will utilize the stream queue properly."
        
        commands = """
        ```
        Player information:
            !playerinfo player, tournament
            !recentsets player
        Tournament information:
            !brackets tournament
            !streams tournament
            !multistream tournament
            !streamqueue tournament
        List information:
            !playerlist
            !add player1, player2, ..., tournament
            !delete player, tournament
            !deletetourny tournament
            !splitter character
        Enable/disable mentions:
            !myalerts
            !alertme player1, player2, ..., tournament
            !alertoff player1, player2, ..., tournament
            !alertoff all
        ```
        Type !help command -- for more detailed information.
        Type !admin for admin commands.
        """
        message = intro + commands
        await ctx.send(embed=discord.Embed(title="Gigi How To", description=message))
        return

    @commands.command()
    @commands.is_owner()
    async def admin(self, ctx):
        commands = """
        ```
        !reload
        !reloadlists
        !clearlists
        !enableposting / !disableposting
        !showchannels
        !block userId / !unblock userId
        !blocklist
        !startqueue / !stopqueue
        ```
        Type !help command -- for more detailed information.
        """
        await ctx.send(embed=discord.Embed(title="Gigi Admin Commands", description=commands))
        return

    #PLAYER INFO COMMANDS
    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def playerlist(self, ctx):
        '''
        Prints out what players are being watched.
        !playerlist
        '''
        playerList = self.get_list(ctx)
        embedTitle = "{0}'s Player List".format(ctx.guild.name)
        message = playerList.print_players()
        await ctx.send(embed=discord.Embed(title=embedTitle, description=message))
        return

    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def playerinfo(self, ctx, *, message):
        '''
        Get the Smash.GG pages for every game player is entered in.
        !playerinfo player1, player2, ..., tournament
        '''
        #Split up "message" into a gamertag and tournament slug
        parse = self.parse_message(message)
        if parse == False:
            await ctx.send('!playerinfo player1{0} player2{0} ...{0} tournament'.format(self.splitter))
            return
        gamerTags = parse[0]
        tournySlug = parse[1]
        playerList = self.get_list(ctx)

        for tag in gamerTags:
            info = playerList.player_info(tag, tournySlug)

            #player_info should return a string, False if player was not in the list
            if info == False:
                await ctx.send("{0} @ {1} was not found in the list.".format(tag, tournySlug))
                return
            else:
                embedTitle = "{0} @ {1}".format(tag, tournySlug)
                await ctx.send(embed=discord.Embed(title=embedTitle, description=info))

        return

    @commands.command()
    @commands.cooldown(rate=3, per=60, type=commands.BucketType.user)
    async def recentsets(self, ctx, message):
        '''
        Player's most recent sets. Takes a name or player ID.
        First method requires that the player is already in the list.
        Get a player's id by calling !listplayers or !playerinfo.
        !recentsets player's_name
        !recentsets player's_id
        '''
        #With the player ID, you can go straight into the query. Player name requires pulling it out from a player object
        #1 Each invidual player only has 1 PLayer ID, so even if they are in the list multiple times....
        try: 
            int(message)
            playerId = message
        except:
            gamerTag = message.lower()
            playerList = self.get_list(ctx)
            players = playerList.get_players()
            player = [gamer for gamer in players if gamerTag == gamer.get_gamer_tag()]
            if player == []:
                await ctx.send("Player needs to be in the list if you search by their name.")
                return
            playerId = player[0].get_player_id() #1

        #Smash.gg recentSets query + validation
        query = Queries.recentSetsQuery
        input = {"playerId": playerId}
        result = self.client.execute(query, input)
        data = json.loads(result)
        validation = DataValidation.recent_sets_validate_data(data)
        if validation != "Valid":
            await ctx.send(validation)
            return
        
        #Parsing data for set information
        try:
            realId = data["data"]["player"]["id"]
            realTag = data["data"]["player"]["gamerTag"]
            recentSets = data["data"]["player"]["recentSets"]
            embedTitle = "{0}'s Recent Sets - Player ID: {1}".format(realTag, realId)
            info = ""
            for match in recentSets:
                tournament = match["event"]["tournament"]["name"]
                game = match["event"]["videogame"]["name"]
                score = match["displayScore"]
                roundText = match["fullRoundText"]
                info += """{0}\n{1} {2} @ {3}\n\n""".format(score, game, roundText, tournament)
        except Exception as error:
            print(error)
            await ctx.send("Something went wrong with the recent sets query.")
        else:
            await ctx.send(embed=discord.Embed(title=embedTitle, description=info.rstrip()))
        return

    #Don't wanna use this until you can specify the game, otherwise too spammy
    @commands.command(hidden=True)
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def playersets(self, ctx, *, message):
        '''
        All of the sets a player has completed in the specified tournament.
        !playersets player's_name ; tournament
        '''
        #Add in ability to specify which event you want to filter on another day
        #If you just get the player and tournament, whole list. If they put player/tourny/game...
        parse = self.parse_message(message)
        if parse == False:
            await ctx.send('!playersets player name{0} tournament name'.format(self.splitter))
            return
        gamerTag = parse[0]
        tournySlug = parse[1]
        playerList = self.get_list(ctx)
        player = playerList.get_player(gamerTag, tournySlug)
        if player is False:
            await ctx.send("{0} is not in the list under {1}. Add them first.".format(gamerTag, tournySlug))
            return
        
        #Smash.gg query + validation
        query = Queries.playerSetsQuery
        input = {"slug": tournySlug, "playerId": player.get_player_id()}
        result = self.client.execute(query, input)
        data = json.loads(result)
        validation = DataValidation.player_sets_validate_data(data)
        if validation != "Valid":
            await ctx.send(validation)
            return
        
        #Getting player's matches in each event they're entered in
        events = data["data"]["tournament"]["events"]
        for event in events:
            if event["sets"]["nodes"] is None:
                continue
            else:
                info = ""
                gameName = event["name"]
                for match in event["sets"]["nodes"]:
                    roundText = match["fullRoundText"]
                    displayScore = match["displayScore"]
                    #Spoiler tag this
                    info += "{0} --- {1}\n".format(displayScore, roundText)
                    embedTitle = "{0} @ {1} - {2}".format(gamerTag, tournySlug, gameName)
                await ctx.send(spoiler=True, embed=discord.Embed(title=embedTitle, description=info.rstrip()))
        return

    #TOURNAMENT INFO COMMANDS
    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.guild)
    async def streams(self, ctx, *, tournySlug: str):
        '''
        Get all of a tournament's streams.
        !tournystreams tournament
        '''
        #Smash.gg query + validation
        tournySlug = self.string_clean(tournySlug)
        query = Queries.tournamentStreamQuery
        input = {"slug": tournySlug}
        result = self.client.execute(query, input)
        data = json.loads(result)
        #print(json.dumps(data, indent=4, sort_keys=True))
        validation = DataValidation.tourny_streams_validate_data(data)
        if validation != "Valid":
            await ctx.send(validation)
            return

        #Getting each tournament's stream info
        info = ""
        embedTitle = "{0}'s Stream List".format(tournySlug)
        streams = data["data"]["tournament"]["streams"]
        try:
            for stream in streams:
                if stream["streamGame"] is not None:
                    streamGame = " - " + stream["streamGame"]
                else:
                    streamGame = ""
                streamSite = self.get_domain(stream["streamSource"])
                streamUrl = "https://{0}{1}".format(streamSite, stream["streamName"])
                info += "{0}{1}\n".format(streamUrl, streamGame)
        except Exception as error:
            await ctx.send("Something went wrong getting the streams.")
            print("{}: {}".format(type(error).__name__, error))
        else:
            await ctx.send(embed=discord.Embed(title=embedTitle, description=info.rstrip()))
        return

    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.guild)
    async def multistream(self, ctx, *, tournySlug: str):
        '''
        Provides a multistre.am link for all a tournament's streams.
        Only works for Twitch.tv streams.
        !multistream tournament
        '''
        #Smash.gg query + validation
        tournySlug = self.string_clean(tournySlug)
        query = Queries.tournamentStreamQuery
        input = {"slug": tournySlug}
        result = self.client.execute(query, input)
        data = json.loads(result)
        #print(json.dumps(data, indent=4, sort_keys=True))
        validation = DataValidation.tourny_streams_validate_data(data)
        if validation != "Valid":
            await ctx.send(validation)
            return

        #Getting each tournament's stream info
        url = "https://multistre.am/"
        numStreams = 0
        embedTitle = "{0}'s Multistream".format(tournySlug)
        streams = data["data"]["tournament"]["streams"]
        try:
            for stream in streams:
                numStreams += 1
                url += "{0}/".format(stream["streamName"])
                if numStreams == 8: #Multistre.am can fit a maximum of 8 streams
                    break

            layout = self.get_layout(numStreams)
            url = url + layout
        except Exception as error:
            await ctx.send("Something went wrong grabbing the streams.")
            print("{}: {}".format(type(error).__name__, error))
        else:
            await ctx.send(embed=discord.Embed(title=embedTitle, description=url))
        
        return

    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.guild)
    async def streamqueue(self, ctx, *, tournySlug: str):
        '''
        Get a tournament's stream queue.
        !streamqueue tournament
        '''
        #Smash.gg query + validation
        tournySlug = self.string_clean(tournySlug)
        query = Queries.streamQueueQuery
        input = {"slug": tournySlug}
        result = self.client.execute(query, input)
        data = json.loads(result)
        #print(json.dumps(data, indent=4, sort_keys=True))
        validation = DataValidation.stream_queue_validate_data(data)
        if validation != "Valid":
            await ctx.send(validation)
            return
        
        #Getting each tournament's stream and it's individual queue
        embedTitle = "{0}'s stream queue".format(tournySlug)
        streamQueue = data["data"]["tournament"]["streamQueue"]
        info = ""
        try:
            for stream in streamQueue:
                streamSource = stream["stream"]["streamSource"]
                streamSite = self.get_domain(streamSource)
                streamName = stream["stream"]["streamName"]
                streamUrl = "https://{0}{1}".format(streamSite, streamName)
                sets = stream["sets"]
                info += "{0}\n".format(streamUrl)
                for slot in sets:
                    event = slot["event"]["name"]
                    fullRoundText = slot["fullRoundText"]
                    entrant1 = slot["slots"][0]["entrant"]
                    entrant2 = slot["slots"][1]["entrant"]
                    if entrant1 is not None and entrant2 is not None:
                        info += "{0} vs {1} - {2}, {3}\n".format(entrant1["name"], entrant2["name"], event, fullRoundText)
                info += "\n"
        except Exception as error:
            await ctx.send("Something went wrong getting the stream queue's information.")
            print("{}: {}".format(type(error).__name__, error))
        else:
            await ctx.send(embed=discord.Embed(title=embedTitle, description=info.rstrip()))
        return

    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def brackets(self, ctx, * , tournySlug: str):
        '''
        List of brackets for specified tournament.
        !brackets tournament
        '''
        tournySlug = self.string_clean(tournySlug)
        url = "https://smash.gg/tournament/{0}/events".format(tournySlug)
        await ctx.send(url)
        return

    #LIST EDITING COMMANDS
    @commands.command()
    @commands.cooldown(rate=5, per=30, type=commands.BucketType.user)
    async def add(self, ctx, *, message):
        '''
        Add player @ tournament combination to the list to be watched.
        Adds whoever invoked the command to that player's alert list.
        !add player1, player2, ..., tournament
        '''
        success = False
        #Split up "message" into a gamertag and tournament slug
        parse = self.parse_message(message)
        if parse == False:
            await ctx.send("!add player1{0} player2{0} ...{0} tournament name".format(self.splitter))
            return
        gamerTags = parse[0]
        tournySlug = parse[1]
        for tag in gamerTags:
            input = {"gamerTag": tag, "slug": tournySlug}

            #Smash.gg query + validation
            query = Queries.playerQuery
            result = self.client.execute(query, input)
            data = json.loads(result)
            validation = DataValidation.tourny_validate_data(data)
            if validation != "Valid":
                await ctx.send(validation)
                continue

            #Create player object and add to the appropriate list; update json file
            try:
                realTag = data["data"]["tournament"]["participants"]["nodes"][0]["gamerTag"]
                playerId = data["data"]["tournament"]["participants"]["nodes"][0]["playerId"]
                attendeeId = data["data"]["tournament"]["participants"]["nodes"][0]["id"]
                eventList = data["data"]["tournament"]["participants"]["nodes"][0]["entrants"]
                gameList = {self.string_clean(eventList["event"]["name"]): eventList["id"] for eventList in eventList}
                alertList = dict()
                player = Player(realTag, playerId, tournySlug, attendeeId, gameList, alertList)

                playerList = self.get_list(ctx)
                check = playerList.add_player(player)
                if check != "Success":
                    #Case where player was already in the list
                    #Add the user to the alert list regardless
                    alertList = player.get_alert_list()
                    alertList[str(ctx.author.id)] = ctx.author.name
                    self.update_serial_list(ctx)
                    await ctx.send(check)
                    continue
            except Exception as error:
                print(error) #Logging
                await ctx.send("Something went wrong getting information from the player query")
            else:
                success = True
                alertList = player.get_alert_list()
                alertList[str(ctx.author.id)] = ctx.author.name
                self.update_serial_list(ctx)
                await ctx.send("Added {0} @ {1}.".format(realTag, tournySlug))

        if success == True:
            await ctx.send(
                "I'll mention you when these players are in the stream queue.\n"
                + "!alertoff all --- if you don't want to be mentioned."
                )
        return

    @commands.command()
    @commands.cooldown(rate=5, per=30, type=commands.BucketType.user)
    async def delete(self, ctx, *, message): 
        '''
        Delete player from the list.
        !delete player1, player2, ..., tournament
        '''
        #Split up "message" into a gamertag and tournament slug
        parse = self.parse_message(message)
        if parse == False:
            await ctx.send("!delete player1{0} player2{0} ...{0} tournament name".format(self.splitter))
            return
        gamerTags = parse[0]
        tournySlug = parse[1]

        playerList = self.get_list(ctx)
        for tag in gamerTags:
            check = playerList.delete_player(tag.lower(), tournySlug.lower())
            if check != "Success":
                await ctx.send(check)
                continue
            await ctx.send("Removed {0} @ {1}.".format(tag, tournySlug))

        self.update_serial_list(ctx)
        return

    @commands.command()
    @commands.cooldown(rate=5, per=30, type=commands.BucketType.user)
    async def deletetourny(self, ctx, *, tourny: str): 
        '''
        Delete all instances of a specific tournament from the list.
        !deletetourny tournament
        '''
        playerList = self.get_list(ctx)
        check = playerList.delete_tourny(self.string_clean(tourny))
        if check != "Success":
            await ctx.send(check)
            return
        await ctx.send("Removed all instances of {0} from the list".format(tourny))
        self.update_serial_list(ctx)
        return

    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def splitter(self, ctx, splitter):
        '''
        Change the symbol used to separate the player and tournament names in certain commands.
        The default is ,
        !splitter character
        '''
        if splitter.isalnum():
            await ctx.send("Splitter should not be alphanumeric.")
            return
        else:
            oldSplitter = self.splitter
            self.splitter = splitter
            await ctx.send("Changed splitter from {0} to {1}.".format(oldSplitter, self.splitter))
            return

    #ALERT COMMANDS
    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def myalerts(self, ctx):
        '''
        Alert lists you're on.
        !myalerts
        '''
        alerts = self.find_alerts(ctx)
        embedTitle = "{0}'s alerts.".format(ctx.author.name)
        players = ["{0} @ {1}".format(player.get_gamer_tag(), player.get_tourny_slug()) for player in alerts] 
        await ctx.send(embed=discord.Embed(title=embedTitle, description=", ".join(players)))
        return

    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def alertme(self, ctx, *, message):
        '''
        Be alerted when player is the 1st or 2nd in the stream queue.
        Keep in mind that the Smash.gg stream queue is not always managed properly.
        !alertme player1, player2, ..., tournament
        '''
        #Split up "message" into a gamertag and tournament slug
        parse = self.parse_message(message)
        if parse == False:
            await ctx.send('!alertme player1{0} player2{0} ...{0} tournament name'.format(self.splitter))
            return
        gamerTags = parse[0]
        tournySlug = parse[1]
        playerList = self.get_list(ctx)

        #get_player returns a player object if the player exists, otherwise it returns a message
        for tag in gamerTags:
            player = playerList.get_player(tag, tournySlug)
            if player is "{0} @ {1} was not found in the list.".format(tag, tournySlug):
                await ctx.send(player)
                return
            alertList = player.get_alert_list()
            if str(ctx.author.id) in alertList.keys():
                await ctx.send("{0}: You're already on {1} @ {2}'s alert list.".format(ctx.author.name, tag, tournySlug))
                return

            #Load the ID into the Json as a string and not int, otherwise the ID would be saved as an int
            #and loaded back in as a string, leading to potential duplicate users in a list and other errors
            alertList[str(ctx.author.id)] = ctx.author.name
            self.update_serial_list(ctx)

        await ctx.send("{0}: I'll mention you when these players are in the stream queue or on stream.".format(ctx.author.name))
        return

    @commands.command()
    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    async def alertoff(self, ctx, *, message):
        '''
        Takes you off one player or all player's alert lists.
        !alertoff player1, player2, ..., tournament
        !alertoff all
        '''
        playerList = self.get_list(ctx)
        players = playerList.get_players()

        #If: Remove user from all player's alert lists
        #Else: Remove user from specified player's list
        if message == "all":
            for player in players:
                alertList = player.get_alert_list()
                if str(ctx.author.id) in alertList.keys():
                    del alertList[str(ctx.author.id)]
            await ctx.send("{0}: Removed you from all alert lists.".format(ctx.author.name))
        else:
            parse = self.parse_message(message)
            if parse == False:
                await ctx.send("!alertoff player1{0} player2{0} ...{0} tournament name, or !alertoff all.".format(self.splitter))
                return
            gamerTags = parse[0]
            tournySlug = parse[1]

            for tag in gamerTags:
                #get_player returns a player object if the player exists, otherwise it returns a message
                player = playerList.get_player(tag, tournySlug)
                if player is "{0} @ {1} was not found in the list.".format(tag, tournySlug):
                    await ctx.send(player)
                    continue
                #Delete from player's alert list
                alertList = player.get_alert_list()
                if str(ctx.author.id) in alertList.keys():
                    del alertList[str(ctx.author.id)]
                    await ctx.send("{0} removed from {1} @ {2}'s alert list.".format(ctx.author.name, tag, tournySlug))
                else:
                    await ctx.send("{0}: You were not found in their alert list.")

        self.update_serial_list(ctx)
        return
    
    #OWNER-ONLY COMMANDS
    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx):
        '''
        Reload GigiCog. ADMIN ONLY.
        Note that only changes to GigiCog and not utilities or objects will be reflected.
        !reload GigiCog
        '''
        #I think... this should actually be in main.py
        await self.bot.wait_until_ready()
        try:
            self.auto_queue.cancel()
            self.bot.reload_extension("Cogs.Gigi.GigiCog")
        except Exception as error:
            await ctx.send("Something went wrong trying to reload.")
            print("{}: {}".format(type(error).__name__, error))
        else:
            await ctx.send("Reloaded GigiCog.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reloadlists(self, ctx):
        '''
        In case something goes wrong and lists need to be reloaded. ADMIN ONLY.
        !reloadlists
        '''
        self.load_serial_list()
        await ctx.send("{0}'s list reloaded.".format(ctx.guild.name))
        return

    @commands.command(hidden=True)
    @commands.is_owner()
    async def clearlist(self, ctx):
        '''
        Clear this server's list. ADMIN ONLY.
        !clearlist
        '''
        playerList = self.get_list(ctx)
        playerList.clear_list()
        self.update_serial_list(ctx)
        await ctx.send("{0}'s list cleared.".format(ctx.guild.name))
    
    @commands.command(hidden=True)
    @commands.is_owner()
    async def enableposting(self, ctx):
        '''
        Allows GigiCog to post in current channel. ADMIN ONLY.
        MUST ENABLE IN AT LEAST ONE CHANNEL TO USE THE BOT.
        !enableposting
        '''
        playerList = self.get_list(ctx)
        channelList = playerList.get_channel_list()
        channelList[ctx.channel.name] = ctx.channel.id
        await ctx.send("{0} added to queue channel list".format(ctx.channel.name))
        self.update_serial_list(ctx)
        return

    @commands.command(hidden=True)
    @commands.is_owner()
    async def disableposting(self, ctx):
        '''
        Disallows posting in current channel. ADMIN ONLY.
        !disableposting
        '''
        playerList = self.get_list(ctx)
        channelList = playerList.get_channel_list()
        try:
            del channelList[ctx.channel.name]
        except:
            await ctx.send("{0} wasn't in the queue channel list.".format(ctx.channel.name))
            return
        else:
            self.update_serial_list(ctx)
            await ctx.send("{0} removed from queue channel list.".format(ctx.channel.name))
            return

    @commands.command(hidden=True)
    @commands.cooldown(rate=2, per=30, type=commands.BucketType.guild)
    async def showchannels(self, ctx):
        '''
        Channels Gigi is allowed to post in.
        !showchannels
        !enableposting to enable a channel
        !disableposting to disable a channel
        '''
        playerList = self.get_list(ctx)
        channelList = playerList.get_channel_list()
        await ctx.send(embed=discord.Embed(title="Auto-Queue Channels", description=", ".join(channelList.keys())))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def block(self, ctx, id):
        '''
        Block user from running commands on the bot. ADMIN ONLY.
        !block userid
        '''
        if not int(id):
            await ctx.send("Give me an ID. (Right-click user -> Copy ID)")
            return
        else:
            try:
                userName = self.bot.get_user(int(id)).name
            except Exception as error:
                await ctx.send("Invalid ID. (Wrong, or not in the server)")
                return
            
            #Add user to block list
            playerList = self.get_list(ctx)
            blockList = playerList.get_block_list()
            blockList[str(id)] = userName
            await ctx.send(f"Blocked {userName}.")
            
            #Remove this user from all mentions lists as well
            players = playerList.get_players()
            for player in players:
                alertList = player.get_alert_list()
                if str(id) in alertList:
                    del alertList[str(id)]

            self.update_serial_list(ctx)
    
    @commands.command(hidden=True)
    @commands.is_owner()
    async def unblock(self, ctx, id):
        '''
        Unblock user from running commands on the bot. ADMIN ONLY.
        !unblock userid
        '''
        if not int(id):
            await ctx.send("Give me an ID. (Right-click user -> Copy ID)")
            return
        else:
            playerList = self.get_list(ctx)
            blockList = playerList.get_block_list()
            try:
                userName = blockList[str(id)]
                del blockList[str(id)]
            except Exception as error:
                await ctx.send("ID is not in the blocklist.")
                return

            await ctx.send(f"Unblocked {userName}.")
            self.update_serial_list(ctx)
    
    @commands.command(hidden=True)
    @commands.is_owner()
    async def blocklist(self, ctx):
        '''
        Show the block list. ADMIN ONLY.
        !blocklist
        '''
        playerList = self.get_list(ctx)
        blockList = playerList.get_block_list().values()
        await ctx.send(embed=discord.Embed(title="Block list", description=", ".join(blockList)))

    @commands.command()
    @commands.is_owner()
    async def stopqueue(self, ctx):
        '''
        Stops the auto_queue task. ADMIN ONLY.
        '''
        self.auto_queue.cancel()
        print("Auto queue stopped.")
        for playerList in self.playerLists.values():
            channelList = playerList.get_channel_list()
            channelIds = [id for id in channelList.values()]
            for id in channelIds:
                channel = self.bot.get_channel(id)
                await channel.send("Auto queue stopped.")
    
    @commands.command()
    @commands.is_owner()
    async def startqueue(self, ctx):
        '''
        Restarts the auto_queue task. ADMIN ONLY.
        '''
        self.auto_queue.start()
        print("Auto queue restarted.")
        for playerList in self.playerLists.values():
            channelList = playerList.get_channel_list()
            channelIds = [id for id in channelList.values()]
            for id in channelIds:
                channel = self.bot.get_channel(id)
                await channel.send("Auto queue restarted.")

    #AUTOMATIC TASKS
    @tasks.loop(seconds=20)
    async def auto_queue(self):
        '''
        Runs a query for each player to see if they are in their tournament's stream queue.
        If a player is found, GigiCog will send a message to the server
        and mention users in their alert list.
        '''
        #Run through each PlayerList object, 
        #Run check.queue to see if player is in the stream queue
        await self.bot.wait_until_ready()
        for playerList in self.playerLists.values():
            if not playerList.get_players():
                continue

            #print("Queuing for {0}'s players....".format(playerList.serverName))
            status = playerList.check_queue(self.client)
            #status[0] either contains stream queue information or an empty string if nobody was found
            if status[0] == "":
                #print("No players from {0}'s list in the stream queue.\n".format(playerList.serverName))
                continue

            #At least one player found in a stream queue
            #Get user ids from the alert list and turning them into Discord mentions
            mentions = set()
            message = status[0]    
            idList = status[1]
            for id in idList:
                mentions.add(self.bot.get_user(id).mention)

            #Print stream queue information and mentions to applicable channels
            #channelNum so bot doesn't mention people in multiple channels in the same server
            channelNum = 1 
            channelList = playerList.get_channel_list()
            channelIds = [id for id in channelList.values()]
            for id in channelIds:
                channel = self.bot.get_channel(id)
                await channel.send(embed=discord.Embed(title="Tracked players found in stream queue.", description=message))
                if mentions and channelNum == 1:
                    await channel.send(", ".join(mentions))
                channelNum += 1
            print()

        return

    #UTILITY FUNCTIONS
    def get_list(self, ctx):
        '''
        Gets the PlayerList for the server that invoked the command to update/grab info.
        '''
        serverName = ctx.guild.name
        if serverName not in self.playerLists:
            channelList = {ctx.channel.name: ctx.channel.id}
            self.playerLists[serverName] = PlayerList(guild=ctx.guild, channelList=channelList, blockList=dict())
            self.update_serial_list(ctx)
            return self.playerLists[serverName]
        else:
            return self.playerLists[serverName]

    def load_serial_list(self):
        '''
        Loads json player list files into memory 
        and creates each list and its players.
        '''
        #Getting player list for each server the bot is connected to
        for guild in self.bot.guilds:
            serverName = guild.name
            serverFile = "{0}'s Player List.json".format(serverName)
            jsonPath = os.path.join("Cogs", "Gigi", "Player Lists", serverFile)
            print("Getting {0}".format(serverFile))
            if not os.path.exists(jsonPath):
                print("{0} does not exist.".format(jsonPath))
                continue
            with open(jsonPath, "r") as readFile:
                try:
                    data = json.load(readFile)
                    self.playerLists[serverName] = PlayerList(guild, data["channelList"], data["blockList"])
                    players = data["playerList"]
                except Exception as error:
                    print(f"Could not load {serverFile} due to {error}. Clear or undo any edits to your list.")
                    continue

                #Recreating player list and player objects from the json file
                for player in players:
                    try:
                        gamerTag = player["gamerTag"]
                        playerId = player["playerId"]
                        tournySlug = player["tournySlug"]
                        attendeeId = player["attendeeId"]
                        gameList = player["gameList"]
                        alertList = player["alertList"]
                        self.playerLists[serverName].players.append(
                            Player(gamerTag, playerId, tournySlug, attendeeId, gameList, alertList))
                        print("Got {0} @ {1}".format(gamerTag, tournySlug)) #Logging
                    except Exception as error:
                        print(f"Could not load a player due to {error}. Clear or undo any edits to your list.")
                self.playerLists[serverName].update_query_list()
            print()
        print()
        return

    def update_serial_list(self, ctx):
        '''Updates server's player list json file'''
        playerList = self.get_list(ctx)
        jsonList = playerList.jsonifyList()
        serverFile = "{0}'s Player List.json".format(ctx.guild.name)
        jsonPath = os.path.join("Cogs", "Gigi", "Player Lists", serverFile)
        with open(jsonPath, "w") as writeFile:
            json.dump(jsonList, writeFile, indent=4)
        return
    
    def parse_message(self, message):
        '''
        Splits the message into tournament info and player info when necessary
        Turns tournament name into proper slug
        '''
        if self.splitter not in message:
            return False
        splitMessage = message.split(self.splitter)
        gamerTag = [tag.strip().lower() for tag in splitMessage]
        tournySlug = self.string_clean(gamerTag.pop())
        return (gamerTag, tournySlug)
    
    def string_clean(self, input):
        '''
        Line 1: Replace non-alphanumerics with spaces
        Line 2: Replace successive whitespace with a single space
        Line 3: Strip trailing whitespace, replace remaining space with a dash suitable for later turning into a url
        '''
        input = "".join((letter if letter.isalnum() or letter.isspace() else " ") for letter in input)
        input = " ".join(input.split())
        input = input.strip().lower().replace(" ", "-")
        return input

    def find_alerts(self, ctx):
        '''Finds each alert list that the author who invoked the command is in.'''
        playerList = self.get_list(ctx)
        players = playerList.get_players()
        alerts = []
        for player in players:
            if str(ctx.author.id) not in player.get_alert_list().keys():
                continue
            else:
                alerts.append(player)

        return alerts

    def get_domain(self, streamSource: str):
        '''For use with stream query commands.'''
        domains = {
            "TWITCH": "twitch.tv/",
            "STREAMME": "stream.me/",
            "MIXER": "mixer.com/",
            "HITBOX": "smashcast.tv/"
        }
        return domains.get(streamSource, "None")

    def get_layout(self, numStreams: int):
        '''For use with multistream command.'''
        layouts = {
            1: "layout0/",
            2: "layout3/",
            3: "layout6/",
            4: "layout10/",
            5: "layout14/",
            6: "layout17/",
            7: "layout19/",
            8: "layout22/"
        }
        return layouts.get(numStreams, "layout0")


def setup(bot):
    bot.add_cog(GigiCog(bot))
    return