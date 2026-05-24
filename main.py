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

# ===== CONFIG =====
API_ID = 20807000
API_HASH = 'cde2366a7c61e23f4cb44618cbe6cf70'
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE' # ⚠️ यहाँ अपना टोकन डालें
OWNER_ID = [5938871512, 890749443] 

bot = Client("ProDownloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# 🛡️ DEBUG MODE: यह पता लगाने के लिए कि बॉट मैसेज देख रहा है या नहीं
@bot.on_message(filters.all)
async def debug_all_messages(bot, m: Message):
    print(f"DEBUG: Message received from {m.chat.id}: {m.text}")

# ===== COMMANDS =====
@bot.on_message(filters.command(["start"]) & filters.user(OWNER_ID))
async def start_command(bot: Client, message: Message):
    await message.reply_text("✅ **Bot is Working!** Send /txt to start.")

@bot.on_message(filters.command(["txt"]) & filters.user(OWNER_ID))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("⚡ **Send your .txt file** ⚡")
    try:
        input_msg: Message = await bot.listen(editable.chat.id, timeout=300)
        if not input_msg.document:
            await editable.edit("❌ **Error:** Please send as a FILE/DOCUMENT.")
            return

        x = await input_msg.download()
        await input_msg.delete(True)
        
        with open(x, "r", encoding="utf-8") as f:
            links = [line.split("://", 1) for line in f.read().splitlines() if "://" in line]
        os.remove(x)

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

        for i, link_data in enumerate(links):
            url = "https://" + link_data[1].replace("master.m3u8", "master.mpd")
            name = f"{i+1}) {link_data[0][:50]}"
            
            prog = await m.reply(f"⬇️ **Downloading:** {name}")
            
            # DRM LOGIC
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
