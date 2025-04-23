"""Modulo para obtener TLEs de SpaceTrack.org"""
import json
import requests

LOGIN_URL              = 'https://www.space-track.org/auth/login'
DATA_URL               = 'https://www.space-track.org/basicspacedata/query/class/tle_latest/ORDINAL/1/NORAD_CAT_ID/27424/orderby/TLE_LINE1'
USER                   = 'user'
PASSWORD               = 'psswd'

siteCredentials = {'identity': USER, 'password': PASSWORD}

URI_BASE                = "https://www.space-track.org"
REQUEST_LOGIN           = "/ajaxauth/login"
CMD_ACTION              = "/basicspacedata/query"
FIND_SATELLITE          = '/class/tle_latest/ORDINAL/1/NORAD_CAT_ID/27424/orderby/TLE_LINE1'

class MyError(Exception):
    """Custom exception class for handling errors in the script."""
    def __init___(self,args):
        Exception.__init__(self,f"my exception was raised with arguments {args}")
        self.args = args

with requests.Session() as session:

    resp = session.post(URI_BASE + REQUEST_LOGIN, data = siteCredentials)
    if resp.status_code != 200:
        raise MyError(resp, "POST fail on login")

    resp = session.get(URI_BASE + CMD_ACTION + FIND_SATELLITE )
    if resp.status_code != 200:
        raise MyError(resp, "GET fail on request for Starlink satellites")

    retData = json.loads(resp.text)
    print(retData)
    session.close()
