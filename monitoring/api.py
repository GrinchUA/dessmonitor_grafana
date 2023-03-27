import hashlib
import requests
import re
import logging

from datetime import datetime, timedelta
from urllib.parse import urlencode
from pprint import pprint
from monitoring.settings import settings

logger = logging.getLogger("uvicorn")

class Api:
    pwd = settings.password
    usr = settings.login
    company_key = settings.company_key
    source = "1"
    _app_client_ = 'web'
    _app_id_ = "com.demo.test"
    _app_version_ = '3.6.2.1'
    secret = None
    token = None

    def __init__(self, app):
        self.app = app
        self.metrics = {}

        if 'expire' not in self.app.data:
            self.auth()
        elif self.app.data['expire'] < datetime.now():
            self.auth()
        else:
            self.secret = self.app.data['secret']
            self.token = self.app.data['token']

        if 'device' not in self.app.data:
            self.get_params()
        else:
            self.device = self.app.data['device']

    def make_salt(self):
        d = datetime.now()
        return int(datetime.timestamp(d)*1000)        

    def auth(self):
        logger.info("auth")
        salt = self.make_salt()
        pwd_sha = hashlib.sha1(self.pwd.encode('utf-8')).hexdigest()
        sign_str = f"{salt}{pwd_sha}&action=authSource&usr={self.usr}&company-key={self.company_key}&source={self.source}&_app_client_={self._app_client_}&_app_id_={self._app_id_}&_app_version_={self._app_version_}"
        sign = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()
        args = urlencode({
            "sign": sign,
            "salt": salt,
            "action": "authSource",
            "usr": self.usr,
            "company-key": self.company_key,
            "source": self.source,
            "_app_client_": self._app_client_,
            "_app_id_": self._app_id_,
            "_app_version_": self._app_version_
        })

        url = f"http://api.dessmonitor.com/public/?{args}"
        

        r = requests.get(url)

        if r.ok:
            self.secret = r.json().get('dat', {}).get('secret')
            self.token = r.json().get('dat', {}).get('token')
            expire = r.json().get('dat', {}).get('expire')
            if expire:
                expire = int(expire) - 120

                self.app.data['secret'] = self.secret
                self.app.data['token'] = self.token
                self.app.data['expire'] = datetime.now() + timedelta(seconds=expire)

    def get_params(self):
        if self.token:
            result = self.get_request('webQueryDeviceEs', {})

            if result and result.ok:
                self.device = result.json().get('dat', {}).get('device')[0]

                self.app.data['device'] = self.device


    def get_request(self, action='queryDeviceParsEs', params={}, show_result=False):
        salt = self.make_salt()
        sign_param = urlencode(params)

        if len(params) > 0:
            sign_str = f"{salt}{self.secret}{self.token}&action={action}&{sign_param}&_app_client_={self._app_client_}&_app_id_={self._app_id_}&_app_version_={self._app_version_}"
        else:
            sign_str = f"{salt}{self.secret}{self.token}&action={action}&_app_client_={self._app_client_}&_app_id_={self._app_id_}&_app_version_={self._app_version_}"
        
        sign = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()
        args = {
            "sign": sign,
            "salt": salt,
            "token": self.token,
            "action": action,
        }

        for k, v in params.items():
            args[k] = v

        args["_app_client_"] = self._app_client_
        args["_app_id_"] = self._app_id_
        args["_app_version_"] = self._app_version_
        r_params = urlencode(args)

        url = f"http://api.dessmonitor.com/public/?{r_params}"

        r = requests.get(url)
    
        if r.ok and show_result:
            print(f"************** {action} **************")
            pprint(r.json())

        return r

    def queryDeviceParsEs(self):
        params = {
            "devcode": self.device['devcode']
        }

        self.get_request('queryDeviceParsEs', params)


    def queryDeviceLastData(self):
        if not self.token:
            return

        params = {
            'i18n': 'en_US',
            "pn": self.device['pn'],
            "devcode": self.device['devcode'],
            "devaddr": self.device['devaddr'],
            "sn": self.device['sn']
        }

        r = self.get_request('queryDeviceLastData', params)

        metrics = {}

        if r.ok:
            for m in r.json().get('dat', []):
                # key = m['title'].lower()
                key = re.sub(r'[^\w\s]', '', m['title']).replace(" ", "_").replace("__", "_").lower()
                metrics[key] = m

        self.metrics = dict(sorted(metrics.items()))

    def querySPDeviceLastData(self):
        params = {
            'i18n': 'en_US',
            "pn": self.device['pn'],
            "devcode": self.device['devcode'],
            "devaddr": self.device['devaddr'],
            "sn": self.device['sn']
        }

        self.get_request('querySPDeviceLastData', params, show_result=True)

    # def webQueryDeviceEs(self):
    #     self.get_request('webQueryDeviceEs', {})
