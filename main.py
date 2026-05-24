# main.py
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import core as helper
from app import generate_drm_keys

bot = Client("ProDownloader", api_id=20807000, api_hash='cde2366a7c61e23f4cb44618cbe6cf70', bot_token='8564398983:AAGxMpPkmLcgZsPnVzIQzCUIro5KNk76QBw')

@bot.on_message(filters.command("txt"))
async def txt_handler(bot, m: Message):
    editable = await m.reply_text("**📂 Please Send TXT file**")
    input_file: Message = await bot.listen(m.chat.id)
    file_path = await input_file.download()
    
    # 1. Links Read karna
    with open(file_path, "r") as f:
        links = [line.strip().split("://", 1) for line in f if "://" in line]
    os.remove(file_path)

    # 2. Batch Settings (Purana Function)
    await editable.edit("➡️ Enter Batch Name:")
    input1 = await bot.listen(m.chat.id)
    b_name = input1.text
    
    await editable.edit("➡️ Enter Resolution (e.g. 720):")
    input2 = await bot.listen(m.chat.id)
    res = input2.text

    await editable.edit("➡️ Enter Working Token:")
    input3 = await bot.listen(m.chat.id)
    token = input3.text
    
    # 3. Batch Downloading Loop
    for i in range(len(links)):
        url = "https://" + links[i][1]
        vid_name = links[i][0]
        
        try:
            # DRM Decryption Call
            drm_info = generate_drm_keys(url, token)
            
            # Downloading Logic (core.py)
            await helper.decrypt_and_merge_video(drm_info['mpd_url'], drm_info['keys_string'], "./downloads/", vid_name, res)
            await m.reply(f"✅ Done: {vid_name}")
        except Exception as e:
            await m.reply(f"❌ Failed {vid_name}: {e}")

bot.run()
