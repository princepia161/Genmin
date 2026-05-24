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

API_ID = 20807000
API_HASH = 'cde2366a7c61e23f4cb44618cbe6cf70'
BOT_TOKEN = '7686849126:AAFjtFz6YZlLP-FnadMvrFTJIsphVr1OYEY'
OWNER_ID = [5938871512, 890749443] 

bot = Client("ProDownloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

@bot.on_message(filters.command(["txt"]) & filters.user(OWNER_ID))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("⚡ **Send the .txt file now** ⚡")
    try:
        # File wait logic
        input_msg: Message = await bot.listen(editable.chat.id, timeout=300)
        
        # 🛡️ CRASH-PROOF CHECK: Check agar file hai ya nahi
        if not input_msg.document:
            await editable.edit("❌ **Error:** Please send a file, not text/image.")
            return

        x = await input_msg.download()
        await input_msg.delete(True)
        file_name, _ = os.path.splitext(os.path.basename(x))
        
        # Baaki logic same hai...
        with open(x, "r", encoding="utf-8") as f:
            content = f.read().splitlines()
        links = [line.split("://", 1) for line in content if "://" in line]
        os.remove(x)

        # User Inputs
        await editable.edit("📚 **Batch Name?** (Send 1 for default)")
        input1 = await bot.listen(editable.chat.id)
        b_name = file_name if input1.text == '1' else input1.text
        
        await editable.edit("**📸 Resolution?** (e.g. 720)")
        input2 = await bot.listen(editable.chat.id)
        raw_res = input2.text
        res = {"144": "256x144", "240": "426x240", "360": "640x360", "480": "854x480", "720": "1280x720", "1080": "1920x1080"}.get(raw_res, "1280x720")
        
        await editable.edit("**Token?**")
        input4 = await bot.listen(editable.chat.id)
        cp_token = input4.text
        
        await editable.edit("Thumb URL? (or send 'no')")
        input6 = await bot.listen(editable.chat.id)
        thumb_url = input6.text
        await editable.delete()

        # Downloading
        thumb = "thumb.jpg" if thumb_url.startswith("http") else "no"
        if thumb == "thumb.jpg": urllib.request.urlretrieve(thumb_url, thumb)

        for i, link_data in enumerate(links):
            url = "https://" + link_data[1].replace("master.m3u8", "master.mpd")
            name = f"{i+1}) {link_data[0][:50]}"
            
            if "classplus" in url or "cpvod" in url:
                drm_data = generate_drm_keys(url, cp_token)
                if "error" in drm_data:
                    await m.reply(f"❌ **DRM Error:** {drm_data['error']}")
                    continue
                keys_str = " ".join([f"--key {k}" for k in drm_data['keys']])
                res_file = await helper.decrypt_and_merge_video(drm_data["mpd_url"], keys_str, "./downloads/", name, res)
                await helper.send_vid(bot, m, "Done", res_file, thumb, name, None)
            else:
                # Normal video logic...
                cmd = f'yt-dlp -f "bv+ba/b" "{url}" -o "{name}.mp4"'
                res_file = await helper.download_video(url, cmd, name)
                await helper.send_vid(bot, m, "Done", res_file, thumb, name, None)
                
    except Exception as e:
        await m.reply_text(f"‼️ **Failed:** {e}")

bot.run()
