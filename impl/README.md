# PAL 参考实现

> PAL Level 2 (Standard) 参考实现 — ESP32-S3 + PY32F002B

## 状态

| 组件 | 状态 | 预计完成 |
|---|---|---|
| I2C 热插拔底层 (PY32) | ✅ 已跑通 | 2026-06 |
| ESP32 固件框架 | 🔄 开发中 | 2026-08 |
| Agent 客户端库 | 🔄 开发中 | 2026-08 |

## 目录

```
esp32_pal/          # ESP32-S3 PAL 终端固件
├── core0/          # Core 0 — C, FreeRTOS, 写死
├── core1/          # Core 1 — MicroPython, 全开
└── sdkconfig       # ESP-IDF 配置

agent_side/         # Agent 侧 Python 库
└── pal_client.py   # PAL JSON 协议客户端
```

## 快速开始

见各子目录 README（开发完成后更新）。
