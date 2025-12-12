import discord
from discord.ext import commands
import json
from datetime import datetime
import pytz
import asyncio # New import for running two loops concurrently
import random

# --- Configuration ---

# 1. Use the commands.Bot class (Standard for prefix commands)
# 2. You MUST keep intents.message_content = True for !status, !lessons, and !hello to work.
intents = discord.Intents.default()
intents.message_content = True 

# Create the bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Define your timezone (IMPORTANT for accurate checking)
TIMEZONE = pytz.timezone('Europe/London')
SCHEDULE_FILE = 'sched.json'

# Define the channel ID where the bot should send messages from the terminal
TARGET_CHANNEL_ID = 1448683440831598808 


# --- Helper Functions (No changes needed here) ---

def is_currently_in_class(schedule_data):
    """
    Checks the schedule to see if the current time falls within any class slot.
    Returns: (is_in_class: bool, course_name: str or None)
    """
    now = datetime.now(TIMEZONE)
    current_day = now.strftime('%A')
    current_time = now.time()

    today_schedule = schedule_data.get(current_day, [])

    for class_slot in today_schedule:
        try:
            start_time = datetime.strptime(class_slot['start'], '%H:%M').time()
            end_time = datetime.strptime(class_slot['end'], '%H:%M').time()

            if start_time <= current_time <= end_time:
                return True, class_slot['course']
        except ValueError as e:
            print(f"Error parsing time in schedule: {e}")
            continue

    return False, None


def get_todays_schedule_list(schedule_data):
    """
    Retrieves and formats the schedule for the current day.
    """
    now = datetime.now(TIMEZONE)
    
    # FIX: Use now.tzname() to get the timezone name from the aware datetime object
    tz_name = now.tzname() 

    current_day = now.strftime('%A')
    
    today_schedule = schedule_data.get(current_day, [])

    if not today_schedule:
        return f"no lessons for **{current_day}**"

    # Build the formatted list
    schedule_lines = [f"**lessons for {current_day} (Time Zone: {tz_name}):**"]
    
    for class_slot in today_schedule:
        start = class_slot['start']
        end = class_slot['end']
        course = class_slot['course']
        
        schedule_lines.append(f"• **{start} - {end}**: {course}")
        
    return "\n".join(schedule_lines)


# --- Terminal Input Function (Modified for Shutdown Message) ---

async def run_terminal_input():
    """
    Asynchronously listens for input in the terminal and executes commands.
    """
    await bot.wait_until_ready() # Wait until the bot is logged in and ready

    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel is None:
        print(f"\n[TERMINAL] ERROR: Could not find channel with ID {TARGET_CHANNEL_ID}. Check the ID and ensure the bot is in the server.")
        return

    print("\n[TERMINAL] Bot is running. Type 'say [message]' to send a message to the target channel.")
    
    # Run a loop to continuously listen for terminal input
    while not bot.is_closed():
        try:
            # Use loop.run_in_executor to safely handle the blocking 'input()' function
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, input)
            
            if user_input.lower().startswith('say '):
                message_content = user_input[4:].strip()
                if message_content:
                    print(f"[TERMINAL] Sending message: '{message_content}' to #{channel.name}")
                    await channel.send(message_content)
                else:
                    print("[TERMINAL] 'say' command requires a message.")
            elif user_input.lower() == 'quit':
                # --- SHUTDOWN MESSAGE IMPLEMENTATION ---
                print("[TERMINAL] Sending shutdown message...")
                await channel.send(f"bot is shutting down Goodbye!")
                # --- END SHUTDOWN MESSAGE ---
                print("[TERMINAL] Shutting down bot...")
                await bot.close()
                break
            elif user_input.strip():
                print(f"[TERMINAL] Unknown command: {user_input}")

        except Exception as e:
            print(f"[TERMINAL] An error occurred: {e}")
            await asyncio.sleep(1) # Wait a bit before retrying


# --- New Feature: Hourly Message Loop ---

hamsterImgs = [
    "https://cdn.discordapp.com/attachments/1448683440831598808/1448704528357658815/e73cd4ddca957c0794be7e140f052990.jpg?ex=693c3abb&is=693ae93b&hm=d2c9268b3b67de733a57122ba968bed12dfbebdc2e2ac76091db0407a90902a3&",
    "https://cdn.discordapp.com/attachments/1447116715044507760/1448318554289082408/4fe33d5dbe2ec0a0e06f1c3fdb4f223a.jpg?ex=693ccd83&is=693b7c03&hm=1426c9f7fe342d067b7f9c8919870cf1a2ca1c157735a8aca87a7361b72c8bda&",
    "https://cdn.discordapp.com/attachments/1447116715044507760/1448315205225287680/4f55979bf27ca414e71b2293f3cedc18.jpg?ex=693cca65&is=693b78e5&hm=29ca4cf126c6204ecdfe76b1da62964cf54f98381336c48e78f6c6378a9b71bc&",
    "https://cdn.discordapp.com/attachments/1447116715044507760/1447968286930112624/fa6bfcce972a6135e38bfd9a439401bb.jpg?ex=693cd8cd&is=693b874d&hm=6730e70124a51f07a98a5b3e8f7f60ed19e804ecae86865d520543205f88dfd6&",
    "https://cdn.discordapp.com/attachments/1447116715044507760/1447945351066550272/d6a5508bd631a1043b66f443d066e4ab.jpg?ex=693cc371&is=693b71f1&hm=f712300334ae101dd86d928bb531f645594dc87fe7a12f803c37cb0dd2721161&",
    "https://cdn.discordapp.com/attachments/1447116715044507760/1447881640645754890/3ff44c37ce8c905a57c107c3d3c8842d.jpg?ex=693c881b&is=693b369b&hm=9d52d42ec422e9850e8964a4e672ae4ab7352b1c610f4938964f812120454c3d&",
    "https://cdn.discordapp.com/attachments/1447116715044507760/1447879240887304214/9d27876501e96ebef7604c451db0ed34_1.jpg?ex=693c85df&is=693b345f&hm=75c74e5b335bee60d8f7b9608e726eb6c791ed7e6f079e1e8c3a614105dbf89c&",
    "https://cdn.discordapp.com/attachments/1447116715044507760/1447869141137756261/ef3a31c80a1a3fbdbe6b561d13f302b2.jpg?ex=693c7c77&is=693b2af7&hm=33a464eb5b7cf61b0cad84e64ccbc06e45ff1ead0fc9fe23338ac67b240c3167&",
    "https://cdn.discordapp.com/attachments/1447116715044507760/1447142312881950740/98e9045249478573da6c361a03c560b2.jpg?ex=693c7a8d&is=693b290d&hm=7161b6543ba7ce1ffa0c3de92a771881f7457f0738f30947658e2a969120e92e&",
    "https://cdn.discordapp.com/attachments/1447116715044507760/1447138213964681288/jollyham.jpg?ex=693c76bc&is=693b253c&hm=36c8ed75fc6086d543ce20dfe197e572c41a608d7379774391c81a946819b965&"
]

async def hourly_message_loop():
    """
    A persistent task that sends a message to the target channel every hour.
    """
    await bot.wait_until_ready()
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel is None:
        print(f"[HOURLY] ERROR: Could not find channel with ID {TARGET_CHANNEL_ID}. Hourly message will not run.")
        return

    # Wait until the start of the next hour to align the messages
    now = datetime.now(TIMEZONE)
    # Calculate seconds until the next hour (e.g., 5:59:30 -> 6:00:00)
    minutes_to_wait = 60 - now.minute
    seconds_to_wait = minutes_to_wait * 60 - now.second

    print(f"[HOURLY] Waiting {seconds_to_wait} seconds to align with the next hour.")
    await asyncio.sleep(seconds_to_wait)

    while not bot.is_closed():
        try:
            now_hourly = datetime.now(TIMEZONE)
            current_time_str = now_hourly.strftime('%H:%M')
            arrayIndex = random.randint(0, 9)
            
            # Message content could include status or just a simple time check
            status_message = hamsterImgs(arrayIndex)
            
            await channel.send(status_message)
            print(f"[HOURLY] Sent message at {current_time_str}")

            # Wait for exactly 1 hour (3600 seconds)
            await asyncio.sleep(3600)
            
        except Exception as e:
            print(f"[HOURLY] An error occurred in the loop: {e}")
            await asyncio.sleep(60) # Wait a minute before trying again


# --- Bot Events (Modified for Startup Message) ---

@bot.event
async def on_ready():
    print(f'entered the mainframe as {bot.user}')

    # --- STARTUP MESSAGE IMPLEMENTATION ---
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        startup_time = datetime.now(TIMEZONE).strftime('%H:%M:%S %Z')
        await channel.send(f"super cool bot is online. Startup time: {startup_time}")
    else:
        print(f"[STARTUP] WARNING: Could not send startup message to channel {TARGET_CHANNEL_ID} (Channel not found).")
    # --- END STARTUP MESSAGE ---

    # Start the terminal input listener when the bot is ready
    bot.loop.create_task(run_terminal_input())
    
    # Start the new hourly message task
    bot.loop.create_task(hourly_message_loop())


@bot.event
async def on_message(message):
    # (Existing on_message logic remains the same)
    if message.author == bot.user:
        return

    # 1. Handle the existing $hello command
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
        return 

    # --- Common Schedule Loading Block ---
    if message.content.startswith('!status') or message.content.startswith('!lessons'):
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                schedule_data = json.load(f)

        except FileNotFoundError:
            await message.channel.send(f" err: The schedule file (`{SCHEDULE_FILE}`) was not found. Please contact the bot owner.")
            return
        except json.JSONDecodeError:
            await message.channel.send("err: Could not read the schedule. Check if the JSON file is correctly formatted.")
            return
        except Exception as e:
            await message.channel.send(f"err An unexpected error occurred: {e}")
            return
            
        # 2. Handle the !status command
        if message.content.startswith('!status'):
            in_class, course_name = is_currently_in_class(schedule_data)
            now_local = datetime.now(TIMEZONE)

            if in_class:
                response = f" **in college** doing **{course_name}**."
            else:
                formatted_time = now_local.strftime('%A at %H:%M')
                tz_name = now_local.tzname()
                response = f" **not at college** (Checked at {formatted_time} {tz_name})"

            await message.channel.send(response)
        
        # 3. Handle the !lessons command
        elif message.content.startswith('!lessons'):
            lessons_response = get_todays_schedule_list(schedule_data)
            await message.channel.send(lessons_response)

    # Required: This line tells the bot to also process commands defined 
    # with @bot.command()
    await bot.process_commands(message) 

# --- Run the Bot ---
# Note: Ensure you have replaced the token with your VALID bot token.
# IMPORTANT: You can now use 'quit' in the terminal to stop the bot.
bot.run('MTQ0ODY2OTc1MDg2MjI4NzAyMg.GxiVAF.9qv0elbyDnKgmLnGzMLJ4zG3WIU8lsAhFOa0DI')
