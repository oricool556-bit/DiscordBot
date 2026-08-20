import os
import discord
from discord.ext import commands
import asyncio
from flask import Flask
from threading import Thread

# ==========================================
# 🌐 טריק ההשכמה (שומר על הבוט ער בענן) 🌐
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "הבוט של מיקמק עובד באוויר!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 🤖 קוד הבוט המקורי 🤖
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MAIN_FOLDER = "images" 

@bot.event
async def on_ready():
    print(f"הבוט התחבר בתור {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!"):
        command_word = message.content[1:].strip()
        target_path = os.path.join(MAIN_FOLDER, command_word)
        
        if os.path.isdir(target_path):
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            
            found_images = []
            try:
                for filename in os.listdir(target_path):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        found_images.append(filename)
            except Exception as e:
                print(f"❌ שגיאה בקריאת התיקייה: {e}")
            
            if not found_images:
                await message.channel.send(f"החדר '{command_word}' עדיין ריק מאובייקטים.", delete_after=5)
                return
            
            try:
                overwrites = {
                    message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    message.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    message.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, manage_channels=True)
                }
                
                channel_safe_name = command_word.replace(" ", "-")
                channel_name = f"אובייקטים-{channel_safe_name}-{message.author.name}"
                new_channel = await message.guild.create_text_channel(channel_name, overwrites=overwrites)
                
                await message.channel.send(f"פתחתי לך חדר פרטי עם כל האובייקטים כאן: {new_channel.mention}", delete_after=5)
                
                await new_channel.send(f"היי {message.author.mention}, מצאתי **{len(found_images)}** אובייקטים ב{command_word} בשבילך:")
                
                for filename in found_images:
                    file_path = os.path.join(target_path, filename)
                    file = discord.File(file_path)
                    await new_channel.send(file=file)
                    
                await new_channel.send("⏳ **יש לך 10 דקות לשמור את האובייקטים לפני שהחדר ייסגר אוטומטית!**")
                await asyncio.sleep(600)
                await new_channel.delete()
                
            except Exception as e:
                print(f"❌ שגיאה: {e}")
                await message.channel.send("משהו השתבש, תבדוק את חלון הטרמינל!", delete_after=10)

    await bot.process_commands(message)

# מפעילים את שעון ההשכמה
keep_alive()

# מפעילים את הבוט מתוך הענן באופן מאובטח (ללא הטוקן הגלוי)
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ הטוקן חסר כי אנחנו עובדים במצב מאובטח לענן! נכניס אותו בהמשך דרך ההגדרות של Render.")