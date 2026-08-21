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
# 🤖 קוד הבוט המשודרג 🤖
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MAIN_FOLDER = "images" 
channel_deadlines = {}
user_cooldowns = {} # זיכרון למערכת ההגבלות

COOLDOWN_TIME = 180 # זמן המתנה בין פתיחת חדרים (בשניות) - כרגע 3 דקות

# --- מחלקה ליצירת הכפתור האינטראקטיבי ---
class TimeButton(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="הוסף 5 דקות", style=discord.ButtonStyle.green, emoji="⏳")
    async def add_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.channel_id in channel_deadlines:
            channel_deadlines[self.channel_id] += 300 # הוספת 5 דקות (300 שניות)
            await interaction.response.send_message(f"⏳ {interaction.user.mention} **הוסיף/ה עוד 5 דקות לזמן החדר!**", ephemeral=False)
        else:
            await interaction.response.send_message("❌ הזמן כבר נגמר או שהחדר נסגר.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"הבוט התחבר בתור {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # === טיפול בבקשות לפתיחת חדר ===
    if message.content.startswith("!"):
        command_word = message.content[1:].strip()
        target_path = os.path.join(MAIN_FOLDER, command_word)
        
        # בדיקה אם יש תיקייה בשם הזה
        if os.path.isdir(target_path):
            try:
                await message.delete() # מחיקת הודעת הפקודה כדי לשמור על סדר
            except discord.Forbidden:
                pass

            # --- מערכת Cooldown (הגבלת זמן) ---
            user_id = message.author.id
            current_time = time.time()
            if user_id in user_cooldowns:
                time_passed = current_time - user_cooldowns[user_id]
                if time_passed < COOLDOWN_TIME:
                    wait_time = int(COOLDOWN_TIME - time_passed)
                    await message.channel.send(f"⚠️ {message.author.mention}, אנא המתן עוד **{wait_time} שניות** לפני שתוכל לפתוח חדר חדש.", delete_after=7)
                    return
            
            # רושמים את הזמן הנוכחי שבו המשתמש פתח את החדר
            user_cooldowns[user_id] = current_time
            # -----------------------------------
            
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
                # הגדרת הרשאות - החדר פרטי לחלוטין
                overwrites = {
                    message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    message.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    message.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, manage_channels=True)
                }
                
                channel_safe_name = command_word.replace(" ", "-")
                channel_name = f"אובייקטים-{channel_safe_name}-{message.author.name}"
                new_channel = await message.guild.create_text_channel(channel_name, overwrites=overwrites)
                
                await message.channel.send(f"פתחתי לך חדר פרטי עם כל האובייקטים כאן: {new_channel.mention}", delete_after=5)
                
                # --- שליחת דיווח לחדר הלוגים ---
                # חובה ליצור בדיסקורד ערוץ טקסט בשם בדיוק: לוג-בוט
                log_channel = discord.utils.get(message.guild.channels, name="לוג-בוט")
                if log_channel:
                    await log_channel.send(f"📝 **תיעוד:** {message.author.mention} פתח/ה חדר לאובייקט `{command_word}`.")
                # --------------------------------

                await new_channel.send(f"היי {message.author.mention}, מצאתי **{len(found_images)}** אובייקטים ב{command_word} בשבילך:")
                
                for filename in found_images:
                    file_path = os.path.join(target_path, filename)
                    file = discord.File(file_path)
                    await new_channel.send(file=file)
                    
                # צירוף הכפתור להודעת הסיום
                view = TimeButton(new_channel.id)
                await new_channel.send("⏳ **יש לך חמש עשרה דקות עד שהחדר נסגר אז כדאי לקחת את התמונות לפני שהזמן יגמר!**", view=view)
                
                # מערכת הספירה לאחור של החדר
                channel_deadlines[new_channel.id] = time.time() + 900
                
                while time.time() < channel_deadlines.get(new_channel.id, 0):
                    await asyncio.sleep(5)
                
                # מחיקת החדר בסיום הזמן
                try:
                    await new_channel.delete()
                except:
                    pass
                
                if new_channel.id in channel_deadlines:
                    del channel_deadlines[new_channel.id]
                
            except Exception as e:
                print(f"❌ שגיאה: {e}")
                await message.channel.send("ימטומטם משהו השתבש תחזור לטרמינל", delete_after=10)

    await bot.process_commands(message)

# מפעילים את שעון ההשכמה
keep_alive()

# התחברות לדיסקורד
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ הטוקן חסר! נא להוסיף ל-Environment Variables.")