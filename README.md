# Smash-GG-Discord-Bot
Discord bot that supplies information on game tournaments hosted on Smash.gg, such as alerting users when specific players are playing on a Twitch.tv stream.

## Installation
Requires Python3.

`pip install -r requirements.txt`.

Must also acquire both a Smash.gg and a Discord API Token. 

See:
https://discordpy.readthedocs.io/en/latest/discord.html and https://developer.smash.gg/docs/authentication

I cannot guarantee that the Smash.gg devs will grant you an API Token if just link this repo as your reasoning for requesting a key, but it does not hurt to try.

Store these tokens in a .env file in the form of:

SMASHGG_API_KEY = smashggKey

DISCORD_API_KEY = discordKey

The bot was created as a Discord Cog, so it should be able to be added onto to any other Discord bot that can add cogs. Just add your Smash.gg API Key and everything in the Cogs/Gigi/ folder. Main.py is configured to only accept Gigi as a Cog, and thus is not necessary when adding onto an existing bot that can already add multiple cogs.

## How To Use
After adding the bot to a Discord server, run Main.py. Type !gigi for information on general usage and commands.

The main purpose of the bot is to keep track of players in a tournament hosted on Smash.gg. The stream queue for the given tournaments are watched, and the bot will post a message in the Discord channel letting users know if a player is about to come on, or is already on a Twitch.tv / Mixer.com stream playing their match. Please be aware that not all tournaments keep track of their stream queue properly, and may not even utilize it at all.

![Imgur](https://i.imgur.com/Zp2fzmv.png)

Additional functions come in the form of letting users check for a player's most recently played sets, the games they are entered in along with the corresponding Smash.gg pages, the tournament's stream queue, a multistream link for all of a tournament's streams, and more.

## Information Commands
* **Player Info**
  * Get the Smash.gg pages for every game the specified plaer is entered in.
* **Recent Sets**
  * A player's most recent sets. Gives the names of all players, the score, and the tournament round and name.
* **Brackets**
  * List of brackets for the specified tournament.
* **Streams**
  * List of streams for the specified tournament.
* **Multistream**
  * Provies a multistre.am link for all a tournament's streams. Only works for Twitch.tv streams.
* **Streamqueue**
  * Get a tournament's stream queue giving the (supposed) order of upcoming stream matches.

## List Commands
* **Player List**
  * Prints out what players are being watched.
* **Add**
  * Add player @ tournament combination to the list to be watched. Adds whoever invoked the command to that player's alert list.
* **Delete**
  * Delete player @tournament combination from the list.
* **Delete Tourny**
  * Delete all instances of a specific tournament from the list.
* **Splitter**
  * Change the symbol used to separate the player and tournament names in certain commands. The default is ,
* **My Alerts**
  * Alert lists you're on. Bot will message you when these players are about to come on stream.
* **Alert Me**
  * Be alerted when player is the 1st/2nd in the stream queue, or on stream.
* **Alert Off**
  * Takes you off one player or all player's alert lists.
  
## Admin/Owner Commands
* **Reload**
  * Reload GigiCog. ADMIN ONLY.
* **Reload List**
  * In case something goes wrong and lists need to be reloaded. ADMIN ONLY.
* **Clear List**
  * Clear this server's list of all players. ADMIN ONLY.
* **Enable/Disable Posting**
  * Allows/Disallows bot to post in current channel. ADMIN ONLY. MUST ENABLE IN AT LEAST ONE CHANNEL TO USE THE BOT.
* **Show Channels**
  * Channels Gigi is allowed to post in. ADMIN ONLY.
* **Block/Unblock**
  * Block/Unblock user from running commands on the bot. ADMIN ONLY.
* **Block List**
  * Show the block list. ADMIN ONLY.
* **Start/Stop Queue**
  * Restarts/Stops the auto_queue task that watches for players in the stream queue. ADMIN ONLY.

![Imgur](https://i.imgur.com/Z4TffVD.png)
