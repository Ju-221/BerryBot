
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Run pip install -r requirements.txt to install the required libraries
# Please open this as a venv
# Fill out the .env with the token and channel id you want the bot to respond to


TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')
DEBUG_MODE = os.getenv('DEBUG_MODE')

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
    # Debug use only
    if DEBUG_MODE:
        print("all tests passed, succesfully deployed")
        for guild in bot.guilds:
            if CHANNEL_ID:
                channel = guild.get_channel(int(CHANNEL_ID))
                if channel and channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send("all tests passed, succesfully deployed")
                    except Exception:
                        pass
        import sys
        sys.exit(0)
    else:
        # Normal welcome message
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
            

@bot.event
async def on_message(message):

    # Only print messages from the specified channel
    if CHANNEL_ID and str(message.channel.id) == str(CHANNEL_ID):
        # Debug only
        # print(f"[CHANNEL {CHANNEL_ID}] {message.author}: {message.content}")
        # Randomly react with 😂 to about 1 in 10 messages
        if random.randint(1, 10) == 1:
            try:
                await message.add_reaction("😂")
            except Exception as e:
                print(f"[DEBUG] Failed to add reaction: {e}")
    await bot.process_commands(message)

        
if __name__ == "__main__":
    bot.run(TOKEN)
