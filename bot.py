
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Run pip install -r requirements.txt to install the required libraries
# please open this as a venv
# fill out the .env with the token and channel id you want the bot to respond to


TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

# List of luck messages
luck_messages = [
    "A handsome man will visit you today.",
    "Reply hazy, try again.",
    "Excellent luck.",
    "You might want to reconsider again...",
    "Not your luckiest moment.",
    "Electrical Engineer",
    "You are extremely unlucky!",
    "Bad luck.",
    "Extremely bad luck!",
    "Better not tell you now.",
    "ಠ_ಠ",
    "( ͡° ͜ʖ ͡°)",
    "Please stop using the internet",
    "STOP ASKING ME, DAMN.",
    "idgaf",
    " https://tenor.com/view/cat-tongue-shaking-gif-1214800249503457963",
    " https://klipy.com/gifs/text-bubble",
    " https://pbs.twimg.com/media/Fmp4xtEagAM8g4U.jpg"
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    # Send welcome message only to the specified channel in each guild
    for guild in bot.guilds:
        if CHANNEL_ID:
            channel = guild.get_channel(int(CHANNEL_ID))
            if channel and channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send("berrie connected: nice chat")
                except Exception:
                    pass
    
@bot.event
async def on_guild_join(guild):
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    if channel_id:
        channel = guild.get_channel(int(channel_id))
        if channel and channel.permissions_for(guild.me).send_messages:
            await channel.send("Berrie has just joined the server! Nice!")

@bot.command()
async def fortune(ctx):
    # Only send output to the specified channel
    if CHANNEL_ID:
        channel = ctx.guild.get_channel(int(CHANNEL_ID))
        if channel and channel.permissions_for(ctx.guild.me).send_messages:
            message = random.choice(luck_messages)
            await channel.send(f"{ctx.author.mention} {message}")
            #await channel.send("nice ^")
            
#@bot.event
#async def on_message(message):
#    # Only print messages from the specified channel
#    if CHANNEL_ID and str(message.channel.id) == str(CHANNEL_ID):
#        print(f"[CHANNEL {CHANNEL_ID}] {message.author}: {message.content}")
#    await bot.process_commands(message)

        
if __name__ == "__main__":
    bot.run(TOKEN)
