# PAL 参考实现

> PAL Level 2 (Standard) 参考实现 — 开发中

## 当前状态

PAL 规范目前处于草案阶段（v0.1）。参考实现代码正在开发中，将在后续版本中逐步发布。

## PAL Level 1 验证（已完成）

| 日期 | 平台 | 状态 |
|---|---|---|
| 2026-06-28 | ESP32-S3 (QFN56) + MicroPython v1.28.0 | ✅ 全部通过 |

验证项目：
- ✅ GPIO 控制（Pin 38, Pin 21）
- ✅ 硬件定时器（300ms / 800ms 双 LED 闪烁）
- ✅ I2C 扫描
- ✅ ADC 读取
- ✅ PAL JSON 协议往返（JSON → Python exec → stdout/stderr 捕获 → JSON 返回）
- ✅ 异常捕获与错误回报

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
