
# MCmod-info-mirror

为各平台的 Mod 信息缓存加速

不会计划提供 **文件** 下载

基于 [Curseforge](https://curseforge.com/) 和 [Modrinth](https://modrinth.com/) 作为信息源

参考 [CFCore](https://docs.curseforge.com/) 和 [Modrinth Docs](https://docs.modrinth.com/)

---

计划缓存策略为 **尽可能返回信息**。除了搜索接口有待规划，所有接口都会采用此策略。

具体表现为 **忽视数据是否过期**，以及 **忽略数据是否不全**，无条件返回已有数据，在过期、未找到等情况下先返回数据，然后后台拉取数据源

将在 headers 和 data 内提供 `trustable` 参数

---

Link:
- API: https://mcim.z0z0r4.top
- Docs: https://mcim.z0z0r4.top/docs

Contact:
- Eamil: z0z0r4@outlook.com
- QQ: 3531890582

## 使用

期待有启动器使用此镜像, awa!

请联系 z0z0r4，留下启动器名称与 UA 以方便统计

记得在 headers 加上您的项目的 UA，例如
- PCL2/2.3.0.50 Mozilla/5.0 AppleWebKit/537.36 Chrome/63.0.3239.132 Safari/537.36
- HMCL/3.3.172 Java/1.8.0_261
