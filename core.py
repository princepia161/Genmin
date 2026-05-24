import os
import time
import asyncio
import subprocess
import urllib.request
import tarfile
import shutil
from pyrogram import Client

# ==========================================
# Auto-Download DRM Tool (100% Python - No wget needed)
# ==========================================
if not os.path.exists("N_m3u8DL-RE"):
    print("Downloading DRM Tool via Python...")
    try:
        url = "https://github.com/nilaoda/N_m3u8DL-RE/releases/download/v0.2.0-beta/N_m3u8DL-RE_Beta_linux-x64_20230628.tar.gz"
        urllib.request.urlretrieve(url, "drm.tar.gz")
        with tarfile.open("drm.tar.gz", "r:gz") as tar:
            tar.extractall("drm_temp")
        shutil.move("drm_temp/N_m3u8DL-RE_Beta_linux-x64/N_m3u8DL-RE", "N_m3u8DL-RE")
        os.chmod("N_m3u8DL-RE", 0o755)
        os.remove("drm.tar.gz")
        shutil.rmtree("drm_temp")
        print("✅ DRM Tool Setup Complete!")
    except Exception as e:
        print(f"❌ Error downloading tool: {e}")

# ==========================================
# 1. DRM Video Downloader & Decryptor
# ==========================================
async def decrypt_and_merge_video(mpd_link, keys_string, path, name, res):
    os.makedirs(path, exist_ok=True)
    safe_name = name.replace("/", "").replace(":", "").replace(" ", "_")
    
    # N_m3u8DL-RE command
    cmd = f'./N_m3u8DL-RE "{mpd_link}" {keys_string} --auto-select --save-name "{safe_name}" --save-dir "{path}" -M format=mp4'
    
    process = await asyncio.create_subprocess_shell(cmd)
    await process.communicate()
    
    # Check output file format (kabhi mp4 hota hai, kabhi mkv)
    final_file = os.path.join(path, f"{safe_name}.mp4")
    if not os.path.exists(final_file):
        final_file = os.path.join(path, f"{safe_name}.mkv")
    return final_file

# ==========================================
# 2. Normal Video Downloader (Non-DRM)
# ==========================================
async def download_video(url, cmd, name):
    safe_name = name.replace("/", "").replace(":", "").replace(" ", "_")
    process = await asyncio.create_subprocess_shell(cmd)
    await process.communicate()
    
    if os.path.exists(f"{safe_name}.mp4"): return f"{safe_name}.mp4"
    if os.path.exists(f"{safe_name}.mkv"): return f"{safe_name}.mkv"
    return f"{safe_name}.webm"

# ==========================================
# 3. Telegram Uploader (Send Video)
# ==========================================
async def send_vid(bot: Client, m, caption, filename, thumb, name, prog):
    await prog.edit("📤 **Uploading to Telegram... Please wait.**")
    thumb_path = thumb if str(thumb).endswith(".jpg") and os.path.exists(str(thumb)) else None

    try:
        await bot.send_video(
            chat_id=m.chat.id,
            video=filename,
            caption=caption,
            thumb=thumb_path,
            supports_streaming=True
        )
    except Exception as e:
        await prog.edit(f"❌ **Upload Error:**\n`{str(e)}`")
    finally:
        # File server se hata dein taaki storage full na ho
        if os.path.exists(filename):
            os.remove(filename)
