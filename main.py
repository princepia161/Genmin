import os
import sys
import asyncio
import urllib.request
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import pyromod.listen
import core as helper
from app import generate_drm_keys

# ===== ADVANCE CONFIGURATION =====
API_ID = 35822069
API_HASH = '35cea1c5e6384f57e914ac982ff5ffd1'
BOT_TOKEN = os.environ.get("8338892359:AAFQ9LctB2s_Efp3ULPLdW9RvOVFCHYWIHg") 

# ⚠️ APNI NAYI ID YAHAN DALO! 
# Telegram par @userinfobot ko message karke apni ID pata karo.
OWNER_ID = [890749443, 5938871512] # Purani ID aur apni Nayi ID yahan likho

# in_memory=True is the key to stability on Railway
bot = Client("ProDownloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# ===== DEBUG & SECURITY =====
@bot.on_message(filters.all)
async def debug_log(bot, m: Message):
    # Logs mein dekho kya message mil raha hai
    print(f"DEBUG: Message from {m.chat.id}: {m.text or 'File'}")

@bot.on_message(filters.command(["start"]) & filters.user(OWNER_ID))
async def start_command(bot: Client, message: Message):
    await message.reply_text("✅ **Bot is Alive and Authenticated!**\nSend /txt to start downloading.")

# ===== MAIN BATCH DOWNLOADER =====
@bot.on_message(filters.command(["txt"]) & filters.user(OWNER_ID))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("⚡ **Send the .txt file (As Document)** ⚡")
    try:
        input_msg: Message = await bot.listen(editable.chat.id, timeout=300)
        
        if not input_msg.document:
            await editable.edit("❌ **Error:** Please send a .txt FILE, not text or image.")
            return

        x = await input_msg.download()
        await input_msg.delete(True)
        
        with open(x, "r", encoding="utf-8") as f:
            links = [line.split("://", 1) for line in f.read().splitlines() if "://" in line]
        os.remove(x)

        # Inputs
        await editable.edit("📚 **Batch Name?** (Send 1 for default)")
        b_name_m = await bot.listen(editable.chat.id)
        b_name = "Course" if b_name_m.text == '1' else b_name_m.text
        
        await editable.edit("**📸 Resolution?** (e.g. 720)")
        res_m = await bot.listen(editable.chat.id)
        raw_res = res_m.text
        
        await editable.edit("**Token?**")
        tok_m = await bot.listen(editable.chat.id)
        cp_token = tok_m.text
        
        await editable.delete()

        # Processing Loop
        for i, link_data in enumerate(links):
            url = "https://" + link_data[1].replace("master.m3u8", "master.mpd")
            name = f"{i+1}) {link_data[0][:50]}"
            
            prog = await m.reply(f"⬇️ **Downloading:** {name}")
            
            # DRM & Normal Logic
            if "classplus" in url or "cpvod" in url:
                drm_data = generate_drm_keys(url, cp_token)
                if "error" in drm_data:
                    await prog.edit(f"❌ **DRM Error:** {drm_data['error']}")
                    continue
                keys_str = " ".join([f"--key {k}" for k in drm_data['keys']])
                res_file = await helper.decrypt_and_merge_video(drm_data["mpd_url"], keys_str, "./downloads/", name, raw_res)
            else:
                cmd = f'yt-dlp -f "bv+ba/b" "{url}" -o "{name}.mp4"'
                res_file = await helper.download_video(url, cmd, name)
            
            await helper.send_vid(bot, m, "Done", res_file, "no", name, prog)
            await prog.delete()
                
    except Exception as e:
        await m.reply_text(f"‼️ **Failed:** {e}")

bot.run()
