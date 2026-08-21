import os
import time
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

# מילון ששומר את זמני הסגירה של כל חדר
channel_deadlines = {}

@bot.event
async def on_ready():
    print(f"הבוט התחבר בתור {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # === הוספת זמן לחדר (פקודת !עוד 5) ===
    if message.content.strip() == "!עוד 5":
        if message.channel.id in channel_deadlines:
            channel_deadlines[message.channel.id] += 300 # הוספת 5 דקות (300 שניות)
            try:
                await message.delete() # מחיקת הודעת הבקשה
            except:
                pass
            await message.channel.send("⏳ **קיבלת! הוספתי עוד 5 דקות לזמן החדר.**", delete_after=5)
        return

    # === יצירת החדר והבאת האובייקטים ===
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
                    
                await new_channel.send("⏳ **יש לך חמש עשרה דקות עד שהחדר נסגר אז כדאי לקחת את התמונות לפני שהזמן יגמר!**\n💡 *(טיפ: אפשר לכתוב פה בחדר `!עוד 5` כדי להוסיף עוד זמן)*")
                
                # קביעת שעת הסגירה הראשונית
                channel_deadlines[new_channel.id] = time.time() + 900
                
                # הבוט יבדוק כל 5 שניות אם השעה הנוכחית עברה את שעת הסגירה
                while time.time() < channel_deadlines.get(new_channel.id, 0):
                    await asyncio.sleep(5)
                
                # ברגע שהזמן עבר - מוחקים את החדר ומנקים אותו מהזיכרון
                try:
                    await new_channel.delete()
                except:
                    pass
                
                if new_channel.id in channel_deadlines:
                    del channel_deadlines[new_channel.id]
                
            except Exception as e:
                print(f"❌ שגיאה: {e}")
                await message.channel.send("ימטומטם עשית משהו לא נכון תחזור לטרמינל", delete_after=10)

    await bot.process_commands(message)

# מפעילים את שעון ההשכמה
keep_alive()

# מפעילים את הבוט מתוך הענן באופן מאובטח
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ הטוקן חסר! נא להוסיף ל-Environment Variables.")