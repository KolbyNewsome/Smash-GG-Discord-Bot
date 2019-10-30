import os, logging, discord
from dotenv import load_dotenv
from discord.ext import commands

if __name__ == '__main__':
    #logging.basicConfig(level=logging.WARNING, format=' %(asctime)s - %(levelname)s - %(message)s')
    load_dotenv()
    Discord_API_Key = os.getenv("DISCORD_API_KEY")
    bot = commands.Bot("!")
    bot.load_extension("Cogs.Gigi.GigiCog")    
    bot.run(Discord_API_Key)