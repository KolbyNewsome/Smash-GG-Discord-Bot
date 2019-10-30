# Smash-GG-Discord-Bot
Discord bot that supplies information on game tournaments hosted on Smash.gg, such as alerting users when specific players are playing on a Twitch.tv stream.

## Installation
Requires Python3.
`pip install -r requirements.txt`.

Must also acquire both a Smash.gg and a Discord API Token. See:
https://discordpy.readthedocs.io/en/latest/discord.html
https://developer.smash.gg/docs/authentication

Store these in a .env file in the form of:
SMASHGG_API_KEY = smashggKey
DISCORD_API_KEY = discordKey

The bot was created as a Discord Cog, so it should be able to be added onto to any other Discord bot that can add cogs. Just add your Smash.gg API Key and everything in the Cogs/Gigi/ folder. Main.py is configured to only accept Gigi as a Cog, and thus is not necessary when adding onto an existing bot that can already add multiple cogs.

## How To Use
After adding the bot to a Discord server, run Main.py. Type !gigi for information on general usage and commands.

The main purpose of the bot is to keep track of players in a tournament hosted on Smash.gg. The stream queue for the given tournaments are watched, and the bot will post a message in the Discord channel letting users know if a player is about to come on, or is already on a Twitch.tv / Mixer.com stream playing their match. Please be aware that not all tournaments keep track of their stream queue properly, and may not even utilize it at all.

![Imgur](https://i.imgur.com/Zp2fzmv.png)

Additional functions come in the form of letting users check for a player's most recently played sets, the games they are entered in along with the corresponding Smash.gg pages, the tournament's stream queue, a multistream link for all of a tournament's streams, and more.

## Commands

![Imgur](https://i.imgur.com/Z4TffVD.png)
