
# MCmod-info-mirror

为各平台的 Mod 信息缓存加速

不会计划提供**文件**下载，成本过高

基于 [Curseforge](https://curseforge.com/) 和 [Modrinth](https://modrinth.com/) 作为信息源

参考 [CFCore](https://docs.curseforge.com/) 和 [Modrinth Docs](https://docs.modrinth.com/)

Link:
- API: https://mcim.z0z0r4.top
- Docs: https://mcim.z0z0r4.top/docs
- ~~Status: https://status.mcim.z0z0r4.top/status/mcim~~

Contact:
- Eamil: z0z0r4@outlook.com
- QQ: 3531890582

## 使用

期待有启动器使用此镜像, awa!

请联系 z0z0r4，留下启动器名称与 UA 以方便统计

记得在 headers 加上您的项目的 UA，例如
- PCL2/2.3.0.50 Mozilla/5.0 AppleWebKit/537.36 Chrome/63.0.3239.132 Safari/537.36
- HMCL/3.3.172 Java/1.8.0_261

## 部署

1. 克隆本仓库到本地 `git clone https://github.com/z0z0r4/mcim.git`
2. 安装 Python3 (推荐 3.10.4，未测试其他版本)，安装包 `pip install -r requirements.txt`
3. 准备一个 Curseforge API Key 以能够从 CFCore 获取信息  
   参见 [CFCore Authentication](https://docs.curseforge.com/#pagination-limits)
   填入 `config/config.json -> curseforge_api_key`
4. 准备 Mysql 数据库，将信息填入 `config/mysql.config.json` 
5. 启动 Fastapi `uvicorn webapi:api` 或 `python webapi.py`
   可以为 uvicorn 添加参数 `--port <port>` 或在 webapi.py 中修改端口

- 在找不到缓存或者缓存超时的情况下，会向官方源拉取到数据库然后返回信息
  也许需要一次性拉取缓存，参见 `sync.py`，不定期维护此脚本
- 设置 `config/config.json -> proxies` 以通过代理拉取官方源

> 2022-12-29  
> 已经基本上完成了整个镜像  
> 期待是否会有合作者？感谢！请联系  
> 如果有启动器准备接入，请联系并提供 UA...  
> 本服务可能会在必要的时候关闭，请不要把此镜像当做公开可选镜像使用  
> 如果您有什么建议，请联系或者提交 issue  
