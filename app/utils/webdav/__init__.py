from webdav4.fsspec import WebdavFileSystem
from webdav4.client import Client
from app.config import WebDavConfig
from app.utils.loger import log

webdav_config = WebDavConfig.load()


def init_webdav():
    global client, fs
    client = Client(
        webdav_config.base_url, auth=(webdav_config.username, webdav_config.password)
    )
    fs = WebdavFileSystem(
        webdav_config.base_url, auth=(webdav_config.username, webdav_config.password)
    )
    return client, fs


client: Client = Client(
    webdav_config.base_url, auth=(webdav_config.username, webdav_config.password)
)
fs: WebdavFileSystem = WebdavFileSystem(
    webdav_config.base_url, auth=(webdav_config.username, webdav_config.password)
)

log.success("Webdav client and fs ready.")