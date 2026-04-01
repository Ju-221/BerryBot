import json
import os
import random
from datetime import datetime, timedelta

#hot take generator: it starts a thread every 2 hours and whoever wins the thread 
HOT_TAKE_HOURS = [10, 14, 18, 20]
HOT_TAKE_DURATION = timedelta(hours=2)

_state_file = "hot_take_state.txt"
_state_loaded = False
_hot_take_state = {
    "created_slots": [],
    "active_threads": {}
}

_hot_take_prompts = [
    {
        "topic": "Food",
        "take": "Hot take: fries are better with vinegar than ketchup."
    },
    {
        "topic": "Gaming",
        "take": "Hot take: short games are usually better than 100-hour games."
    },
    {
        "topic": "Music",
        "take": "Hot take: the opener is often better than the headliner."
    },
    {
        "topic": "Tech",
        "take": "Hot take: fewer features usually means a better product."
    },
    {
        "topic": "Movies",
        "take": "Hot take: the sequel is sometimes better than the original."
    }
]


def configure(state_file=None):
    global _state_file
    if state_file:
        _state_file = state_file


def ensure_loaded(state_file=None):
    global _state_loaded
    configure(state_file)
    if _state_loaded:
        return
    load_hot_take_state()
    _state_loaded = True


def load_hot_take_state():
    global _hot_take_state
    if not os.path.exists(_state_file):
        return

    try:
        with open(_state_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            _hot_take_state["created_slots"] = loaded.get("created_slots", [])
            _hot_take_state["active_threads"] = loaded.get("active_threads", {})
    except Exception as e:
        print(f"[HOT_TAKE] Failed to load state file: {e}")


def save_hot_take_state():
    try:
        with open(_state_file, "w", encoding="utf-8") as f:
            json.dump(_hot_take_state, f, indent=2)
    except Exception as e:
        print(f"[HOT_TAKE] Failed to save state file: {e}")


def _current_slot_key(now):
    return now.strftime("%Y-%m-%d-%H")


def _parse_created_at(timestamp):
    try:
        return datetime.fromisoformat(timestamp)
    except Exception:
        return None


def _get_configured_channel(bot, channel_id):
    if not channel_id:
        return None

    try:
        target_channel_id = int(channel_id)
    except ValueError:
        return None

    for guild in bot.guilds:
        channel = guild.get_channel(target_channel_id)
        if channel and channel.permissions_for(guild.me).send_messages:
            return channel
    return None


async def _create_hot_take_thread(channel):
    prompt = random.choice(_hot_take_prompts)
    now = datetime.now()
    thread_title = f"hot-take-{now.strftime('%m%d-%H%M')}"

    opener = await channel.send(
        f"Hot Take starts now! Topic: **{prompt['topic']}**\n"
        "Thread lasts 2 hours. Reply in thread for points."
    )
    thread = await opener.create_thread(name=thread_title)

    await thread.send(
        f"{prompt['take']}\n"
        "Scoring rules:\n"
        "- Message length must be more than 20 and less than 1000 characters\n"
        "- Earn a random 1-100 points per valid message\n"
        "- Per user, awarded points are capped at 1000 per second\n"
        "Winner is announced after 2 hours."
    )

    _hot_take_state["active_threads"][str(thread.id)] = {
        "thread_id": thread.id,
        "parent_channel_id": channel.id,
        "created_at": now.isoformat(),
        "topic": prompt["topic"],
        "hot_take": prompt["take"],
        "scores": {},
        "replied_users": [],
        "points_per_user_second": {},
        "winner_announced": False
    }
    save_hot_take_state()


async def _close_finished_hot_take_threads(bot):
    now = datetime.now()

    for thread_id, info in list(_hot_take_state.get("active_threads", {}).items()):
        if info.get("winner_announced"):
            continue

        created_at = _parse_created_at(info.get("created_at", ""))
        if not created_at:
            info["winner_announced"] = True
            continue

        if now - created_at < HOT_TAKE_DURATION:
            continue

        channel = bot.get_channel(int(thread_id))
        if channel is None:
            try:
                channel = await bot.fetch_channel(int(thread_id))
            except Exception:
                channel = None

        scores = info.get("scores", {})
        if not scores:
            result_msg = "Hot Take finished. No valid entries this round."
        else:
            winning_user_id, winning_points = max(
                scores.items(), key=lambda item: item[1]
            )
            result_msg = (
                f"Hot Take winner: <@{winning_user_id}> with "
                f"**{winning_points}** points!"
            )

        if channel:
            try:
                await channel.send(result_msg)
            except Exception:
                pass

        info["winner_announced"] = True

    save_hot_take_state()


async def scheduler_tick(bot, channel_id):
    channel = _get_configured_channel(bot, channel_id)
    if not channel:
        return

    now = datetime.now()
    if now.hour in HOT_TAKE_HOURS and now.minute == 0:
        slot = _current_slot_key(now)
        if slot not in _hot_take_state["created_slots"]:
            try:
                await _create_hot_take_thread(channel)
                _hot_take_state["created_slots"].append(slot)
                save_hot_take_state()
            except Exception as e:
                print(f"[HOT_TAKE] Failed to create thread: {e}")

    await _close_finished_hot_take_threads(bot)


async def start_hot_take_now(bot, channel_id):
    channel = _get_configured_channel(bot, channel_id)
    if not channel:
        return False

    await _create_hot_take_thread(channel)
    return True


async def handle_message(message):
    thread_info = _hot_take_state["active_threads"].get(str(message.channel.id))
    if not thread_info or thread_info.get("winner_announced"):
        return

    msg_len = len(message.content or "")
    if not (20 < msg_len < 1000):
        return

    now_sec = int(datetime.now().timestamp())
    user_id_str = str(message.author.id)
    rate_key = f"{user_id_str}:{now_sec}"

    already_awarded_this_second = thread_info["points_per_user_second"].get(rate_key, 0)
    if already_awarded_this_second >= 1000:
        return

    points = random.randint(1, 100)
    allowed_points = min(points, 1000 - already_awarded_this_second)
    if allowed_points <= 0:
        return

    current_total = thread_info["scores"].get(user_id_str, 0)
    thread_info["scores"][user_id_str] = current_total + allowed_points
    thread_info["points_per_user_second"][rate_key] = (
        already_awarded_this_second + allowed_points
    )

    if user_id_str not in thread_info["replied_users"]:
        thread_info["replied_users"].append(user_id_str)

    try:
        await message.channel.send(
            f"<@{user_id_str}> +{allowed_points} points "
            f"(total: {thread_info['scores'][user_id_str]})"
        )
    except Exception:
        pass

    save_hot_take_state()


def is_active_hot_take_thread(channel_id):
    thread_info = _hot_take_state["active_threads"].get(str(channel_id))
    return bool(thread_info and not thread_info.get("winner_announced"))


def get_user_points(channel_id, user_id):
    thread_info = _hot_take_state["active_threads"].get(str(channel_id))
    if not thread_info:
        return None

    scores = thread_info.get("scores", {})
    return scores.get(str(user_id), 0)
