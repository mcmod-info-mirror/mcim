
__all__ = [
	'Clash'
]

import requests

class Clash:
    '''
    Clash RESTful API Docs: https://clash.gitbook.io/
    '''
    def __init__(self, api_url: str , port: int, secret: str):
        self.api_url = api_url
        self.port = str(port)
        self.url = "http://" + api_url + ":" + self.port + "/"
        self.secrt = secret
        self.headers={"Authorization": "Bearer " + self.secrt}
        
        # Test
        res = requests.get(self.url,headers=self.headers)
        if res.status_code != 200:
            raise Exception("Failed to connect to Clash API")
    
    def get_traffic(self):
        res = requests.get(self.url + "traffic", headers=self.headers)
        if res.status_code == 200:
            return res.json()
        else:
            return None

    def get_proxies(self):
        res = requests.get(self.url + "proxies", headers=self.headers)
        if res.status_code == 200:
            return res.json()
        else:
            return None

    def get_proxy(self,name: str):
        res = requests.get(self.url + "proxies" + "/" + name, headers=self.headers)
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 404:
            return res.json()["error"]
        else:
            return None
    
    def get_delay(self, name: str, timeout: int, url: str):
        res = requests.get(self.url + "proxies" + "/" + name + "/" + "delay", params={"timeout": timeout, "url": url}, headers=self.headers)
        if res.status_code == 200:
            return res.json()["delay"]
        elif res.status_code in [400,404,408]:
            return res.json()["error"]
        else:
            return None
    
    def change_proxy(self, name: str, selector: str):
        res = requests.put(self.url + "proxies" + "/" + selector, json={"name": name} ,headers=self.headers)
        if res.status_code == 204:
            return True
        elif res.status_code in [400,404]:
            return res.json()
        else:
            return None

    def get_config(self):
        res = requests.get(self.url + "config", headers=self.headers)
        if res.status_code == 200:
            return res.json()
        else:
            return None

    def patch_config(self,**kwargs):
        res = requests.patch(self.url + "config", data=kwargs, headers=self.headers)
        if res.status_code == 204:
            return True
        else:
            return None

    def put_config(self,force: bool, path: str):
        res = requests.put(self.url + "config", data = {"force": force}, params = {"path": path}, headers=self.headers)
        if res.status_code == 200:
            return True
        else:
            return None

    def get_rules(self):
        res = requests.get(self.url + "rules", headers=self.headers)
        if res.status_code == 200:
            return res.json()
        else:
            return None