from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
import requests
from bs4 import BeautifulSoup
import os
import glob

def generate_drm_keys(video_url, cp_token):
    try:
        wvd = glob.glob(f'{os.getcwd()}/WVDs/*.wvd')[0]
    except Exception:
        return {"error": "WVD file not found in WVDs folder!"}

    # Aapka working token yahan dynamically aayega
    headers = {
        'x-access-token': cp_token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    try:
        api_url = f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={video_url}'
        response = requests.get(api_url, headers=headers).json()
    except Exception as e:
        return {"error": f"API Request Failed: {e}"}

    if response.get('status') != 'ok':
        return {"error": "Token Expired ya Invalid hai. Naya token daalein!"}

    mpd = response['drmUrls']['manifestUrl']
    lic = response['drmUrls']['licenseUrl']

    mpd_response = requests.get(mpd)
    soup = BeautifulSoup(mpd_response.text, 'xml')
    uuid = soup.find('ContentProtection', attrs={'schemeIdUri': 'urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed'})
    
    if not uuid:
        return {"error": "Is video me DRM nahi mila."}

    pssh = uuid.find('cenc:pssh').text
    ipssh = PSSH(pssh)
    
    device = Device.load(wvd)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, ipssh)
    licence = requests.post(lic, data=challenge, headers=headers)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)

    keys = []
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            keys.append(f'{key.kid.hex}:{key.key.hex()}')

    cdm.close(session_id)
    return {"mpd_url": mpd, "keys": keys}
