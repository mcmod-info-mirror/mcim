# MCmod-info-mirror

为各平台的 Mod 的缓存加速，由 [MCLF-CN #3](https://github.com/MCLF-CN/docs/issues/3) 提议

基于 [BMCLAPI](https://bmclapidoc.bangbang93.com) 使用网盘缓存的先例，当前文件缓存在 [Mr.yang](https://github.com/YangHaoNing-CN) 和 [八蓝米](https://alist.8mi.tech) 支持下试运行！

以 [Curseforge](https://curseforge.com/) 和 [Modrinth](https://modrinth.com/) 为镜像源

- [API](https://mod.mcimirror.top)
- [Docs](https://mod.mcimirror.top/docs)
- [Status](https://status.mcimirror.top)

## 使用

以下所有内容均建立在已经能够成功从官方源下载数据的基础上，不了解的话请前往 [CFCore](https://docs.curseforge.com) 和 [Modrinth Docs](https://docs.modrinth.com) 参考。

MCIM 的目标是 100% 兼容官方的 API 结构，可以直接替换，方便迁移，可以直接替换，具体可以比对 [Docs](https://mod.mcimirror.top/docs)，你可以直接在里面尝试。

### Modrinth

- `api.modrinth.com/v2` or `staging-api.modrinth.com/v2` -> `mod.mcmirror.top/modrinth`
- `cdn.modrinth.com` -> `mod.mcimirror.top`

### Curseforge

- `api.curseforge.com` -> `mod.mcmirror.top/curseforge`
- `edge.forgecdn.net` or `mediafilez.forgecdn.net` -> `mod.mcimirror.top`

## 缓存思路

由于除了搜索接口是反代，其他都是通过数据库缓存，无法保证一定已缓存，也可能过期。

基本思路为 **忽视数据是否过期**，以及 **忽略数据是否不全**，无条件返回已有数据，在过期、未找到等情况下先返回数据，然后后台拉取源站。

不可信的响应将在 `headers` 内提供 `Trustable` 参数，提供 `sync_at` 缓存时间

## 注意事项

请联系在 [启动器信息](https://github.com/mcmod-info-mirror/mcim/issues/4)，留下 UA 以方便统计

记得在 `headers` 加上您的项目的 UA，例如

- PCL2/2.3.0.50 Mozilla/5.0 AppleWebKit/537.36 Chrome/63.0.3239.132 Safari/537.36
- HMCL/3.3.172 Java/1.8.0_261

**文件**下载可能存在一定的不稳定性，当前缺少多节点网盘的分流，建议启动器在未能成功下载的情况下才尝试使用镜像源

未缓存部分接口，如果有 API 需要更新或新增请联系。

## 部署

先安装 docker，clone 到本地后直接 `docker-compose up -d` 即可，记得修改 `docker-compose.yml` 里面的 `config` 挂载目录，以及 `config` 内容

## 鸣谢

- [Mr.yang](https://github.com/YangHaoNing-CN)
- [八蓝米](https://github.com/8Mi-Tech)
- [Pysio](https://github.com/pysio2007)

## 联系

- Eamil: z0z0r4@outlook.com
- QQ: 3531890582

## 协议

1. MCIM 下的所有文件，除 MCIM 本身的源码之外，归源站点所有
2. MCIM 会尽量保证文件的完整性、有效性和实时性，对于使用 MCIM 带来的一切纠纷，与 MCIM 无关。
3. 所有使用 MCIM 的程序必需在下载界面或其他可视部分标明来源
4. 禁止在 MCIM 上二次封装其他协议
