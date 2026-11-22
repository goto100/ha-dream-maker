# 造梦者 · Home Assistant

在 Home Assistant 中查看造梦者设备的数据。集成复用 Aqara Devices 已登录的账号，由它负责请求签名和令牌续期，无需再次输入密码。

## 已支持的设备

| 设备 | Aqara 型号 | HA 传感器 |
| --- | --- | --- |
| 造梦者空气质量监测器 | `aqara.adetector.drcn01` | 温度（°C）、相对湿度（%）、PM2.5（µg/m³）、CO₂（ppm） |

每 5 分钟从 Aqara 云端读取一次。每台设备的四项指标共用一次请求，各自取最近 15 分钟内的最新上报。某项指标没有新数据时，只有该项显示为不可用。

## 安装

1. 在 Aqara Home 中关联造梦者账号，确认能看到设备读数。
2. 在 HA 中安装并配置 **Aqara Devices**，确认该账号的配置条目已加载。该集成的 v1.5.2 要求账号下至少有一个它原生支持的设备。[Aqara Devices 安装说明](https://github.com/Darkdragon14/ha-aqara-devices)
3. 打开安装链接，在 HA 的 Marketplace（旧版为 HACS）中下载 **Dream Maker**。首次打开时，如果页面提示添加自定义仓库，选择「集成」。[在我的 Home Assistant 中打开造梦者](https://my.home-assistant.io/redirect/hacs_repository/?owner=goto100&repository=ha-dream-maker&category=integration)
4. 重启 HA Core，在「设置 → 设备与服务 → 添加集成」中搜索「造梦者」或「Dream Maker」，再选择已有的 Aqara Devices 账号。

账号新增支持的设备后，在 HA 中重新加载「造梦者」即可发现。

手动安装时，将仓库中的 `custom_components/dream_maker_aqara` 复制到 HA 的 `/config/custom_components/`，然后执行第 4 步。

## 兼容性

已验证 Home Assistant Core **2026.11.1** 和 Aqara Devices **v1.5.2**。本集成只保存来源配置条目的 ID。每次查询都会从 Aqara Devices 获取当前客户端，来源集成重载后会自动使用新连接。客户端属于 Aqara Devices 的内部 Python 接口，上游调整该接口时可能需要适配。[上游实现](https://github.com/Darkdragon14/ha-aqara-devices/tree/v1.5.2/custom_components/ha_aqara_devices)

## 许可证

本项目采用 [MIT 许可证](LICENSE)。
