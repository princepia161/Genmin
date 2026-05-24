from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
import requests
from bs4 import BeautifulSoup
import os
import glob


def wvd_check():
    extracted_device = glob.glob(f'{os.getcwd()}/WVDs/*.wvd')[0]
    return extracted_device


wvd = wvd_check()

headers = { 'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTY0MDQwNzkyLCJvcmdJZCI6ODEyNDEwLCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTgyMTAxNjk5NTEiLCJuYW1lIjoiUHJpbmNlcGlhIiwiZW1haWwiOiJwcmluY2VwaWExNjFAZ21haWwuY29tIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJkZWZhdWx0TGFuZ3VhZ2UiOiJFTiIsImNvdW50cnlDb2RlIjoiSU4iLCJjb3VudHJ5SVNPIjoiOTEiLCJ0aW1lem9uZSI6IkdNVCs1OjMwIiwiaXNEaXkiOnRydWUsIm9yZ0NvZGUiOiJra3Vja3kiLCJpc0RpeVN1YmFkbWluIjowLCJmaW5nZXJwcmludElkIjoiNTYyODI3NmQyNmJhMTAwMDE5OWRlNmUwZWVhMWE1MDEiLCJpYXQiOjE3Nzk2MDA3NzQsImV4cCI6MTc4MDIwNTU3NH0.fona8i66tmufk1R639uA2vHgq4YtxmvARhBZbgL_zHnmKGtEZKgKYzmeZu7ckRac'}

url = input("url:")

response = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers=headers).json()

if response['status'] == 'ok':
    mpd = response['drmUrls']['manifestUrl']
    lic = response['drmUrls']['licenseUrl']
    response=requests.get(mpd)
    soup = BeautifulSoup(response.text, 'xml')
    uuid = soup.find('ContentProtection', attrs={'schemeIdUri': 'urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed'})
    pssh = uuid.find('cenc:pssh').text
    ipssh = PSSH(pssh)
    device = Device.load(wvd)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id,ipssh)
    licence = requests.post(lic, data=challenge,headers=headers)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)

    keys = []
    for key in cdm.get_keys(session_id):
        if key.type != 'SIGNING':
            keys.append(f'{key.kid.hex}:{key.key.hex()}')

    cdm.close(session_id)
    print(f"\n{mpd}\n")
    for i in keys:
        print(f"--key {i}")

else:
    print("error, check again")
