# PAL: Physical Abstraction Layer

> **An Agent-Friendly Embedded Terminal Standard — v0.1 (Draft)**
>
> *REPL Is All You Need.*
>
> 作者：[yosaKun](https://github.com/hanasite) | 日期：2026-06-28 | 状态：草案阶段，欢迎讨论

---

## 摘要

当前 AI Agent 主要工作在数字环境中——写代码、调 API、搜网页。它们缺乏直接操控物理设备的能力。现有的嵌入式执行方案（裸机 C、ESP-Claw/Lua、树莓派/Linux）要么太重、要么绑定框架、要么对 Agent 不友好。

**PAL** 提出一个简洁的范式：利用 MicroPython REPL 作为 Agent 操控物理世界的唯一接口。核心理念：**Agent 在云端推理，终端只做执行。** 终端通过双核分离架构保证安全——Core 0 运行不可修改的 C 固件（硬实时、系统完整性），Core 1 运行开放的 MicroPython（Agent 操作空间）。不到 10 个硬件原语覆盖 99% 的物理操控需求。

PAL 不绑定任何 Agent 框架，基于标准 ESP-IDF 和 MicroPython，硬件成本约 $3-5。

---

## 1. 设计原则

### 原则 1：REPL 是唯一的 Agent 接口

```
Agent → PAL 终端:  Python 代码（通过 WebSocket JSON）
PAL 终端 → Agent:  stdout + stderr + 退出状态
```

- Agent 直接编写 Python 代码操控硬件
- **不需要预注册工具**（vs ESP-Claw 的 Skill Registry）
- **不需要定义 JSON Schema**（vs mimiclaw 的 `mimi_tool_t`）
- Claude / GPT / Qwen 已经会写 Python——让它们写 Python

### 原则 2：双核分离是安全模型

```
Core 0 (PRO CPU):  C + FreeRTOS — 写死，永不改动
Core 1 (APP CPU):  MicroPython — 完全开放给 Agent
```

- Core 0 负责系统完整性：通信总线、看门狗、电源管理
- Core 1 是 Agent 的"游乐场"：可以随便写 Python，搞崩了 Core 0 兜底
- 核间通过 FreeRTOS 队列通信，共享内存受原子操作保护

### 原则 3：Agent 在云端，终端只执行

```
┌──────────┐  WebSocket JSON  ┌──────────┐  SPI/I2C  ┌──────┐
│  Agent   │ ◄──────────────► │PAL 终端  │ ◄───────► │ 外设  │
│ (云端)    │                  │(ESP32-S3)│           │(任意) │
└──────────┘                  └──────────┘           └──────┘
```

- PAL 终端不存储 API Key、不运行 LLM、不做推理
- 终端是一个"物理执行器"，不是"微型大脑"
- 云端使用最强模型（Claude / GPT / 自部署），终端不受算力限制

### 原则 4：硬件原语最小化

物理世界 99% 的操作可以用不到 10 个原语覆盖：

| 原语 | 用途 | MicroPython 接口 |
|---|---|---|
| GPIO 读/写 | 继电器、LED、按钮、开关 | `Pin.in()` / `Pin.out()` |
| ADC 读 | 温度、光强、电压、电流 | `ADC.read()` |
| I2C 收发 | 传感器、EEPROM、控制器 | `I2C.writeto()` / `I2C.readfrom()` |
| SPI 收发 | 屏幕、Flash、高速设备 | `SPI.read()` / `SPI.write()` |
| PWM 输出 | 调光、调速、调压 | `PWM.duty()` |
| UART 收发 | 串口设备、调试 | `UART.write()` / `UART.read()` |

**PAL Level 1 要求支持全部 6 类原语。不定义上层语义——每个外设的行为由 Agent 自行理解。**

### 原则 5：传输层无关

Agent ↔ 终端之间的传输层是可替换的：

| 传输层 | 适用场景 | 默认 |
|---|---|---|
| **WebSocket** | WiFi 局域网 | ✅ PAL Level 2+ 默认 |
| UART | 有线串口 | 调试/降级 |
| BLE | 低功耗无线 | 移动设备 |
| MQTT | 广域网 | 远程控制 |

---

## 2. 架构

### 2.1 总览

```
┌─────────────────────────────────────────────────────────┐
│                     Layer 4: Agent (云端)                │
│  ┌───────────────────────────────────────────────────┐ │
│  │  AstrBot / LangChain / 自研 Agent 框架              │ │
│  │  · LLM 推理  · 工具调度  · 对话管理                │ │
│  └───────────────────┬───────────────────────────────┘ │
└──────────────────────┼──────────────────────────────────┘
                       │ WebSocket JSON (PAL Protocol)
┌──────────────────────▼──────────────────────────────────┐
│                     Layer 3: PAL 终端                    │
│  ┌───────────────────────────────────────────────────┐ │
│  │              ESP32-S3 (或等效双核 MCU)             │ │
│  │                                                    │ │
│  │  ┌─── Core 0 (C, FreeRTOS, 写死) ────────────┐   │ │
│  │  │ · SPI/I2C/UART 硬件驱动                     │   │ │
│  │  │ · 系统看门狗 (WDT)                           │   │ │
│  │  │ · 网络维持 (WiFi 自动重连)                    │   │ │
│  │  │ · 引脚所有权管理                              │   │ │
│  │  │ · MicroPython 心跳监控                        │   │ │
│  │  │                                              │   │ │
│  │  │ NEVER TOUCH. 烧录后永不再改。                 │   │ │
│  │  └──────────────────────────────────────────────┘   │ │
│  │                       ↕  FreeRTOS Queue              │ │
│  │  ┌─── Core 1 (MicroPython, 全开) ──────────────┐   │ │
│  │  │ · PAL Protocol 处理（WebSocket JSON）         │   │ │
│  │  │ · 工具注册表（@tool 装饰器, 动态扩展）         │   │ │
│  │  │ · machine 模块 → 硬件操控                     │   │ │
│  │  │ · uasyncio → 并发任务管理                     │   │ │
│  │  │                                              │   │ │
│  │  │ ANYTHING GOES. 崩了 Core 0 会重启你。         │   │ │
│  │  └──────────────────────────────────────────────┘   │ │
│  └───────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ SPI / I2C / UART / GPIO
┌──────────────────────▼──────────────────────────────────┐
│                     Layer 1-2: 外设                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │  继电器模块  ·  传感器阵列  ·  电机驱动  ·  LED    │ │
│  │  料盘单元  ·  编码器  ·  屏幕  ·  ...              │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Core 0 详细定义（硬实时安全域）

```
Core 0 是 PAL 终端的"不可变基础层"。代码编译后锁死，OTA 更新需物理确认。

职责：
  ├─ 硬件通信总线驱动（SPI/I2C/UART）
  │    └─ DMA + 中断，μs 级响应
  ├─ 系统看门狗（10s 超时 → 全系统复位）
  ├─ WiFi 维持 + 断线自动重连
  ├─ 引脚所有权表
  │    ├─ OWNER_SYSTEM: MicroPython 无权操作
  │    └─ OWNER_AGENT: 暴露给 Core 1
  └─ Core 1 心跳监控
       └─ 超时 → 重启 MicroPython VM，不影响 Core 0

不可变：
  ├─ 不透传 API Key
  ├─ 不运行 LLM 推理
  ├─ 不做上层协议解析
  └─ 不暴露 Core 0 的系统引脚给 Core 1
```

### 2.3 Core 1 详细定义（Agent 操作域）

```
Core 1 是 Agent 的"物理工作区"。代码可以随时通过 REPL 修改。

职责：
  ├─ PAL Protocol 处理（WebSocket ↔ JSON ↔ Python 执行）
  ├─ 工具注册表（@tool 装饰器，Python dict，动态扩展）
  ├─ 硬件原语执行（通过 machine 模块）
  └─ uasyncio 并发管理（接收命令 + 定时上报 + 事件推送）

安全边界：
  ├─ 不能访问 Core 0 的系统引脚
  ├─ 不能禁用看门狗
  ├─ 不能修改网络配置（由 Core 0 管理）
  └─ 崩溃不影响 Core 0 运行
```

---

## 3. PAL 协议

### 3.1 消息格式

**Agent → PAL 终端（命令/代码执行）：**

```json
{
  "version": "1",
  "id": "msg_001",
  "type": "exec",
  "tool": null,
  "code": "led = Pin(5, Pin.OUT); led.on()",
  "timeout_ms": 10000
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `version` | string | ✅ | 协议版本，当前 `"1"` |
| `id` | string | ✅ | 消息唯一标识，响应时原样返回 |
| `type` | string | ✅ | `"exec"` (执行 Python) 或 `"tool"` (调用已注册工具) |
| `tool` | string | 否 | `type="tool"` 时指定工具名 |
| `code` | string | 否 | `type="exec"` 时的 Python 代码 |
| `timeout_ms` | integer | 否 | 执行超时，默认 30000ms |

**PAL 终端 → Agent（结果回传）：**

```json
{
  "version": "1",
  "id": "msg_001",
  "type": "result",
  "stdout": "Pin 5 set HIGH\n",
  "stderr": "",
  "error": false,
  "exec_time_ms": 12,
  "truncated": false
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 对应请求的 id |
| `stdout` | string | 标准输出（print() 内容） |
| `stderr` | string | 标准错误 |
| `error` | boolean | Python 执行是否抛出异常 |
| `exec_time_ms` | integer | 执行耗时（毫秒） |
| `truncated` | boolean | 输出是否被截断（>4KB） |

**PAL 终端 → Agent（事件推送，主动上报）：**

```json
{
  "version": "1",
  "id": "evt_001",
  "type": "event",
  "event": "pin_change",
  "data": {
    "pin": 6,
    "value": 1
  },
  "timestamp_ms": 1719552000000
}
```

| 事件名 | 说明 |
|---|---|
| `boot` | 终端启动完成 |
| `shutdown` | 终端即将关闭/复位 |
| `pin_change` | GPIO 引脚电平变化（需配置中断） |
| `adc_threshold` | ADC 超出阈值 |
| `connection_lost` | 网络断开 |
| `connection_restored` | 网络恢复 |
| `watchdog_warning` | Core 1 即将被看门狗复位 |
| `core1_restarted` | Core 1 MicroPython VM 已重启 |

### 3.2 典型会话

```
Agent                              PAL 终端
  │                                    │
  │ {"id":"1","type":"exec",           │
  │  "code":"import machine;           │
  │          [hex(d) for d in          │
  │           I2C(0).scan()]"}          │
  │──────────────────────────────────→│
  │                                    │ 执行 I2C.scan()
  │                                    │
  │ {"id":"1","type":"result",         │
  │  "stdout":"['0x20','0x21']",      │
  │  "error":false}                    │
  │←──────────────────────────────────│
  │                                    │
  │ {"id":"2","type":"exec",           │
  │  "code":"from machine import Pin;  │
  │   led=Pin(5,Pin.OUT);             │
  │   led.on()"}                        │
  │──────────────────────────────────→│
  │                                    │ 翻转 LED
  │ {"id":"2","type":"result",         │
  │  "stdout":"","error":false}        │
  │←──────────────────────────────────│
  │                                    │
  │         ...（一段时间后）...         │
  │                                    │
  │                                    │ GPIO 引脚变化
  │ {"id":"evt_01","type":"event",     │
  │  "event":"pin_change",            │
  │  "data":{"pin":6,"value":0}}      │
  │←──────────────────────────────────│
```

### 3.3 安全限制

```python
# PAL 终端预定义的 Python 环境
# Agent 代码中以下操作将被拦截（Core 0 层拒绝）:

import machine

# ❌ 访问系统保留引脚
machine.Pin(0, machine.Pin.OUT)    # 系统引脚 → OSError

# ❌ 修改网络配置
import network
network.WLAN().connect('...')       # 由 Core 0 管理 → OSError

# ❌ 禁用看门狗
machine.WDT(0)                      # 由 Core 0 独占 → OSError

# ✅ 以下完全允许:
led = machine.Pin(5, machine.Pin.OUT)
led.on()
adc = machine.ADC(machine.Pin(1))
temp = adc.read()
i2c = machine.I2C(0)
devices = i2c.scan()
```

---

## 4. 兼容性等级

### PAL Level 1 — Minimal

```
硬件: 任何支持 MicroPython 的 MCU (ESP32 / RP2040 / STM32 / ...)
架构: 单核，无安全隔离
传输: UART REPL
成本: ~$2-5

用途:
  · 开发调试
  · 教育实验
  · 个人 DIY 项目

限制:
  · 无 Core 0 保护，Agent 代码可拖死系统
  · UART 带宽有限 (115200-921600 bps)
  · 无网络事件推送
```

### PAL Level 2 — Standard (推荐)

```
硬件: ESP32-S3 或等效双核 MCU
架构: Core 0 (C, FreeRTOS) + Core 1 (MicroPython)
      完整双核分离，引脚所有权管理，WDT 分层
传输: WebSocket (默认) + UART (降级)
成本: ~$5-15

用途:
  · 工业现场的 Agent 操控终端
  · 实验室自动化
  · 智能农业/楼宇控制

能力:
  · Core 0 保证系统完整性
  · WiFi 自动重连
  · 事件主动推送
  · OTA 固件升级
```

### PAL Level 3 — Industrial

```
硬件: 双 MCU 物理隔离
      外部安全 MCU (如 PY32) + 主 MPU (ESP32-S3 或更高)
架构: 安全 MCU 做通信代理 + 看门狗监管
      主 MCU 跑 MicroPython，可热替换
传输: Ethernet + CAN + RS-485 多冗余
成本: ~$20-50

用途:
  · 产线自动化
  · 危险环境远程操控
  · 高可靠性工业控制

额外能力:
  · 双 MCU 互相看门狗
  · 冗余通信链路
  · 工业温度范围 (-40~85°C)
  · 电流/电压监控
  · 安全停机回路
```

---

## 5. 与已有方案对比

| 维度 | PAL | ESP-Claw | mimiclaw | 裸机 C + 串口 | 树莓派 + GPIO |
|---|---|---|---|---|---|
| **Agent 位置** | 云端 | 终端 | 终端 | 云端（仅预定义命令） | 终端 |
| **脚本语言** | **Python** | Lua | C (无脚本层) | 无 | Python |
| **LLM 生成代码准确率** | **高** | 中 | N/A | N/A | 高 |
| **工具注册** | **无需注册** | Skill Registry | `mimi_tool_t` C struct | 预定义指令集 | `RPi.GPIO` 库 |
| **加新操作** | **Agent 当场写 Python** | LLM 生成 Lua | 改 C → 编译 → 烧录 | 改 C → 编译 | Agent 写 Python |
| **安全隔离** | **Core 0 锁死** | 无显式隔离 | Core 0/1 分工 | 无 | 无 |
| **硬件成本** | **~$3-5** (Level 2) | ~$15+ | ~$5 | ~$1-5 | ~$35+ |
| **功耗** | ~0.5W | ~1W | ~0.5W | ~0.1W | ~5W |
| **启动时间** | ~1s | ~2s | ~2s | ~0.1s | ~30s |
| **硬实时** | ✅ Core 0 保证 | ⚠️ 受 Agent 影响 | ⚠️ 受 Agent 影响 | ✅ | ❌ |
| **框架绑定** | **无** | ESP-Claw 生态 | mimiclaw | 无 | Linux 生态 |
| **硬件库覆盖** | **machine 模块全内置** | 自己写 lua_driver_* | 自己写 | 自己写 | 社区库 |
| **代码量(网关层)** | **~700 行** | 几万行 | ~2000 行 | 几百行 | 依赖分发 |
| **参考实现** | 本仓库 `impl/` | ESP-Claw 仓库 | mimiclaw 仓库 | — | — |

> 注：表中对比对象为 PAL Level 2 (Standard)。ESP-Claw 数据来源：[espressif/esp-claw](https://github.com/espressif/esp-claw)，mimiclaw 数据来源：[memovai/mimiclaw](https://github.com/memovai/mimiclaw)。

---

## 6. 参考实现

本规范附带一个 PAL Level 2 参考实现（目录 `impl/`），基于 ESP32-S3 + PY32F002B：

```
impl/
├── esp32_pal/              # ESP32-S3 PAL 终端固件
│   ├── core0/              # Core 0 C 代码 (ESP-IDF + FreeRTOS)
│   │   ├── spi_task.c      # SPI DMA 驱动
│   │   ├── ws_client.c     # WebSocket 客户端
│   │   ├── wdt_task.c      # 看门狗 + Core 1 心跳监控
│   │   └── pin_manager.c   # 引脚所有权管理
│   ├── core1/              # Core 1 MicroPython 代码
│   │   ├── main.py         # PAL 协议处理入口
│   │   ├── tools.py        # @tool 装饰器 + 工具注册表
│   │   ├── board.py        # 预注册外设封装
│   │   └── events.py       # 事件推送管理
│   ├── Kconfig.projbuild   # 编译时配置
│   └── sdkconfig.defaults
├── agent_side/             # Agent 侧 Python 库
│   └── pal_client.py       # PAL JSON 协议客户端
└── README.md               # 搭建指南
```

**参考实现状态：**

| 组件 | 状态 |
|---|---|
| PAL 协议定义 | ✅ v0.1 |
| Core 0 C 框架 | 🔄 开发中 (预计 2026 年 8 月) |
| Core 1 MicroPython | 🔄 开发中 |
| Agent 客户端库 | 🔄 开发中 |
| 硬件验证（I2C 热插拔底层） | ✅ 已跑通 (PY32F002B) |

---

## 7. 设计动机：为什么不是 ESP-Claw

[ESP-Claw](https://github.com/espressif/esp-claw) 是 Espressif 官方的 "Chat Coding" AI Agent 框架，在 ESP32 上跑 Lua 解释器 + LLM Agent 循环。它是最接近 PAL 的已有方案，也是我们最重要的参考对象。但在以下核心假设上 PAL 选择了相反的方向：

| ESP-Claw 的假设 | PAL 的立场 |
|---|---|
| Agent 应该跑在 MCU 上 | **Agent 应该在云端推理，终端只执行** |
| LLM 生成 Lua 代码 | **LLM 应该生成它最擅长的 Python** |
| 需要 Skill Registry 预注册能力 | **不需要预注册——Agent 当场写代码** |
| 需要 IM 通道（Telegram/微信） | **WebSocket 一条线，不引入 IM 依赖** |
| 需要 Event Router 规则引擎 | **设备事件由 Core 1 Python 处理，灵活度更高** |
| 8MB PSRAM 门槛 | **无 PSRAM 要求，$3 MCU 也能跑** |

**PAL 不否认 ESP-Claw 的工程价值。但 Agent-on-Device 存在三个根本性问题，PAL 在每个问题上选择了相反的答案。**

### 问题 1：占用资源过大

Agent 循环需要以下资源来维持最基本的 ReAct 推理：

```
LLM API 调用缓冲区:  ~4-16 KB
工具注册表 + Schema:  ~2-8 KB
上下文窗口 (对话历史): ~8-64 KB
JSON 解析堆:          ~4-16 KB
Skills 文件系统:       ~不定 (Markdown → Flash)
```

ESP-Claw 要求 **8 MB PSRAM + 8 MB Flash**，仅固件框架就占用数万行代码。这不是"轻量嵌入式"——这是把一台小型 Linux 机器的负载搬到了 MCU 上。ESP32-S3 的 512 KB SRAM 跑 FreeRTOS + WiFi 栈 + TLS 已经占了大半，剩下的要同时养 Agent 循环和硬件驱动，内存碎片化是常态。

**PAL 的立场：** 终端不跑 Agent 循环。Core 0 只做 I/O 和 WDT（~16KB 栈足够），Core 1 只跑 Python VM（~100KB heap）。剩余资源全部释放给实际任务。

### 问题 2：Agent 循环无法保证稳定性

Agent 的 ReAct 循环本质上是一个**链式重试机制**：

```
Think → Act → Observe → Think → Act → Observe → ... (最多 10 轮)
```

每一轮都可能出问题：

| 故障点 | 后果 |
|---|---|
| LLM API 超时或返回格式错误 | Agent 循环卡住，等待超时 |
| 工具调用 JSON 解析失败 | 需要额外 round-trip 让 LLM 修正 |
| 上下文窗口溢出 | 需要 compaction / summarization，额外 LLM 调用 |
| WiFi 断连 | API 不可达，设备静默等待重连 |

在服务器上，这些故障有成熟的 retry / circuit-breaker / health-check 机制。在 MCU 上，**一个未处理的网络超时可能导致整个 FreeRTOS 任务栈溢出**——然后看门狗复位整块板子。

ESP-Claw 的 Agent 循环跑在 Core 1 上，但 Core 1 如果崩了，设备失去的不只是 AI 能力——是全部上层逻辑。这就是为什么在生产环境中，你无法信任一个运行 LLM 推理循环的 MCU。

**PAL 的立场：** Agent 循环的稳定性问题交给云端解决。云端的 AstrBot / LangChain 有完整的异常处理、超时重试、上下文管理基础设施。PAL 终端只接收已经决策好的命令——"端上来的是菜，不是菜谱"。

### 问题 3：AI 思考需要时间，实时任务等不起

这是 Agent-on-Device 最本质的物理矛盾：

```
I2C 喂狗周期:   ~2s（错过 3 次 = 设备离线）
LLM API 延迟:   ~500ms-5s（取决于模型和网络）
Agent 多轮推理:  ~2-30s（取决于任务复杂度）
```

如果 Agent 循环正在等 LLM 返回（5 秒），而这时 PY32 交换机通过 SPI 发来一帧"料盘 0x23 掉线"，**谁来处理这帧数据？**

Agent-on-Device 的答案是"分优先级"——让 I/O 任务优先级比 Agent 循环高。这确实能让 SPI 中断抢到 CPU，但 Agent 的上下文状态在这些打断中可能变得不一致。更严重的是，**Agent 自己也要发起实时操作**——它推理出"需要翻转 0x20 的 LED"，发 SPI 命令。如果这个推理花了 3 秒，LED 翻转晚了 3 秒——在工业场景中，3 秒可以意味着一批料被错装。

**PAL 的立场：** 实时任务（I2C 喂狗、SPI 帧处理、WDT、设备表更新）全部在 PY32 交换机上独立运行，与 Agent 完全异步。PAL 终端只做最上层的决策翻译——Agent 在云端推理出"翻 LED"，终端收到 JSON 后 <1ms 内转发给 PY32。AI 的慢和物理的快之间，有一道明确的墙。

### 总结

```
               Agent-on-Device              PAL
               ────────────────             ───
资源:           Agent 吃掉一半 MCU 资源        Agent 不占终端资源
稳定性:         一个 API 超时可能拖死板子      云端负责容错，终端只管执行
实时性:         推理延迟 vs 喂狗周期 矛盾      实时任务在 PY32 上完全独立
职责边界:       MCU 既是大脑又是手             终端是手，大脑在云上
调试:           抓日志看 ReAct trace          PY32 逻辑分析仪 + WebSocket JSON
```

**Agent-on-Device 让嵌入式终端背负了不该它承担的复杂度。PAL 把 Agent 留在云端，终端只做一件事：收到命令，执行，回报结果。**

---

## 8. Agent-on-Device 的硬件门槛、适用与不适用场景

以上批判并非否定 Agent-on-Device，而是界定其**适用边界**。以下是基于资源约束和工程边界的诚实分析。

### 8.1 硬件门槛

Agent-on-Device 对硬件有硬性的最低要求。目前已知的运行 Agent 循环的 MCU：

| 芯片 | Agent 方案 | PSRAM 要求 | Flash 要求 | 模组单价 |
|---|---|---|---|---|
| ESP32 (无 PSRAM) | ❌ 无法运行 | — | — | ~$2 |
| ESP32-S3 | ESP-Claw, pycoClaw | **≥ 8 MB** | **≥ 8 MB** | ~$3-5 |
| ESP32-P4 | ESP-Claw | ≥ 8 MB | ≥ 16 MB | ~$8-15 |
| 树莓派 Zero 2W | 任何 Python Agent | 512 MB (DDR) | SD 卡 | ~$15 |
| 树莓派 4B | 任何 Python Agent | 1-8 GB (DDR) | SD 卡 | ~$35-75 |

**Agent-on-Device 的硬件底线是 ESP32-S3 + 8MB PSRAM。** 这个配置大概 $3-5/模组。低于这条线（ESP32 无 PSRAM、ESP8266、ST BlueNRG、STM32F1/F4/G0 系列、国产 PY32/AT32 等）**完全不可能跑 Agent 循环**——不是因为算力不够，是因为 RAM 装不下一个 ReAct 循环的运行时。

PAL Level 1 可以在**无 PSRAM 的 ESP32（~$2）**上运行，因为终端不需要 Agent 循环——只需要一个 MicroPython VM。这就是"Agent 不在终端"带来的硬件成本差异：PAL 的门槛比 Agent-on-Device 低一整档。

### 8.2 适用场景（Agent-on-Device 的合理选择）

| 场景 | 为什么 Agent-on-Device 合适 |
|---|---|
| **离线/无网络环境** | 野外、矿井、水下——WiFi 不可用。Agent 必须在本地推理和决策。这是 Agent-on-Device 最强也是唯一不可替代的优势。 |
| **隐私敏感数据** | 医疗设备、家庭监控——数据不能出设备。本地 Agent 在端侧完成推理，不经过云端。 |
| **单功能消费设备** | 智能音箱、桌面机器人——单一功能 + 固定交互模式，Agent 推理任务简单且可预期。没有多节点协调的复杂度。 |
| **低延迟交互（无实时要求）** | 语音助手、表情机器人——不需要微秒级响应，但需要避开网络延迟。本地小模型推理可以在 100-500ms 内完成。 |
| **原型/教育/研究** | 用一块 ESP32-S3 快速搭建概念验证，证明"AI 可以控制硬件"。成本 $5-10 即可开始。 |

### 8.3 不适用场景（应该选 PAL 或裸机方案）

| 场景 | 为什么 Agent-on-Device 不合适 |
|---|---|
| **多节点协调系统** | 料盘阵列、产线传感器网络——一个 Agent 要管理几十个物理节点。Agent 在本地 = 只有一个大脑管理所有节点，单点故障。云端 Agent 可以全局视角。 |
| **硬实时工业控制** | 电机驱动、电源管理、安全停机——I2C 喂狗周期 2s，Agent 多轮推理 2-30s。实时任务必须与 Agent 完全异步。**AI 思考是需要时间的，物理世界等不起。** |
| **成本敏感场景（$2-3 决定生死）** | 智能农业传感器、一次性物流标签——每个节点加 $5 PSRAM = 成本翻倍。PY32（$1）+ 裸机 C 才是正解。 |
| **长期连续运行（24/7）** | 产线、仓库、基站的设备监控——Agent 循环的内存泄漏、LLM API 波动、WiFi 断连累积，最终导致 WDT 复位。工业场景不接受"平均每周复位一次"。 |
| **需要云端最强模型** | 复杂视觉理解、多模态推理——端侧小模型（Gemma、Phi）远不如 Claude/GPT。如果业务本身需要大模型，Agent 留在云端是唯一选择。 |
| **频繁更新业务逻辑** | 产线流程变更、仓库 SKU 重组——如果 Agent 在终端，改工具逻辑要 OTA 固件。PAL 改一行 Python 重启 Core 1 即可。 |

### 8.4 决策矩阵

```
                    有稳定网络？
                   /          \
                 是            否
                 │             └──→ Agent-on-Device（离线刚需）
                 │
              有硬实时要求？
             /           \
           是             否
           │              └──→ 节点数 > 1？
           │                  /          \
           │                是            否
           │                │             │
           ▼                ▼             ▼
     ┌─────────┐     ┌─────────┐    ┌──────────────┐
     │裸机 C    │     │  PAL    │    │Agent-on-Device│
     │或 PAL +  │     │Level 2  │    │(单设备, 无实时)│
     │独立实时层│     │         │    │               │
     └─────────┘     └─────────┘    └──────────────┘
```

**PAL 的适用区是"有网络 + 无硬实时 + 需要多节点协调或频繁变更逻辑"。Agent-on-Device 的适用区是"无网络或隐私敏感 + 单设备 + 无实时冲突"。两者不是竞争关系——是互补的。**

---

## 9. FAQ

**Q: PAL 和 MicroPython 自带的 WebREPL 有什么区别？**

A: WebREPL 提供的是一个交互式的 Python REPL，没有安全边界——你可以 `import machine` 然后操作任何引脚，包括系统用的。PAL 在 WebREPL 的基础上加了：① 引脚所有权管理；② Core 0 系统保护；③ 结构化的 JSON 协议（不只是裸 REPL）；④ 事件推送机制。

**Q: 一定要用 ESP32-S3 吗？**

A: 不。PAL Level 1 可以在任何支持 MicroPython 的 MCU 上跑。PAL Level 2 建议双核 MCU 以实现 Core 0/Core 1 分离，ESP32-S3 是目前性价比最高的选项。

**Q: 安全吗？Agent 会把硬件搞坏吗？**

A: PAL Level 2+ 的 Core 0 负责保护系统完整性。Agent 只能操作被标记为 `OWNER_AGENT` 的引脚，不能禁用看门狗、不能改网络配置、不能操作系统总线。最坏情况：Agent 崩了 → Core 0 检测到心跳超时 → 自动重启 Core 1 MicroPython VM → 系统继续运行。

**Q: 延迟怎么样？**

A: Agent → WebSocket → JSON 解析 → Python 执行 → machine 库（C 底层）→ 硬件。典型往返：WiFi 局域网 <10ms，Python 执行 <1ms。总量 ~10-20ms。对于物理操控场景（开关继电器、读传感器、更新显示），这个延迟完全可接受。

---

## 10. 贡献与讨论

本规范处于草案阶段。以下问题需要社区的输入：

1. **Core 0 的边界应该定在哪里？** 哪些功能必须锁死在 Core 0，哪些可以下沉？
2. **PAL 协议是否需要支持流式执行？** 即 Agent 持续发送代码块，终端持续返回结果？
3. **多终端协调**：多个 PAL 终端是否需要一个上层的协调协议（类似 I2C 多从机）？
4. **认证与安全**：Agent ↔ 终端之间的认证机制应该如何设计？
5. **Level 3 的冗余策略**：双 MCU 物理隔离的具体方案？

欢迎通过 Issues 提交讨论或 Pull Request 参与规范修订。

---

## 11. 许可

本规范文档采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 许可。

参考实现代码（`impl/` 目录）采用 [MIT](https://opensource.org/license/MIT) 许可。

---

> *"The best way to predict the future is to define it."*
>
> *PAL v0.1 — 2026-06-28, 于安徽理工大学*
