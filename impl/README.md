# PAL 参考实现

> PAL Level 2 (Standard) 参考实现 — 开发中

## 当前状态

PAL 规范目前处于草案阶段（v0.1）。参考实现代码正在开发中，将在后续版本中逐步发布。

预计包含：

```
esp32_pal/          # ESP32-S3 PAL 终端固件
├── core0/          # Core 0 — C + FreeRTOS（SPI / WebSocket / WDT / 引脚管理）
├── core1/          # Core 1 — MicroPython（PAL 协议处理 / 工具注册 / 事件推送）
└── sdkconfig       # ESP-IDF 配置

agent_side/         # Agent 侧 Python 库
└── pal_client.py   # PAL JSON 协议客户端
```

## 贡献

如果你有兴趣参与参考实现的开发，请查看 [CONTRIBUTING.md](../CONTRIBUTING.md) 并提交 PR。
