import os
from pyrogram import Client, filters
from pyrogram.types import Message
import pyromod.listen
import core as helper
from app import generate_drm_keys

# ===== NEW CONFIGURATION =====
API_ID = 35822069
API_HASH = '35cea1c5e6384f57e914ac982ff5ffd1'
BOT_TOKEN = '8338892359:AAFQ9LctB2s_Efp3ULPLdW9RvOVFCHYWIH' # ⚠️ WARNING: Token revoke kar lena
OWNER_ID = [5938871512] 

# in_memory=True: Session file corruption ko rokne ke liye sabse zaroori
bot = Client("NxtGen", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# ===== DEBUG MODE =====
@bot.on_message(filters.all)
async def debug_log(bot, m: Message):
    # Yeh log Railway console mein dikhega. 
    # Agar tum message bhejoge aur yahan kuch nahi dikha, toh tum galat bot se baat kar rahe ho.
    print(f"DEBUG: Message mila {m.chat.id} se: {m.text or 'Media'}")

@bot.on_message(filters.command(["start"]) & filters.user(OWNER_ID))
async def start_command(bot: Client, message: Message):
    await message.reply_text("✅ **Bot is Active and Ready!**\nSend /txt to start downloading.")

@bot.on_message(filters.command(["txt"]) & filters.user(OWNER_ID))
async def upload(bot: Client, m: Message):
    editable = await m.reply_text("⚡ **Send the .txt file now (As Document)** ⚡")
    try:
        input_msg: Message = await bot.listen(editable.chat.id, timeout=300)
        
        if not input_msg.document:
            await editable.edit("❌ **Error:** Please send the file as a Document.")
            return

        x = await input_msg.download()
        await input_msg.delete(True)
        
        with open(x, "r", encoding="utf-8") as f:
            links = [line.split("://", 1) for line in f.read().splitlines() if "://" in line]
        os.remove(x)

        # Basic inputs
        await editable.edit("📚 **Batch Name?** (Send 1 for default)")
        b_name = (await bot.listen(editable.chat.id)).text
        
        await editable.edit("**📸 Resolution?** (e.g. 720)")
        raw_res = (await bot.listen(editable.chat.id)).text
        
        await editable.edit("**Token?**")
        cp_token = (await bot.listen(editable.chat.id)).text
        
        await editable.delete()

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
