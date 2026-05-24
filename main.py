import os
import sys
import asyncio
import urllib.request
import cloudscraper
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import pyromod.listen

import core as helper
from app import generate_drm_keys

API_ID = 20807000
API_HASH = 'cde2366a7c61e23f4cb44618cbe6cf70'
BOT_TOKEN = '8564398983:AAGxMpPkmLcgZsPnVzIQzCUIro5KNk76QBw'
OWNER_ID = [5938871512, 890749443] 

bot = Client("ProDownloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# DRM Video Downloader Logic
async def run_drm_downloader(mpd_link, keys_string, path, name):
    os.makedirs(path, exist_ok=True)
    safe_name = name.replace("/", "").replace(":", "").replace(" ", "_")
    cmd = f'./N_m3u8DL-RE "{mpd_link}" {keys_string} --auto-select --save-name "{safe_name}" --save-dir "{path}" -M format=mp4'
    process = await asyncio.create_subprocess_shell(cmd)
    await process.communicate()
    
    file_path = os.path.join(path, f"{safe_name}.mp4")
    if not os.path.exists(file_path):
        file_path = os.path.join(path, f"{safe_name}.mkv")
    return file_path

# Normal Video Downloader Logic
async def run_ytdlp(cmd, name):
    process = await asyncio.create_subprocess_shell(cmd)
    await process.communicate()
    safe_name = name.replace("/", "").replace(":", "").replace(" ", "_")
    if os.path.exists(f"{safe_name}.mp4"): return f"{safe_name}.mp4"
    if os.path.exists(f"{safe_name}.mkv"): return f"{safe_name}.mkv"
    return f"{name}.mp4"

@bot.on_message(filters.command(["start"]) & filters.user(OWNER_ID))
async def start_command(bot, message):
    await message.reply_text("😎 **Bot is Ready!** Send /txt to start.")

@bot.on_message(filters.command("stop") & filters.user(OWNER_ID))
async def stop_handler(_, m):
    await m.reply_text("🚦**STOPPED**🚦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["txt"]) & filters.user(OWNER_ID))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("⚡ 𝗦𝗘𝗡𝗗 𝗧𝗫𝗧 𝗙𝗜𝗟𝗘 ⚡")
    input_msg = await bot.listen(editable.chat.id)
    x = await input_msg.download()
    await input_msg.delete(True)
    file_name, _ = os.path.splitext(os.path.basename(x))
    
    try:    
        with open(x, "r", encoding="utf-8") as f:
            content = f.read().splitlines()
        
        links = [line.split("://", 1) for line in content if "://" in line]
        os.remove(x)
    except Exception as e:
        await m.reply_text("😶 Invalid File.")
        return
   
    await editable.edit(f"`𝗧𝗼𝘁𝗮𝗹 🔗 𝗟𝗶𝗻𝗸𝘀 {len(links)}\n𝗦𝗲𝗻𝗱 𝗙𝗿𝗼𝗺 𝗪𝗵𝗲𝗿𝗲 𝗬𝗼𝘂 𝗪𝗮𝗻𝘁 𝗧𝗼 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 (Index)`")
    input0 = await bot.listen(editable.chat.id)
    count = int(input0.text) if input0.text.isdigit() else 1
    await input0.delete(True)

    await editable.edit("📚 𝗘𝗻𝘁𝗲𝗿 𝗬𝗼𝘂𝗿 𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗲 \n(Send `1` for default)")
    input1 = await bot.listen(editable.chat.id)
    b_name = file_name if input1.text == '1' else input1.text
    await input1.delete(True)
    
    await editable.edit("**📸 𝗘𝗻𝘁𝗲𝗿 𝗥𝗲𝘀𝗼𝗹𝘂𝘁𝗶𝗼𝗻 📸** (e.g. 720, 480)")
    input2 = await bot.listen(editable.chat.id)
    res_dict = {"144": "256x144", "240": "426x240", "360": "640x360", "480": "854x480", "720": "1280x720", "1080": "1920x1080"}
    res = res_dict.get(input2.text, "1280x720")
    raw_res = input2.text
    await input2.delete(True)

    await editable.edit("📛 𝗘𝗻𝘁𝗲𝗿 𝗖𝗮𝗽𝘁𝗶𝗼𝗻 \n(Send `1` for default)")
    input3 = await bot.listen(editable.chat.id)
    CR = "Group Admin:)™" if input3.text == '1' else input3.text
    await input3.delete(True)
   
    await editable.edit("**𝗘𝗻𝘁𝗲𝗿 𝗪𝗼𝗿𝗸𝗶𝗻𝗴 𝗧𝗼𝗸𝗲𝗻 (Classplus)**")
    input4 = await bot.listen(editable.chat.id)
    cp_token = input4.text
    await input4.delete(True)

    await editable.edit("𝗡𝗼𝘄 𝗦𝗲𝗻𝗱 𝗧𝗵𝗲 𝗧𝗵𝘂𝗺𝗯 𝗨𝗿𝗹 (or send `no`)")
    input6 = await bot.listen(editable.chat.id)
    thumb_url = input6.text
    await input6.delete(True)
    await editable.delete()

    if thumb_url.startswith("http"):
        try:
            urllib.request.urlretrieve(thumb_url, "thumb.jpg")
            thumb = "thumb.jpg"
        except: thumb = "no"
    else: thumb = "no"

    failed_count = 0

    # ===== BATCH DOWNLOADING LOOP =====
    for i in range(count - 1, len(links)):
        V = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
        url = "https://" + V
        
        name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").strip()
        safe_name = name1[:60]
        name = f'{str(i+1).zfill(3)}) {safe_name}'
        
        cc = f'**╭── ⋆⋅☆⋅⋆ ──╮**\n✦ **{str(i+1).zfill(3)}** ✦\n**╰── ⋆⋅☆⋅⋆ ──╯**\n\n🎭 **Title:** `{safe_name} .mkv`\n🖥️ **Resolution:** [{raw_res}]\n📘 **Course:** `{b_name}`\n🚀 **Extracted By:** `{CR}`'
        Show = f"✈️ 𝗣𝗥𝗢𝗚𝗥𝗘𝗦𝗦 ✈️\n\n┠ 📈 Total Links = {len(links)}\n┠ 💥 Currently On = {str(i+1).zfill(3)}\n\n**📩 𝗗𝗢𝗪𝗡𝗟𝗢𝗔𝗗𝗜𝗡𝗚 📩**\n\n**🧚🏻‍♂️ Title** : {name}\n├── **Resolution** : {raw_res}\n├── **Extracted By** : {CR}"
        
        try:
            # 1. Image Filter (Isse image DRM me nahi jayegi)
            if any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png"]):
                prog = await m.reply_text(Show + "\n\n🖼️ **Downloading Image...**")
                urllib.request.urlretrieve(url, f"{name}.jpg")
                await bot.send_photo(chat_id=m.chat.id, photo=f'{name}.jpg', caption=cc)
                await prog.delete(True)
                os.remove(f'{name}.jpg')
                await asyncio.sleep(1)
                continue

            # 2. PDF Filter
            elif ".pdf" in url:
                prog = await m.reply_text(Show + "\n\n📄 **Downloading PDF...**")
                cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                os.system(cmd)
                await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc)
                await prog.delete(True)
                os.remove(f'{name}.pdf')
                await asyncio.sleep(1)
                continue

            # 3. CLASSPLUS DRM LOGIC
            elif "classplus" in url or "cpvod" in url:
                prog = await m.reply_text(Show + "\n\n🔐 **DRM Decryption Started...**")
                
                # YAHAN TOKEN PASS HO RAHA HAI
                drm_data = generate_drm_keys(url, cp_token)
                
                if "error" in drm_data:
                    await prog.edit(f"❌ **DRM Error:** {drm_data['error']}\n\n⚠️ Kripya fresh Classplus Token use karein!")
                    failed_count += 1
                    continue
                
                keys_string = " ".join([f"--key {k}" for k in drm_data['keys']])
                res_file = await run_drm_downloader(drm_data["mpd_url"], keys_string, "./downloads/", name)
                
                await prog.delete(True)
                await helper.send_vid(bot, m, cc, res_file, thumb, name, prog)
                await asyncio.sleep(1)
                continue

            # 4. NORMAL VIDEO (YouTube/Appx etc)
            else:
                prog = await m.reply_text(Show)
                ytf = f"b[height<={raw_res}][ext=mp4]/bv[height<={raw_res}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]" if "youtu" in url else f"b[height<={raw_res}]/bv[height<={raw_res}]+ba/b/bv+ba"
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'
                
                res_file = await run_ytdlp(cmd, name)
                await prog.delete(True)
                await helper.send_vid(bot, m, cc, res_file, thumb, name, prog)
                await asyncio.sleep(1)

        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
            
        except Exception as e:
            await m.reply_text(f'‼️ 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗶𝗻𝗴 𝗙𝗮𝗶𝗹𝗲𝗱 ‼️\n\n📝 𝗡𝗮𝗺𝗲 » `{name}`\nError: {e}')
            failed_count += 1
            continue   

    await m.reply_text(f"`✨ 𝗕𝗔𝗧𝗖𝗛 𝗦𝗨𝗠𝗠𝗔𝗥𝗬 ✨\n\n✅ 𝗦𝗧𝗔𝗧𝗨𝗦 » 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗\nFailed: {failed_count}`")

if __name__ == "__main__":
    bot.run()
