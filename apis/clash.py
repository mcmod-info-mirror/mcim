
__all__ = [
	'Clash'
]

import requests

class Clash:
    '''
    Clash RESTful API Docs: https://clash.gitbook.io/
    '''
    def __init__(self, api_url: str, secret: str):
        self.api_url = api_url
        self.secrt = secret
        self.headers = {
            "Authorization": "Bearer " + self.secrt
        }
        
        # Test
        res = requests.get(self.api_url, headers=self.headers)
        if res.status_code != 200:
            raise Exception("Failed to connect to Clash API")
    
    def get_traffic(self):
        res = requests.get(f"{self.api_url}/traffic", headers=self.headers)
        if res.status_code == 200:
            return res.json()
        return None

    def get_proxies(self):
        res = requests.get(f"{self.api_url}/proxies", headers=self.headers)
        if res.status_code == 200:
            return res.json()
        return None

    def get_proxy(self,name: str):
        res = requests.get(f"{self.api_url}/proxies/{name}", headers=self.headers)
        if res.status_code == 200:
            return res.json()
        if res.status_code == 404:
            return res.json()["error"]
        return None
    
    def get_delay(self, name: str, timeout: int, url: str):
        res = requests.get(f"{self.api_url}/proxies/{name}/delay", params={"timeout": timeout, "url": url}, headers=self.headers)
        if res.status_code == 200:
            return res.json()["delay"]
        if res.status_code in (400, 404, 408):
            return res.json()["error"]
        return None
    
    def change_proxy(self, name: str, selector: str):
        res = requests.put(f"{self.api_url}/proxies/{selector}", json={"name": name}, headers=self.headers)
        if res.status_code == 204:
            return True
        if res.status_code in (400, 404):
            return res.json()
        return None

    def get_config(self):
        res = requests.get(f"{self.api_url}/config", headers=self.headers)
        if res.status_code == 200:
            return res.json()
        return None

    def patch_config(self,**kwargs):
        res = requests.patch(f"{self.api_url}/config", data=kwargs, headers=self.headers)
        if res.status_code == 204:
            return True
        return None

    def put_config(self,force: bool, path: str):
        res = requests.put(f"{self.api_url}/config", data={"force": force}, params={"path": path}, headers=self.headers)
        if res.status_code == 200:
            return True
        return None

    def get_rules(self):
        res = requests.get(f"{self.api_url}/rules", headers=self.headers)
        if res.status_code == 200:
            return res.json()
        return None