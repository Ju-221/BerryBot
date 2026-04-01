import os
import random
import discord
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv
import hot_take_feature

# Load environment variables from .env file
load_dotenv()


# Run pip install -r requirements.txt to install the required libraries
# Please open this as a venv
# Fill out the .env with the token and channel id you want the bot to respond to

# .env stuff, see .env.example for reference
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')
DEBUG_MODE = os.getenv('DEBUG_MODE')
SPECIAL_USER_ID = os.getenv('SPECIAL_USER_ID')
try:
    BOT_ROLE_ID = int(os.getenv('BOT_ROLE_ID', '1208193044550123621'))
except ValueError:
    BOT_ROLE_ID = 1208193044550123621
try:
    HOT_TAKE_ADMIN_ROLE_ID = int(os.getenv('HOT_TAKE_ADMIN_ROLE_ID', '1122000921572933653'))
except ValueError:
    HOT_TAKE_ADMIN_ROLE_ID = 1122000921572933653


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
    " https://pbs.twimg.com/media/Fmp4xtEagAM8g4U.jpg",
    " https://static.klipy.com/ii/935d7ab9d8c6202580a668421940ec81/ef/dc/kSso1Wmq.gif"
]


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


# Task: send 'meow' at random intervals averaging 4 hours
@tasks.loop(hours=1)
async def meow_task():
    # Only run if bot is ready and channel is set
    if CHANNEL_ID:
        # 1 in 4 chance every hour (on average every 4 hours)
        if random.randint(1, 4) == 1:
            for guild in bot.guilds:
                channel = guild.get_channel(int(CHANNEL_ID))
                if channel and channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send("meow")
                    except Exception:
                        pass


@tasks.loop(minutes=1)
async def hot_take_scheduler_task():
    await hot_take_feature.scheduler_tick(bot, CHANNEL_ID)


@tasks.loop(minutes=10)
async def hot_take_persist_task():
    hot_take_feature.save_hot_take_state()



@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    hot_take_feature.ensure_loaded(os.getenv('HOT_TAKE_STATE_FILE', 'hot_take_state.txt'))

    if not meow_task.is_running():
        meow_task.start()
    if not hot_take_scheduler_task.is_running():
        hot_take_scheduler_task.start()
    if not hot_take_persist_task.is_running():
        hot_take_persist_task.start()

    if DEBUG_MODE:
        print("all tests passed, succesfully deployed")
    else:
        # Send welcome message to the channel
        for guild in bot.guilds:
            if CHANNEL_ID:
                channel = guild.get_channel(int(CHANNEL_ID))
                if channel and channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send("berrie connected: nice chat")
                    except Exception:
                        pass



special_responses = ["nope", "not feeling like it"]

@bot.command()
async def fortune(ctx):
    # Prevent responding to itself or any user with the Bot role
    if ctx.author == bot.user:
        return
    if hasattr(ctx.author, 'roles') and any(getattr(role, 'id', None) == BOT_ROLE_ID for role in getattr(ctx.author, 'roles', [])):
        return
    # Only send output to the specified channel
    if CHANNEL_ID:
        channel = ctx.guild.get_channel(int(CHANNEL_ID))
        if channel and channel.permissions_for(ctx.guild.me).send_messages:
            is_special_user = (
                SPECIAL_USER_ID and str(ctx.author.id) == str(SPECIAL_USER_ID)
            )
            # special user that has a 1 in 20 chance of getting a special response instead of a luck message
            if is_special_user:
                if random.randint(1, 20) == 1:
                    message = random.choice(luck_messages)
                    await channel.send(
                        f"{message}"
                    )
                else:
                    await channel.send(
                        f"{random.choice(special_responses)}"
                    )
            else:
                message = random.choice(luck_messages)
                await channel.send(
                    f"{message}"
                )


@bot.command()
async def points(ctx):
    if ctx.author == bot.user:
        return
    if hasattr(ctx.author, 'roles') and any(getattr(role, 'id', None) == BOT_ROLE_ID for role in getattr(ctx.author, 'roles', [])):
        return

    if not hot_take_feature.is_active_hot_take_thread(ctx.channel.id):
        return

    user_points = hot_take_feature.get_user_points(ctx.channel.id, ctx.author.id)
    if user_points is None:
        return

    await ctx.send(f"<@{ctx.author.id}> you have **{user_points}** points in this thread.")


@bot.command()
async def hottake(ctx):
    if ctx.author == bot.user:
        return

    is_hot_take_admin = (
        hasattr(ctx.author, 'roles') and
        any(getattr(role, 'id', None) == HOT_TAKE_ADMIN_ROLE_ID for role in getattr(ctx.author, 'roles', []))
    )
    if not is_hot_take_admin:
        return

    started = await hot_take_feature.start_hot_take_now(bot, CHANNEL_ID)
    if started:
        await ctx.send("Hot take thread started.")
    else:
        await ctx.send("Could not start hot take thread. Check channel configuration.")
            

@bot.event
async def on_message(message):
    # Prevent responding to itself or any user with the Bot role
    if message.author == bot.user:
        return
    if hasattr(message.author, 'roles') and any(getattr(role, 'id', None) == BOT_ROLE_ID for role in getattr(message.author, 'roles', [])):
        return
    # Always process commands
    await bot.process_commands(message)
    await hot_take_feature.handle_message(message)

    # Only print messages from the specified channel (for non-command reactions)

    if CHANNEL_ID and str(message.channel.id) == str(CHANNEL_ID):
        # Only react to non-command messages (not starting with '!')
        if not message.content.startswith('!'):
            content_lower = message.content.lower()
            response = None
            debug_case = None
            if "maybe" in content_lower:
                response = "maybe stfu?"
                debug_case = "maybe"
            elif "what" in content_lower:
                response = "what?"
                debug_case = "what"
            elif "67" in content_lower:
                response = "⁶🤷‍♀️⁷"
                debug_case = "67"
            elif "mpreg" in content_lower:
                response = "🫃"
                debug_case = "mpreg"
            if response:
                try:
                    await message.channel.send(
                        response
                    )
                except Exception as e:
                    print(f"[DEBUG][{debug_case}] Failed to send '{response}': {e}")

            # Randomly react with 😂 to about 1 in 10 messages
            if random.randint(1, 10) == 1:
                try:
                    await message.add_reaction("😂")
                except Exception as e:
                    print(f"[DEBUG] Failed to add reaction: {e}")

#if there's an error with a command, print it out instead of crashing the bot
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        print(f"command unrecognized {ctx.message.content}")
    else:
        raise error

if __name__ == "__main__":
    bot.run(TOKEN)
