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

# ===== CONFIGURATION =====
API_ID = 20807000
API_HASH = 'cde2366a7c61e23f4cb44618cbe6cf70'
BOT_TOKEN = '7686849126:AAFjtFz6YZlLP-FnadMvrFTJIsphVr1OYEY' # ⚠️ अपना टोकन यहाँ बदलें
OWNER_ID = [890749443] # ⚠️ आपकी सही ID

# in_memory=True: यह सबसे ज़रूरी है ताकि Session फाइल करप्ट न हो
bot = Client("ProDownloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# ===== DEBUG MODE =====
@bot.on_message(filters.all)
async def debug_log(bot, m: Message):
    # Railway के Logs में ये चेक करने के लिए कि बॉट को मैसेज मिल रहा है या नहीं
    print(f"DEBUG: Message from {m.chat.id}: {m.text or 'File/Media'}")

# ===== COMMANDS =====
@bot.on_message(filters.command(["start"]) & filters.user(OWNER_ID))
async def start_command(bot: Client, message: Message):
    await message.reply_text("✅ **Bot is Running!**\nSend /txt to start downloading.")

@bot.on_message(filters.command(["txt"]) & filters.user(OWNER_ID))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("⚡ **Send the .txt file now (As Document)** ⚡")
    try:
        input_msg: Message = await bot.listen(editable.chat.id, timeout=300)
        
        if not input_msg.document:
            await editable.edit("❌ **Error:** Please send the file as a **Document**, not as text.")
            return

        x = await input_msg.download()
        await input_msg.delete(True)
        
        with open(x, "r", encoding="utf-8") as f:
            links = [line.split("://", 1) for line in f.read().splitlines() if "://" in line]
        os.remove(x)

        # Inputs
        await editable.edit("📚 **Batch Name?**")
        b_name = (await bot.listen(editable.chat.id)).text
        
        await editable.edit("**📸 Resolution?** (e.g. 720)")
        raw_res = (await bot.listen(editable.chat.id)).text
        res = {"720": "1280x720", "480": "854x480"}.get(raw_res, "1280x720")
        
        await editable.edit("**Token?**")
        cp_token = (await bot.listen(editable.chat.id)).text
        
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
                res_file = await helper.decrypt_and_merge_video(drm_data["mpd_url"], keys_str, "./downloads/", name, res)
            else:
                cmd = f'yt-dlp -f "bv+ba/b" "{url}" -o "{name}.mp4"'
                res_file = await helper.download_video(url, cmd, name)
            
            await helper.send_vid(bot, m, "Done", res_file, "no", name, prog)
            await prog.delete()
                
    except Exception as e:
        await m.reply_text(f"‼️ **Failed:** {e}")

bot.run()
