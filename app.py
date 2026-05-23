import os
import glob
import requests
from bs4 import BeautifulSoup
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH

def wvd_check():
    try:
        return glob.glob(f'{os.getcwd()}/WVDs/*.wvd')[0]
    except IndexError:
        raise Exception("Error: WVD file not found in WVDs/ folder!")

def generate_drm_keys(video_url, token):
    wvd = wvd_check()
    headers = {
        'x-access-token': token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Classplus API se MPD aur License URL nikalna
    api_url = f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={video_url}'
    response = requests.get(api_url, headers=headers).json()
    
    if response.get('status') != 'ok':
        return {"error": "Token Expired ya Link Invalid hai!"}

    mpd = response['drmUrls']['manifestUrl']
    lic = response['drmUrls']['licenseUrl']

    # MPD File se PSSH nikalना
    mpd_response = requests.get(mpd)
    soup = BeautifulSoup(mpd_response.text, 'xml')
    uuid = soup.find('ContentProtection', attrs={'schemeIdUri': 'urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed'})
    
    if not uuid:
        return {"error": "Is video me DRM nahi hai."}
        
    pssh = uuid.find('cenc:pssh').text
    ipssh = PSSH(pssh)
    
    # Keys Generate karna
    device = Device.load(wvd)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, ipssh)
    
    licence = requests.post(lic, data=challenge, headers=headers)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)

    keys = []
    keys_string = ""
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            keys.append(f'{key.kid.hex}:{key.key.hex()}')
            keys_string += f"--key {key.kid.hex}:{key.key.hex()} "

    cdm.close(session_id)
    return {"status": "success", "mpd_url": mpd, "keys_string": keys_string.strip()}
