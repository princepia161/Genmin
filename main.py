import os
import sys
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import pyromod.listen  # bot.listen ke liye
import core as helper  # Aapki download/upload file
from app import generate_drm_keys

# ===== BOT SETUP =====
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YAHAN_APNA_BOT_TOKEN_DALEIN")
API_ID = int(os.environ.get("API_ID", "YAHAN_API_ID_DALEIN"))
API_HASH = os.environ.get("API_HASH", "YAHAN_API_HASH_DALEIN")
OWNER_ID = [int(os.environ.get("OWNER_ID", "5938871512"))] # Apna Telegram ID dalein

bot = Client("AdvanceBot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

@bot.on_message(filters.command(["start"]) & filters.user(OWNER_ID))
async def start_handler(bot, m: Message):
    await m.reply_text("😎 **Advance DRM Batch Downloader is Ready!**\\nSend `/txt` to upload file.")

@bot.on_message(filters.command(["txt"]) & filters.user(OWNER_ID))
async def txt_handler(bot, m: Message):
    editable = await m.reply_text("📂 **Please Send TXT file for download**")
    input_msg: Message = await bot.listen(m.chat.id)
    
    # File Download & Read
    file_path = await input_msg.download()
    file_name = os.path.basename(file_path).replace(".txt", "")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().splitlines()
            
        links = []
        for line in content:
            if "://" in line:
                links.append(line.split("://", 1))
        os.remove(file_path)
    except Exception:
        await m.reply_text("❌ Invalid file format.")
        return

    if not links:
        await m.reply_text("❌ No links found in the file.")
        return

    # Inputs from User
    await editable.edit(f"✅ Total links found: **{len(links)}**\\n\\n➡️ Send starting index (e.g., `1`):")
    input0: Message = await bot.listen(m.chat.id)
    start_index = int(input0.text) - 1
    
    await editable.edit("➡️ Send Batch Name (or send `df` for file name):")
    input1: Message = await bot.listen(m.chat.id)
    b_name = file_name if input1.text == 'df' else input1.text

    await editable.edit("➡️ Enter resolution (`1080`, `720`, `480`, `360`):")
    input2: Message = await bot.listen(m.chat.id)
    res_dict = {"144": "256x144", "240": "426x240", "360": "640x360", "480": "854x480", "720": "1280x720", "1080": "1920x1080"}
    res = res_dict.get(input2.text, "1280x720")

    await editable.edit("➡️ Enter Classplus Working Token! (Copy from Network Tab):")
    input3: Message = await bot.listen(m.chat.id)
    cp_token = input3.text

    await editable.edit("🚀 **Processing Started!**")

    count = 1
    success_count = 0
    failed_count = 0

    # ===== BATCH PROCESSING LOOP =====
    for i in range(start_index, len(links)):
        try:
            # URL aur Name alag karna (TXT Format: Name:https://...)
            raw_url = "https://" + links[i][1]
            vid_name = links[i][0].replace("https", "").strip(" :")
            
            prog = await m.reply_text(f"⏳ **Processing:** {vid_name}\\n🔗 Extracting DRM Keys...")
            
            # DRM Keys nikalna app.py se
            drm_data = generate_drm_keys(raw_url, cp_token)
            
            if "error" in drm_data:
                await prog.edit(f"❌ **DRM Error:** {drm_data['error']}\\nSkipping...")
                failed_count += 1
                continue

            mpd_link = drm_data['mpd_url']
            keys_string = drm_data['keys_string']

            await prog.edit(f"📥 **Downloading Video:** {vid_name}")
            
            # Aapke core.py ka helper function call
            # Make sure core.py me decrypt_and_merge_video function exist karta ho
            downloaded_file = await helper.decrypt_and_merge_video(mpd_link, keys_string, "./downloads/", vid_name, res)
            
            await prog.edit("📤 **Uploading to Telegram...**")
            await helper.send_vid(bot, m, "No Caption", downloaded_file, "thumb.jpg", vid_name, prog)
            
            success_count += 1
            await asyncio.sleep(2) # Telegram flood wait se bachne ke liye
            
        except Exception as e:
            await m.reply_text(f"‼️ **Failed:** `{vid_name}`\\nError: {str(e)}")
            failed_count += 1
            continue

    await m.reply_text(f"🎉 **BATCH COMPLETE** 🎉\\n✅ Success: {success_count}\\n❌ Failed: {failed_count}")

bot.run()
