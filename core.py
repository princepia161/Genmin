import os
import time
import asyncio
import subprocess
from pyrogram import Client

# ==========================================
# Auto-Download DRM Tool (N_m3u8DL-RE) for Railway
# ==========================================
if not os.path.exists("N_m3u8DL-RE"):
    print("Downloading DRM Tool...")
    os.system('wget "https://github.com/nilaoda/N_m3u8DL-RE/releases/download/v0.2.0-beta/N_m3u8DL-RE_Beta_linux-x64_20230628.tar.gz"')
    os.system('tar -xvf N_m3u8DL-RE_Beta_linux-x64_20230628.tar.gz')
    os.system('mv N_m3u8DL-RE_Beta_linux-x64/N_m3u8DL-RE .')
    os.system('chmod +x N_m3u8DL-RE')
    os.system('rm -rf N_m3u8DL-RE_Beta_linux-x64 N_m3u8DL-RE_Beta_linux-x64_20230628.tar.gz')
    print("DRM Tool Setup Complete!")

# ==========================================
# 1. DRM Video Downloader & Decryptor
# ==========================================
async def decrypt_and_merge_video(mpd_link, keys_string, path, name, res):
    os.makedirs(path, exist_ok=True)
    # File name ko safe banana
    safe_name = name.replace("/", "").replace(":", "").replace(" ", "_")
    
    # N_m3u8DL-RE command (DRM decrypt karne ke liye)
    cmd = f'./N_m3u8DL-RE "{mpd_link}" {keys_string} --auto-select --save-name "{safe_name}" --save-dir "{path}" -M format=mp4'
    
    # Process run karna
    process = await asyncio.create_subprocess_shell(cmd)
    await process.communicate()
    
    final_file = os.path.join(path, f"{safe_name}.mp4")
    return final_file

# ==========================================
# 2. Normal Video Downloader (Non-DRM)
# ==========================================
async def download_video(url, cmd, name):
    safe_name = name.replace("/", "").replace(":", "")
    final_file = f"{safe_name}.mp4"
    
    # YT-DLP command run karna
    process = await asyncio.create_subprocess_shell(cmd)
    await process.communicate()
    
    return final_file

# ==========================================
# 3. Telegram Uploader (Send Video)
# ==========================================
async def send_vid(bot: Client, m, caption, filename, thumb, name, prog):
    await prog.edit("📤 **Uploading to Telegram... Please wait.**")
    
    # Thumbnail logic
    thumb_path = thumb if str(thumb).endswith(".jpg") and os.path.exists(str(thumb)) else None

    try:
        await bot.send_video(
            chat_id=m.chat.id,
            video=filename,
            caption=caption,
            thumb=thumb_path,
            supports_streaming=True,
            width=1280,
            height=720
        )
        
        # Upload hone ke baad file delete karna (Server storage bachane ke liye)
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        await prog.edit(f"❌ **Upload Error:**\n`{str(e)}`")
        if os.path.exists(filename):
            os.remove(filename)
