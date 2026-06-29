# PAL: Physical Abstraction Layer

> **PAL abstracts physical execution behind standard interfaces — making hardware modular, language-agnostic, and AI-ready.**
>
> *REPL Is All You Need.*
>
> 作者：[yosaKun](https://github.com/hanasite) | 日期：2026-06-28 | 状态：草案阶段，欢迎讨论

---

## 目录

- [摘要](#摘要)
- [0. 为什么是现在：CLI、嵌入式与 Python 的交汇](#0-为什么是现在clii嵌入式与-python-的交汇)
  - [0.1 CLI 工具给了 LLM 什么](#01-cli-工具给了-llm-什么)
  - [0.2 嵌入式给了 LLM 什么](#02-嵌入式给了-llm-什么)
  - [0.3 为什么是 Python](#03-为什么是-python)
- [PAL 的范围：不是什么，是什么](#pal-的范围不是什么是什么)
- [1. 设计原则](#1-设计原则)
  - [开发板 vs 工程项目：两种 Agent 操作模式](#开发板-vs-工程项目两种-agent-操作模式)
- [2. 架构](#2-架构)
  - [2.1 总览](#21-总览)
  - [2.2 Core 0（硬实时安全域）](#22-core-0-详细定义硬实时安全域)
  - [2.3 Core 1（Agent 操作域）](#23-core-1-详细定义agent-操作域)
- [3. PAL 协议](#3-pal-协议)
  - [3.1 消息格式](#31-消息格式)
  - [3.2 典型会话](#32-典型会话)
  - [3.3 安全限制](#33-安全限制)
- [4. 安全模型](#4-安全模型)
  - [4.1 威胁模型](#41-威胁模型)
  - [4.2 五层防御架构](#42-五层防御架构)
  - [4.3 故障模式与恢复](#43-故障模式与恢复)
  - [4.4 PAL 不能保护什么](#44-pal-不能保护什么)
  - [4.5 安全模型的适用前提](#45-安全模型的适用前提)
- [5. 兼容性等级](#5-兼容性等级)
  - [Level 1 — Minimal](#pal-level-1--minimal)
  - [Level 2 — Standard](#pal-level-2--standard-推荐)
  - [Level 3 — Industrial](#pal-level-3--industrial)
- [6. 与已有方案对比](#6-与已有方案对比)
  - [6.1 PAL 与 MCP](#61-pal-与-mcp物理世界的最后一段)
- [7. 参考实现](#7-参考实现)
- [8. 设计动机：为什么不是 ESP-Claw](#8-设计动机为什么不是-esp-claw)
  - [问题 1：占用资源过大](#问题-1占用资源过大)
  - [问题 2：Agent 循环无法保证稳定性](#问题-2agent-循环无法保证稳定性)
  - [问题 3：AI 思考需要时间，实时任务等不起](#问题-3ai-思考需要时间实时任务等不起)
  - [总结](#总结)
  - [为什么云端是正确答案](#为什么云端是正确答案)
- [9. Agent-on-Device 的硬件门槛与场景](#9-agent-on-device-的硬件门槛适用与不适用场景)
  - [9.1 硬件门槛](#91-硬件门槛)
  - [9.2 适用场景](#92-适用场景agent-on-device-的合理选择)
  - [9.3 不适用场景](#93-不适用场景应该选-pal-或裸机方案)
  - [9.4 决策矩阵](#94-决策矩阵)
- [10. 自进化 vs 预蒸馏](#10-自进化-vs-预蒸馏嵌入式场景的可靠性边界)
  - [10.1 物理世界的容错率是零](#101-物理世界的容错率是零)
  - [10.2 个人开发者 vs 工程级的可靠性模型](#102-个人开发者-vs-工程级的可靠性模型)
  - [10.3 混合模型](#103-pal-的答案预蒸馏--自进化的混合模型)
  - [10.4 为什么是混合模型](#104-为什么是混合模型)
  - [10.5 对社区的意见](#105-对社区的意见)
- [11. AI 在嵌入式系统中的决策边界](#11-ai-在嵌入式系统中的决策边界)
  - [11.1 三层决策模型](#111-三层决策模型)
  - [11.2 AI 可以做什么：拼积木](#112-ai-可以做什么拼积木)
  - [11.3 AI 不可以做什么：硬实时域](#113-ai-不可以做什么硬实时域)
  - [11.4 紧急程度分级](#114-紧急程度分级ai-的决策权限表)
  - [11.5 AI 被污染](#115-ai-被污染物理世界的特殊风险)
  - [11.6 边界清单](#116-明确适用场景ai-在嵌入式中的边界清单)
- [12. FAQ](#12-faq)
- [13. 贡献与讨论](#13-贡献与讨论)
  - [MCP 集成路线](#future-workmcp-集成路线)
- [14. 许可](#14-许可)

---

## 摘要

当前 AI Agent 主要工作在数字环境中——写代码、调 API、搜网页。它们缺乏直接操控物理设备的能力。现有的嵌入式执行方案（裸机 C、ESP-Claw/Lua、树莓派/Linux）要么太重、要么绑定框架、要么对 Agent 不友好。

**PAL** 不是固件，不是库，不是操作系统。它是一个 **基于标准通信接口的模块化执行终端架构**。

核心理念：在**已知的物理外设**（UART / I2C / SPI / GPIO）和**公认的传输协议**（JSON）之上，把"决策逻辑"和"硬件执行"彻底解耦。

- **决策层（大脑）**：云端 Agent 通过 JSON 下发指令，不关心底层是什么芯片
- **执行层（手）**：终端通过标准 MicroPython REPL 执行 `code` 字段，返回 JSON 结果

**所有符合 PAL 规范的设备——ESP32、STM32、RP2040、树莓派——都可以通过同样的协议互相通信、组合、替换。** PAL 不绑硬件、不绑语言、不绑厂商，只绑"协议"。

---

## 0. 为什么是现在：CLI、嵌入式与 Python 的交汇

PAL 不是凭空产生的。它是三个趋势碰撞的结果。

### 0.1 CLI 工具给了 LLM 什么

2024 年之前，LLM 只能聊天。Claude 和 GPT 被困在对话框里——它们能推理，但不能执行。你能问"我的磁盘还剩多少空间"，但它不能跑 `df -h`。

**CLI 工具改变了这件事。** 当 Claude Code、Cursor、Codex CLI 等工具把 Shell 交给 LLM 时：

```
LLM 能做的事从"说话"变成了"做事":

  "检查磁盘"  →  df -h               → 结果直接返回
  "安装依赖"  →  pip install -r ...   → 包装好了
  "运行测试"  →  pytest -v            → 看到 pass/fail
  "部署服务"  →  docker compose up    → 服务起来了
```

CLI 本质上给了 LLM 一套**数字世界的操作原语**：
- 文件系统：读、写、删除、搜索
- 进程管理：启动、停止、查状态
- 网络：HTTP 请求、SSH、文件传输
- 包管理：安装、更新、卸载

**但 CLI 能操控的范围止步于操作系统。** `rm -rf` 能删掉代码仓库，但删不掉正在运行的产线。CLI 给了 LLM "数字手"，但没有给它"物理手"。

### 0.2 嵌入式给了 LLM 什么

嵌入式系统把 LLM 的操作空间从操作系统扩展到了**物理世界**：

```
CLI 能做的:                      嵌入式能做的:

  读文件 → 知道"配置写的是什么"       读 ADC → 知道"这个电机现在多少度"
  写文件 → 改变配置                   写 GPIO → 打开/关闭 220V 电源
  调 API → 操作云服务                 发 PWM → 控制风扇转速
  SSH    → 登录远程机器               读 I2C → 扫描挂载了多少个传感器
```

**CLI 让 LLM 有了"手"，嵌入式让 LLM 有了"感官"和"作用力"。** 这是质的飞跃——LLM 不再只是信息处理系统，它开始与物理世界形成闭环：

```
感知 → 推理 → 决策 → 执行 → 观察 → 再感知 → ...
 ↑                                              │
 └──────────── 物理世界反馈 ─────────────────────┘
```

但嵌入式也给 LLM 施加了数字世界没有的约束：
- **时间约束**：硬件看门狗 10s 超时，等不了 LLM 推理 5s
- **安全约束**：`rm -rf` 可以 git reset，GPIO 错了硬件烧了就是烧了
- **资源约束**：MCU 512KB SRAM，不是服务器 512GB

**PAL 就是为了同时抓住嵌入式的"能力扩展"和"约束收紧"而设计的。**

### 0.3 为什么是 Python

Python 成为 AI Agent 的首选语言不是偶然的，是三个因素叠加：

**1. LLM 训练数据中 Python 占比碾压**

| 语言 | GitHub 公开仓库占比 | LLM 代码生成质量 |
|---|---|---|
| **Python** | **~25%** | **高** |
| JavaScript | ~22% | 中高 |
| C | ~9% | 中 |
| Lua | <0.5% | **低** |

当 Claude 被要求写一段控制 GPIO 的代码，它在训练数据中见过几百万次 `machine.Pin()`、几千万次 `import`、上亿次 Python 异常处理。ESP-Claw 选 Lua 的代价就在这里——LLM 见过 Lua 代码的概率不到 Python 的 1/50。

**2. 胶水语言与 Agent 的"拼积木"模型天然匹配**

Python 的设计哲学是"胶水"——把 C 库粘在一起形成一个工作流。这恰好是 Agent 操作物理世界的正确模型：

```python
# Agent 不是在"写嵌入式固件"
# Agent 是在"把已有的积木粘在一起"

from machine import Pin, ADC, I2C         # 积木已经在盒子里了
                                          # (machine 模块, 十年验证)
temp = ADC(Pin(1)).read()                # 拿积木 A
relay = Pin(5, Pin.OUT)                  # 拿积木 B

if temp > 2000:                          # 判断 = 怎么拼
    relay.on()                           # 动手拼
```

Agent 不需要知道 `ADC` 寄存器怎么配、GPIO 时钟怎么开。那些是 C 层的事。Python 在这扮演的正是它在软件世界扮演了 30 年的角色：**胶水，把更快但更难写的东西粘在一起。**

**3. REPL = Agent 的原生接口**

Python 的 REPL 模型和 Agent 的交互模型是同构的：

```
REPL:                     Agent:
  >>> 输入代码              收到任务
  执行                      推理 → 生成代码
  输出结果                  发送到 REPL
  >>> 输入下一段             观察结果 → 调整策略
```

不需要定义 tool schema，不需要注册 callback，不需要穿 JSON。**REPL 就是世界上最简单的 IPC。** CLI 给了 LLM bash REPL，嵌入式给它 Python REPL——同样的交互模型，不同的操作对象。

---

## PAL 架构哲学

> **PAL 不是固件，不是库，不是操作系统。PAL 是一个抽象层——它用标准接口把"物理执行"从"决策逻辑"中彻底剥离，让任何芯片、任何语言、任何 Agent 都能通过同一套协议操控物理世界。**

### 核心断言

**物理执行是可以被抽象成"串口 JSON 服务器"的。**

- 决策层（大脑）只管发 `{"code":"Pin(5).on()"}`。
- 执行层（手）只管 `exec()` 这条字符串，返回 `{"stdout":"OK"}`。
- **大脑不需要知道 GPIO 寄存器长什么样，手不需要理解 Agent 为什么要做这个操作。**

### 四条铁律

**1. 大脑全知，手零自主。**
- 手不知道自己拥有"意志"，它只会被调用、被复位、被替换。
- 所有决策权集中在决策层（可以是 Core 0、树莓派、PC 或云端）。

**2. 协议是宪法，硬件是议员。**
- 串口（UART）、I2C、SPI、共享内存，都是可替换的物理层。
- 不变的只有 JSON 协议——它是决策与执行之间唯一的契约。
- **换硬件不改协议，换平台不改协议，换语言不改协议。**

**3. 传输层透明。**
- Level 1 用 USB 串口（PC ↔ ESP32）。
- Level 2 用虚拟串口（ESP32 Core 0 ↔ Core 1）。
- Level 3 用物理串口（树莓派 ↔ STM32）。
- **执行器的代码在三个 Level 中完全一致，只需更换"串口对象"。**

**4. 模块化 = 可替换性。**
- 决策层可以是 C、Python、Go、Rust 写的任何程序。
- 执行层可以是任何支持 MicroPython 的 MCU（ESP32、STM32、RP2040）。
- 只要两边都认 JSON on 串口，它们就能无缝协作。

### PAL 交互的本质：远程代码注入（RCI）

| 方向 | 内容 | 含义 |
| :--- | :--- | :--- |
| 大脑 → 手 | `{"id":"1","code":"Pin(5).toggle()"}` | "请执行这段代码" |
| 手 → 大脑 | `{"id":"1","stdout":"","error":false}` | "执行完了，结果如下" |

**这不是"远程过程调用（RPC）"，这是"远程代码注入（RCI）"。**
- RPC：你只能调用我预先提供的 10 个函数。
- PAL：你可以注入任何 Python 代码——只要 MicroPython 支持，手就能执行。

### 三组定位对比

| 对比 | PAL 的定位 |
| :--- | :--- |
| 与 FreeRTOS 比 | FreeRTOS 管"怎么跑"，PAL 管"跑什么、什么时候跑"。 |
| 与 MCP 比 | MCP 是 Agent 操控数字世界的协议，PAL 是 Agent 操控物理世界的协议。 |
| 与 ESP-Claw 比 | ESP-Claw 把 Agent 塞进 MCU，PAL 把 MCU 变成 Agent 的执行终端。 |

### 终极目标

> **让任何 Agent（云端或本地）都能通过同一套协议，操控任何支持 MicroPython 的 MCU。**
>
> Agent 只需要会发 JSON，不需要知道 GPIO、I2C、SPI、PWM 是什么。手只需要能跑 `exec()`，不需要知道 Agent 在云端还是本地、用 Python 还是 C++ 写。

**PAL 是"AI 与物理世界之间的通用翻译器"。**

---

## PAL 的范围：不是什么，是什么

### 不是什么

- ❌ **不是一种 I2C/SPI/UART 总线协议** — PAL 不定义总线层的行为。总线协议是 Layer 1 的事，由实时 MCU（如 PY32、STM32、AT32）独立处理。
- ❌ **不是一种热插拔标准** — 物理层的设备发现、地址分配、碰撞检测属于独立的硬件层技术，通过 PAL 的 Layer 1 接口接入，但不是 PAL 规范的一部分。
- ❌ **不是 Agent 框架** — PAL 不定义 Agent 怎么推理、怎么管理对话。AstrBot、LangChain、自研 Agent 框架都可以接入，PAL 只定义它们跟终端之间的 JSON 协议。
- ❌ **不是硬件参考设计** — PAL 不指定具体的 PCB、引脚分配、传感器型号。每个嵌入式系统的 PCB 不同，PAL 关心的是"Agent 怎么跟这些已经画好的外设交互"。

### 是什么

- ✅ **芯片无关的物理执行抽象层** — PAL 在标准外设接口（UART/I2C/SPI）和公认传输协议（JSON）之上，将"决策逻辑"与"硬件执行"彻底解耦。任何实现 PAL 协议的 MCU（ESP32、STM32、RP2040、树莓派）都是平等的 PAL 节点。
- ✅ **自带执行能力的终端** — PAL 终端**不仅能路由命令，还能直接执行 Python 操控硬件**。这是它跟一个纯串口透传模块的本质区别：Agent 不是"发指令给一个黑盒"，而是"直接在终端上跑 Python 读传感器、控 GPIO、扫 I2C"。
- ✅ **只绑协议，不绑硬件** — PAL 定义的是 JSON 协议格式和抽象架构，不绑定任何具体芯片、厂商、编程语言。任何 MCU 只要能跑 MicroPython REPL，就能成为 PAL 节点。

```
┌─────────────────────────────────────────┐
│       PAL 规范的范围                     │
│                                         │
│  Layer 3: PAL JSON 协议                 │
│  Layer 2: ESP32 Core 0/1 双核架构       │
│  Layer 1: PAL 不定义，由实时层独立处理    │
└─────────────────────────────────────────┘
```

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

### 为什么原语够用：Python 是胶水，硬件是积木

嵌入式系统的现实是：**PCB 已经画好了。** 引脚固定，外设固定，能操作的东西就那么几个。Agent 不需要"设计电路"——它只需要**把已有的外设组合成工作流**。

这恰好是 Python 的胶水语言特性在物理世界的映射：

```
软件世界:   Python = 胶水，把 C 库粘在一起
物理世界:   MicroPython = 胶水，把硬件模块粘在一起

Agent 做的事情:
  "读温度 → 如果 >30°C → 开风扇 → 发告警"
  
  这不是在写驱动，这是在拼积木。
  
  adc = ADC(Pin(1))          # 积木 1: 温度传感器
  relay = Pin(5, Pin.OUT)     # 积木 2: 风扇继电器
  
  temp = adc.read()           # 拿积木
  if temp > 2000:             # 判断
      relay.on()              # 拼积木
```

**AI 应该专注于做上层决策——什么时候读、读到什么值该行动、几个外设之间怎么协作。而不是关心 GPIO 寄存器怎么配、I2C 时序怎么调。** 前者是 Agent 擅长的（推理、规划、组合），后者是 `machine` 模块替你封装好的。

这就是为什么 PAL 不需要 ESP-Claw 的 Skill Registry——不是因为 Registry 不好，是因为**物理世界的"技能"就是 machine 模块的 6 个原语**。Agent 自己决定怎么拼，不需要你提前告诉它"这是 toggle_led 工具，这是 read_temp 工具"。Agent 看到 `Pin(5)` 就知道这是 LED，看到 `ADC(1)` 就知道这是温度传感器。它缺的不是工具描述，是一份引脚定义表。

**PAL 只提供一份引脚定义表（board.py），Agent 自己写胶水代码。**

### 开发板 vs 工程项目：两种 Agent 操作模式

PAL 的一个关键设计是**预注册是可选的，不是强制的**。这取决于使用场景，而两种模式都是合法的 PAL：

| | 开发板 / 实验模式 | 工程 / 生产模式 |
|---|---|---|
| **场景** | 个人开发者在面包板上接传感器，今天接 LED 明天换继电器 | PCB 已经量产，引脚和外设全部固定，不能出错 |
| **board.py** | 开发者临时写的，Agent 也可以改 | 部署前写好，Agent 只能调用不能修改 |
| **Agent 的操作权限** | `machine.Pin` 全部可用，自由探索 | 只能调用 `board.py` 暴露的安全函数 |
| **安全边界** | 人的判断（开发者盯着串口） | Core 0 引脚所有权表硬隔离 |
| **工具注册** | 无——Agent 当场 import machine | 无——Agent 调 board.py 函数，函数背后是 machine |
| **灵活性** | 极高，Agent 可以写任意 Python | 受控，Agent 只能在安全边界内组合 |
| **风险** | 写错代码 LED 不亮，改一行重跑 | 写错代码 Python 抛异常，Core 0 拒绝危险操作 |
| **对应的 PAL Level** | Level 1 | Level 2+ |

**关键：这两种模式都不需要"预注册工具"。**

ESP-Claw 需要你为每个 GPIO 写 C 结构体注册成 Lua 工具——无论开发板还是产线，这个步骤逃不掉。PAL 没有这个步骤。在开发板模式，Agent 直接 `machine.Pin(5, Pin.OUT)`。在工程模式，Agent 调 `board.toggle_led()`——但 `toggle_led` 本身是一个 Python 函数，不是 C 结构体注册的。**函数是 Python 的，Agent 可以读它的源码、理解它的行为——但它不能修改它（Core 0 保护）。**

**不是什么情况下都要给 Agent 自由，而是根据场景选择 Agent 的权限级别。** PAL 的架构支持一个统一的方式实现两种模式：始终通过 MicroPython REPL，权限差异由 board.py 的封装程度和 Core 0 的引脚所有权表决定。

### 原则 5：传输层无关

Agent ↔ 终端之间的传输层是可替换的：

| 传输层 | 适用场景 | 默认 |
|---|---|---|
| **WebSocket** | WiFi 局域网 | ✅ PAL Level 2+ 默认 |
| UART | 有线串口 | 调试/降级 |
| BLE | 低功耗无线 | 移动设备 |
| MQTT | 广域网 | 远程控制 |

---

## 2. 架构（Level 2）

> **PAL Level 2 的整个架构建立在"大脑全知，手零自主"的核心理念之上。**

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
│  │  传感器节点  ·  继电器模块  ·  电机驱动  ·  LED    │ │
│  │  显示屏  ·  编码器  ·  任意 I2C/SPI 外设  ·  ...   │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Core 0 — 大脑：四大组件

**Task Registry（任务注册器）**：Agent 下发任务的入口。校验 brief → 资源冲突检测 → 锁定资源 → 持久化（NVS）→ 唤醒 Task Manager。

**Task Manager（任务管理器）**：PAL 调度器的引擎。数组式任务表（O(n) 全表扫描，n ≤ 20），RTC 绝对时间驱动，相位锁定调度。

**Task Registry 工作流**：

```
Agent 下发 JSON {"brief": {...}, "code": "..."}
        │
        ▼
  ① 解析 brief（任务名/资源需求/周期/超时/存储类型）
        │
        ▼
  ② 资源冲突检测 → 冲突则返回详情给 Agent
        │
        ▼
  ③ 生成唯一 task_id，状态=PENDING，计算首次触发 = now + interval
        │
        ▼
  ④ 持久化：volatile → RAM；persistent → NVS Flash + RAM
        │
        ▼
  ⑤ 唤醒 Task Manager（xTaskNotifyGive）
        │
        ▼
  返回 Agent {"task_id": "001", "status": "registered"}
```

**Task Manager 数据结构**：

```c
#define MAX_PAL_TASKS 20

typedef struct {
    char     task_id[16];          // Agent 查询/取消
    uint64_t next_trigger_abs;     // RTC 绝对时间（μs）
    uint32_t interval_us;          // 周期（0 = 一次性）
    uint32_t code_ptr;             // code 字符串指针
    uint32_t pins_mask;            // 引脚占用位图
    uint8_t  state;                // 0=空闲 1=启用 2=执行中
    uint32_t timeout_ms;           // 执行超时
    uint8_t  storage_type;         // volatile / persistent
} pal_task_t;

pal_task_t g_task_table[MAX_PAL_TASKS];  // 全局任务表（RAM + NVS）
```

**WebSocket Server**：Agent ↔ Core 0 唯一通信通道。JSON 解析 + 指令路由（register / cancel / status / result）。

**Hardware Watchdog**：Core 1 超时监护 + 硬复位兜底。卡死 → 不等、不诊断——直接硬件复位，恢复干净状态。

### 2.3 Core 1 — 手：单任务执行器

```
┌───────────────────────────────────────────┐
│  Executor:                                │
│  1. 阻塞读虚拟串口                          │
│  2. 收到 JSON → exec(code)                │
│  3. 返回 {"stdout": ..., "error": ...}    │
│  4. 回到步骤 1                              │
│                                            │
│  一次只执行一段代码。                         │
│  无自主循环，无 uasyncio。                   │
│  阻塞在串口读上，什么都不做——直到下一次被调用。  │
└───────────────────────────────────────────┘
```

### 2.4 虚拟串口：Level 1 → Level 2 零改动迁移

```
Level 1:  PC ──USB UART──→ ESP32 MicroPython (pal_main.py)
Level 2:  Core 0 ──FreeRTOS 流缓冲──→ Core 1 MicroPython (pal_main.py)

执行器只认 read()/write()，不关心底层是物理串口还是共享内存。
Level 1 验证通过的代码，Level 2 无需修改任何 Python 逻辑。
```

### 2.5 相位锁定调度

```
❌ 错误做法：next = now + interval
   → 200ms 任务漂移：0, 205, 410, 615……

✅ PAL 做法：next = next + interval
   → 200ms 任务永远：0, 200, 400, 600……
```

即使某次执行耗时 50ms，下次触发依然基于原计划时刻累加。高频任务不会因单次延迟而整体偏移。**长定时**（> 60s）由 RTC 独立硬件闹钟驱动，断电仍走时。系统重启后从 NVS 恢复任务表，RTC 补偿错过的任务。

### 2.6 PAL 调度器 vs FreeRTOS 调度器

| 维度 | FreeRTOS 调度器 | PAL Level 2 调度器 |
| :--- | :--- | :--- |
| 核心哲学 | 任务自治 | **大脑全知** |
| 任务定义 | C 函数（编译时固定） | Python 字符串（运行时 Agent 下发） |
| 任务表 | RAM 链表（断电即失） | NVS（Flash）+ RAM 缓存 |
| 时间基准 | 相对 Tick（上电归零） | RTC 绝对时间（64 位） |
| 动态注册 | ❌ | ✅ |
| 外部查询 | ❌ | ✅ |
| 调度触发 | SysTick 自动 | 事件驱动 + 阻塞等待 |
| 数据结构 | 有序链表（插入 O(n)） | 无序数组（全表扫描 O(n)，n≤20） |
| 断电恢复 | 任务丢失 | 从 NVS 恢复 + RTC 补偿 |

> **FreeRTOS 是地基，PAL 任务管理器是在地基上建造的面向 AI Agent 的专用调度大楼。FreeRTOS 管"怎么跑"，PAL 管"跑什么、什么时候跑"。它们不是竞争对手。**

### 2.7 组件清单

PAL Level 2 由 **8 个核心组件** 组成，分为大脑侧（Core 0）和手侧（Core 1），通过虚拟串口通信。

#### Core 0（大脑，C / FreeRTOS）— 6 组件

| 组件 | 核心职责 | 关键输入 | 关键输出 |
| :--- | :--- | :--- | :--- |
| **Task Registry** | 注册任务、校验资源、持久化 | Agent JSON（brief + code） | `task_id`、NVS 写入 |
| **Task Manager** | 调度执行、状态管理、相位锁定 | 任务表、RTC 时间 | 下发 code 到 Core 1、状态缓存 |
| **WebSocket Server** | 与 Agent 双向通信 | Agent JSON 指令 | 状态 JSON 响应、事件推送 |
| **Hardware Watchdog** | Core 1 超时监护、硬复位 | Core 1 心跳超时 | `esp_restart()`、事件推送 |
| **RTC Scheduler** | 长定时触发（>60s）、断电恢复 | 任务表、RTC 中断 | 唤醒 Core 0、补偿执行 |
| **NVS Storage** | 任务持久化存储 | 任务结构体 | Flash 读写 |

#### Core 1（手，MicroPython）— 1 组件

| 组件 | 核心职责 | 关键输入 | 关键输出 |
| :--- | :--- | :--- | :--- |
| **Executor** | 阻塞读 → exec(code) → 返回 JSON | 虚拟串口 JSON | `{"stdout":"...","error":false}` |

#### 通信抽象层

| 组件 | 核心职责 |
| :--- | :--- |
| **Virtual UART** | FreeRTOS 流缓冲，Core 0 ↔ Core 1 事件驱动通信。Level 1 代码只需替换串口对象，其余零改动 |

### 2.8 组件交互图

```
┌─────────────────────────────────────────────────────────────────────┐
│                     云端 Agent（WebSocket）                        │
└────────────┬────────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────────┐
│                         Core 0（大脑）                             │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐  │
│  │   WebSocket  │───→│    Task      │───→│      Task          │  │
│  │   Server     │←───│   Registry   │    │     Manager        │  │
│  └──────────────┘    └──────────────┘    └─────────┬──────────┘  │
│         │                                          │              │
│         │                                  ┌───────▼───────┐      │
│         │                                  │     RTC       │      │
│         │                                  │  Scheduler    │      │
│         │                                  └───────────────┘      │
│         │                                          │              │
│         │                                  ┌───────▼───────┐      │
│         │                                  │   Hardware    │      │
│         │                                  │   Watchdog    │      │
│         │                                  └───────────────┘      │
│         │                                          │              │
│         │                                  ┌───────▼───────┐      │
│         │                                  │     NVS       │      │
│         │                                  │   Storage     │      │
│         │                                  └───────────────┘      │
│         │                                          │              │
└─────────┼──────────────────────────────────────────┼──────────────┘
          │                                          │
          │          虚拟串口（FreeRTOS 流缓冲）       │
          │                                          │
┌─────────▼──────────────────────────────────────────▼──────────────┐
│                         Core 1（手）                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                     Executor                               │  │
│  │  阻塞读虚拟串口 → 解析 JSON → exec(code) → 返回 JSON      │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
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
  │  "stdout":"['0x48','0x76']",      │
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

## 4. 安全模型

PAL 的安全模型不是"附加的"——它是架构中的基础组件。本节定义 PAL 面临的威胁、防御层级、以及 PAL 能保护什么、不能保护什么。

### 4.1 威胁模型

PAL 识别以下威胁：

| 威胁 | 来源 | 后果 | PAL 的响应 |
|---|---|---|---|
| **Agent 生成恶意/错误代码** | LLM 幻觉、prompt injection、被污染的模型 | GPIO 错误翻转、继电器误动作 | 引脚所有权表硬隔离 + Core 0 拒绝 |
| **Agent 代码死循环** | LLM 生成 `while True:` 无退出条件 | Core 1 CPU 100%，系统无响应 | 执行超时 (30s) + Core 0 心跳监控 |
| **Agent 尝试操作系统资源** | LLM 推理出"需要改 WiFi 密码"或"关闭看门狗" | 网络断连、安全机制失效 | Core 0 锁定网络/WDT 所有权 |
| **Core 1 Python VM 崩溃** | 内存耗尽、未处理异常、C 扩展 bug | Agent 失去对终端的控制 | Core 0 独立运行，自动重启 Core 1 VM |
| **WiFi 断连** | 信号干扰、路由器重启 | Agent 命令无法到达终端 | Core 0 自动重连 + 终端本地降级模式 |
| **物理攻击（硬件访问）** | 攻击者获得 PCB 物理接触 | 固件篡改、引脚短接 | PAL 不防物理攻击（见 4.4） |

### 4.2 五层防御架构

```
┌──────────────────────────────────────────────────────────┐
│ Layer 5: 云端审计                                        │
│ ─────────────────────────────────────────────────────── │
│ · 所有 Agent → 终端指令在云端 JSON 流中可见                 │
│ · 异常行为可被操作者实时识别并切断 WebSocket                 │
│ · 完整的 audit log，事后可追溯                             │
│ 防御: 人的判断 + 云端监控                                  │
├──────────────────────────────────────────────────────────┤
│ Layer 4: Core 1 执行沙箱                                  │
│ ─────────────────────────────────────────────────────── │
│ · 每条 Python 代码最长执行 30s（超时强制终止）              │
│ · 输出 >4KB 自动截断（防止内存耗尽）                        │
│ · Python 异常不会传播到 Core 0（独立 VM）                   │
│ 防御: 超时 + 资源限制                                      │
├──────────────────────────────────────────────────────────┤
│ Layer 3: 引脚所有权管理                                    │
│ ─────────────────────────────────────────────────────── │
│ · OWNER_SYSTEM: MicroPython 无权操作（SPI MOSI/SCK, WDT） │
│ · OWNER_AGENT:  暴露给 Agent（用户 GPIO, 用户 I2C）        │
│ · 违反所有权 → machine.Pin() 返回 OSError                 │
│ 防御: 硬件层拒绝                                           │
├──────────────────────────────────────────────────────────┤
│ Layer 2: Core 0 系统监护                                   │
│ ─────────────────────────────────────────────────────── │
│ · 监控 Core 1 MicroPython VM 心跳                          │
│ · 心跳超时 → 自动重启 Core 1 VM（不影响 Core 0 运行）      │
│ · 硬件 WDT (10s) → 全系统复位（兜底）                       │
│ 防御: 独立于 MicroPython VM 的硬实时监护                    │
├──────────────────────────────────────────────────────────┤
│ Layer 1: Layer 1 实时 MCU 物理隔离                         │
│ ─────────────────────────────────────────────────────── │
│ · 独立的实时 MCU 处理所有安全关键操作                        │
│ · 不接收来自上层的命令修改                                  │
│ · 物理隔离: AI 指令经过三层翻译才能到达硬件寄存器             │
│ 防御: 物理不连接                                            │
└──────────────────────────────────────────────────────────┘
```

**每一层都是审计点和拦截点。** Agent 的命令从云端到硬件必须穿过这五层。任意一层检测到异常都可以拒绝执行。这不是"安全建议"——是架构强制。

### 4.3 故障模式与恢复

| 故障 | Core 0 状态 | Core 1 状态 | 系统行为 | 恢复时间 |
|---|---|---|---|---|
| Agent 代码抛异常 | 正常运行 | 异常被捕获，返回 stderr | JSON 返回 `"error": true` | 即时 |
| Agent 代码超时 (30s) | 正常运行 | 执行被强制终止 | JSON 返回超时错误 | 30s 超时后 |
| Core 1 Python VM 崩溃 | 正常运行 | VM 停止响应 | Core 0 检测到心跳超时 → 重启 Core 1 | ~1-3s |
| Core 1 无限循环 + 禁用超时 | 正常运行 | CPU 100% | Core 0 心跳超时 → 重启 Core 1 | ~2-5s |
| WiFi 断连 | 正常运行 | 命令队列积压 | Core 0 自动重连；恢复后清空积压队列 | ~5-30s |
| 全系统死锁 | 硬件 WDT 超时 | — | 硬件复位 → 重新初始化 → 重连 Agent | ~5-10s |

**关键设计：任何故障都不会导致 Core 0 和 Layer 1 实时 MCU 停止运行。** 物理控制链路永不中断。

### 4.4 PAL 不能保护什么

诚实声明 PAL 安全模型的能力边界：

| 攻击向量 | PAL 能否防护 | 说明 |
|---|---|---|
| LLM 本身的幻觉/错误 | ⚠️ 部分 | PAL 不能修复 LLM 的推理错误，但可以限制错误的爆炸半径（引脚隔离 + 超时） |
| Prompt injection / jailbreak | ⚠️ 部分 | 同上——受污染的指令仍然不能操作系统引脚 |
| 恶意 WebSocket 客户端 | ❌ 不能 | PAL 终端默认信任 WebSocket 来源。生产环境应通过 VPN/局域网隔离 + Token 认证（Future Work） |
| 固件篡改（OTA 劫持） | ❌ 不能 | 如果攻击者能推送恶意固件，PAL 的所有安全假设失效。OTA 签名验证需独立实现 |
| 物理攻击（JTAG/串口/引脚短接） | ❌ 不能 | 攻击者获得 PCB 物理接触 = 所有软件安全边界被绕过 |
| Core 0 C 代码 bug | ❌ 不能 | Core 0 代码中的内存越界、栈溢出等 C 级 bug 可能导致全系统崩溃。必须通过代码审查和测试保证 |

**PAL 的安全边界是：一个行为正常的 LLM 生成的错误代码，不能造成物理损害。** PAL 不防御对 LLM 本身的攻击（prompt injection），也不防御对硬件的物理攻击。

### 4.5 安全模型的适用前提

PAL 的安全模型基于以下假设，违反任意一条可能导致安全边界失效：

1. Core 0 C 代码经过充分审查，不包含内存安全漏洞
2. 引脚所有权表正确配置，`OWNER_SYSTEM` 和 `OWNER_AGENT` 的划分符合硬件设计
3. Layer 1 实时 MCU 独立运行，不接收来自上层的运行时修改
4. 物理 PCB 不被攻击者接触
5. 固件烧录过程安全（无中间人篡改）

---

## 5. 兼容性等级

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

认证要求:
  ✅ 能通过 UART REPL 接收并执行 Python 代码
  ✅ 支持 machine 模块的 6 类硬件原语
  ✅ 执行结果（stdout/stderr/error）可回传
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

认证要求:
  ✅ 双核物理分离，Core 0 代码不可通过 REPL 修改
  ✅ 引脚所有权表正确划分 OWNER_SYSTEM 和 OWNER_AGENT
  ✅ 系统引脚被 Agent 访问时返回 OSError
  ✅ Core 1 崩溃后 Core 0 自动重启 Core 1
  ✅ WebSocket 断线后 Core 0 自动重连
  ✅ 硬件 WDT 在 Core 0 失效后触发全系统复位
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

认证要求:
  ✅ 双 MCU 物理独立，互相看门狗监控
  ✅ 安全 MCU 独立于 Agent 指令链路
  ✅ 冗余通信链路（至少两条物理通道）
  ✅ 工业温度范围 (-40~85°C) 实测通过
  ✅ 安全停机回路在通信中断时自动触发
  ✅ 所有 Layer 1 操作经由安全 MCU 仲裁
```

---

## 6. 与已有方案对比

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

## 6.1 PAL 与 MCP：物理世界的最后一段

[MCP (Model Context Protocol)](https://modelcontextprotocol.io) 是 Anthropic 提出的 AI-to-Tool 通信标准。它定义了 LLM 如何发现工具、调用工具、获取结果。PAL 与 MCP 不是竞争关系——它们是**互补的不同层次**。

### MCP 解决什么，PAL 解决什么

```
┌──────────────────────────────────────────────────────┐
│  MCP 的范围:                                         │
│  ┌────────────────────────────────────────────────┐ │
│  │  LLM  ←──→  MCP Server  ←──→  Digital Tools    │ │
│  │                    (API/DB/File...)             │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  MCP 到 PAL 的映射:                                   │
│  ┌────────────────────────────────────────────────┐ │
│  │  LLM  ←──→  MCP Server  ←──→  PAL Client       │ │
│  │                                    │            │ │
│  │                              WebSocket JSON     │ │
│  │                                    │            │ │
│  │                              ┌────▼──────────┐ │ │
│  │                              │  PAL 终端      │ │ │
│  │                              │  (物理世界)     │ │ │
│  │                              └───────────────┘ │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

| 维度 | MCP | PAL |
|---|---|---|
| **解决什么问题** | LLM 如何**发现和调用**工具 | Agent 如何**安全执行**物理操作 |
| **协议层** | 工具描述 + 调用 + 结果返回 | Python 代码执行 + 安全边界 + 事件推送 |
| **操作对象** | 数字工具（API、数据库、文件） | **物理硬件**（GPIO、ADC、I2C、PWM） |
| **安全模型** | 工具权限声明 | **五层硬件隔离**（Core 0 锁死 + 引脚所有权 + 超时 + 心跳监控 + 云端沙箱） |
| **延迟** | API 调用延迟 (~100ms-5s) | 硬件执行延迟 (~μs-ms) + AI 推理延迟 (云端) |
| **失败后果** | API 返回错误，可重试 | **继电器误动作、设备损坏、安全隐患** |

### MCP + PAL：一条完整的链路

理想情况下，Agent 通过 MCP 发现 PAL 终端的工具，通过 PAL 协议执行物理操作：

```
LLM (Claude)                          
  │ MCP: tool_call("read_sensor", {pin: 1})  ← Agent 通过 MCP 发现工具
  ▼                                          
MCP Server (AstrBot)                  
  │ PAL JSON: {"type":"exec","code":"ADC(Pin(1)).read()"}  ← MCP Server 翻译为 PAL 协议
  ▼                                          
PAL 终端 (ESP32-S3)                   
  │ machine.ADC(Pin(1)).read()               ← Core 1 执行
  ▼                                          
物理世界: 传感器电压值 = 2048                 ← 真实物理量返回
```

**MCP 负责"Agent 知道有什么工具可用"，PAL 负责"工具被安全地在物理世界执行"。** MCP 到不了硬件，PAL 不定义工具发现——两者合在一起，才是 AI 操控物理世界的完整链路。

### PAL 为什么不是 "MCP for Hardware"

有人可能会问：为什么不直接给硬件设备实现一个 MCP Server？

答案：**因为 MCP 没有物理安全模型。** MCP 的权限模型是"声明性"的——工具声明自己能做什么，LLM 决定要不要调。这在数字世界足够（最坏结果是 API 返回 500）。但在物理世界，你需要的是"强制性"的安全边界——不是"建议 Agent 不要操作系统引脚"，而是"Agent 在硬件层面就碰不到系统引脚"。这就是 PAL Core 0 的引脚所有权表和五层防护。

**PAL 的 JSON 协议可以包装为 MCP 工具（通过一个 MCP Server 作为中间层），但 PAL 的安全模型必须独立于 MCP 存在。** MCP 是 Agent 的工具目录，PAL 是物理世界的闸门。

## 7. 参考实现

本规范附带一个 PAL Level 2 参考实现（目录 `impl/`），基于 ESP32-S3 + 低成本 ARM MCU：

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
| PAL Level 1 硬件验证 | ✅ ESP32-S3 (2026-06-28) |
| Core 0 C 框架 | 🚧 开发中 |
| Core 1 MicroPython | 🚧 开发中 |
| Agent 客户端库 | 📝 设计中 |
| SSD1306 OLED 驱动 | ✅ I2C 128×64 |
| W25Q64 8MB Flash | ✅ SPI 读写验证 |
| Bad Apple 25fps 播放 | ✅ 5478 帧 W25Q64→OLED |
| PAL 协议自愈闭环 | ✅ Claude→ESP32→错误→修复→验证 (14min) |

**演示视频**：[`demo-videos/`](demo-videos/) — 双 LED 异步闪烁、OLED 显示、Bad Apple 完整播放。

**踩坑记录**：[`badapple/LESSONS.md`](badapple/LESSONS.md) — 视频打包方向 ×3、USB 上拉、WiFi 全角字符、W25Q64 旧数据等 8 个坑。

---

## 8. 设计动机：为什么不是 ESP-Claw

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
传感器轮询周期:   ~10ms（错过一轮 = 数据滞后）
LLM API 延迟:   ~500ms-5s（取决于模型和网络）
Agent 多轮推理:  ~2-30s（取决于任务复杂度）
```

如果 Agent 循环正在等 LLM 返回（5 秒），而这时实时 MCU 通过 SPI 发来一帧"温度传感器 3 超阈值"，**谁来处理这帧数据？**

Agent-on-Device 的答案是"分优先级"——让 I/O 任务优先级比 Agent 循环高。这确实能让 SPI 中断抢到 CPU，但 Agent 的上下文状态在这些打断中可能变得不一致。更严重的是，**Agent 自己也要发起实时操作**——它推理出"需要关闭继电器 5"，发 SPI 命令。如果这个推理花了 3 秒，继电器延迟动作 3 秒——在工业场景中，3 秒可以造成设备损坏。

**PAL 的立场：** 实时任务（传感器轮询、SPI 帧处理、WDT、状态表更新）全部在 Layer 1 实时 MCU 上独立运行，与 Agent 完全异步。PAL 终端只做最上层的决策翻译——Agent 在云端推理出"开风扇"，终端收到 JSON 后 <1ms 内转发。AI 的慢和物理的快之间，有一道明确的墙。

### 总结

```
               Agent-on-Device              PAL
               ────────────────             ───
资源:           Agent 吃掉一半 MCU 资源        Agent 不占终端资源
稳定性:         一个 API 超时可能拖死板子      云端负责容错，终端只管执行
实时性:         推理延迟 vs 传感器轮询 矛盾     实时任务在 Layer 1 上完全独立
职责边界:       MCU 既是大脑又是手             终端是手，大脑在云上
调试:           抓日志看 ReAct trace          逻辑分析仪 + WebSocket JSON
```

**Agent-on-Device 让嵌入式终端背负了不该它承担的复杂度。PAL 把 Agent 留在云端，终端只做一件事：收到命令，执行，回报结果。**

### 为什么云端是正确答案

PAL 选择 Agent-in-Cloud 不是技术偏好的问题，是四个不可替代的优势：

**1. 脑与手脚分离。**

物理终端的职责是执行——读传感器、控 GPIO、发 PWM。Agent 的职责是思考——分析数据、规划流程、组合技能。这两种计算在性质上完全不同：前者需要确定性、低延迟、长期稳定；后者需要弹性算力、大内存、频繁迭代。把两者放在同一块 MCU 上就是在逼一个芯片做两种互相矛盾的事。分离之后，各自用最适合自己的硬件。

**2. 一个脑子可以管多个手脚。**

```
              ┌──────────┐
              │  Agent   │  ← 一个云端大脑
              └────┬─────┘
         ┌─────────┼──────────┐
    ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
    │PAL 终端│ │PAL 终端│ │PAL 终端│  ← 多个物理手脚
    │(产线 A) │ │(仓库 B) │ │(实验室)│
    └────────┘ └────────┘ └────────┘
```

云端 Agent 可以同时管理多个 PAL 终端——一个工厂里几十个分布式控制节点，共用一套推理引擎。Agent-on-Device 每个节点都要独立部署一个 Agent 实例，节点之间没有全局视角。

**3. 你可以随时操控脑子。发生异常，随时终止。**

云端 Agent 出问题——推理错误、行为异常、被污染——操作者可以立即切断、重启、换模型。回到安全的默认状态只需要一条命令。

Agent-on-Device 出问题时，**你无法随时终止一个正在运行的 MCU 上的 Agent 循环**——它可能正在等 LLM API 超时，可能卡在 WiFi 断连重试，可能正在生成下一段代码。唯一的恢复手段是硬件看门狗复位。开发和调试时你被迫在物理设备上抓 ReAct trace；PAL 的 trace 全部在云端 JSON 流里可见。

**4. Skills、MCP、工具生态运行在稳定的云基础设施上。**

Agent-on-Device 把 Skills、工具注册表、MCP 客户端全部跑在 MCU 上——受限于 8MB PSRAM、受限于 FreeRTOS 线程安全、受限于 SPIFFS 文件系统的碎片化。云端 Agent 可以跑完整的 Hermes Skills 体系、MCP 工具链、向量数据库、SQLite 持久化——所有成熟的 AI 基础设施，不需要为 MCU 做任何裁减。

**一句话：PAL 不是"把 Agent 从终端赶走了"，是"把它放到了最适合它的地方"。**

---

## 9. Agent-on-Device 的硬件门槛、适用与不适用场景

以上批判并非否定 Agent-on-Device，而是界定其**适用边界**。以下是基于资源约束和工程边界的诚实分析。

### 9.1 硬件门槛

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

### 9.2 适用场景（Agent-on-Device 的合理选择）

> **⚠️ 注意："离线"不等于"Agent-on-Device 可以跑。**
> ESP32 级 MCU **不可能**在本地运行 LLM——最小的可用模型（Gemma 2B 4-bit 量化）需要 ~1.5GB RAM，而 ESP32-S3 最多 8MB PSRAM。所有现有 Agent-on-Device 框架（ESP-Claw、mimiclaw、pycoClaw）**仍然需要 WiFi 调用云端 API**。真正离线 AI 的唯一途径是 Linux 单板机（树莓派 4B/8GB）+ 本地部署小模型——性能远不如云端，且不属于嵌入式 MCU 范畴。

| 场景 | 为什么 Agent-on-Device 合适 |
|---|---|
| **数据必须留在本地** | 医疗设备、军事通信、敏感工业数据——数据不允许离开局域网。Agent 在本地完成推理，API 调 LLM 但不存储上下文于云端。 |
| **单功能消费设备** | 智能音箱、桌面机器人——单一功能 + 固定交互模式，Agent 推理任务简单且可预期。没有多节点协调的复杂度。 |
| **低延迟交互** | 语音助手、表情机器人——不需要微秒级响应，但绕开公网延迟。局域网内的 LLM API 调用可以在 100-500ms 内完成。 |
| **原型/教育/研究** | 用一块 ESP32-S3 快速搭建概念验证，证明"AI 可以控制硬件"。成本 $5-10 即可开始。 |

### 9.3 不适用场景（应该选 PAL 或裸机方案）

| 场景 | 为什么 Agent-on-Device 不合适 |
|---|---|
| **多节点协调系统** | 传感器集群、产线设备网络——一个 Agent 要管理几十个物理节点。Agent 在本地 = 只有一个大脑管理所有节点，单点故障。云端 Agent 可以全局视角。 |
| **硬实时工业控制** | 电机驱动、电源管理、安全停机——传感器轮询周期 10ms，Agent 多轮推理 2-30s。实时任务必须与 Agent 完全异步。 |
| **成本敏感场景（$2-3 决定生死）** | 智能农业传感器、一次性物流标签——每个节点加 $5 PSRAM = 成本翻倍。PY32（$1）+ 裸机 C 才是正解。 |
| **长期连续运行（24/7）** | 产线、仓库、基站的设备监控——Agent 循环的内存泄漏、LLM API 波动、WiFi 断连累积，最终导致 WDT 复位。工业场景不接受"平均每周复位一次"。 |
| **需要云端最强模型** | 复杂视觉理解、多模态推理——端侧小模型（Gemma、Phi）远不如 Claude/GPT。如果业务本身需要大模型，Agent 留在云端是唯一选择。 |
| **频繁更新业务逻辑** | 产线流程变更、仓库 SKU 重组——如果 Agent 在终端，改工具逻辑要 OTA 固件。PAL 改一行 Python 重启 Core 1 即可。 |

### 9.4 决策矩阵

```
                    有稳定网络（WiFi / 以太网）？
                   /          \
                 是            否
                 │             │
                 │             └──→ 需要 AI？
                 │                  /      \
                 │                否        是
                 │                │         │
                 │                ▼         ▼
                 │          ┌─────────┐  ┌──────────┐
                 │          │裸机 C    │  │Linux 单板机│
                 │          │(无 AI)   │  │+ 本地小模型│
                 │          └─────────┘  │(≠ MCU)    │
                 │                       └──────────┘
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

**PAL 的适用区是"有网络 + 无硬实时 + 需要多节点协调或频繁变更逻辑"。Agent-on-Device 的适用区是"有网络 + 单设备 + 无实时冲突"。两者不是竞争关系——是互补的。真正离线 ≠ Agent-on-Device on MCU；真正离线 AI 需要 Linux 单板机 + 本地模型部署，属于另一类硬件。**

---

## 10. 自进化 vs 预蒸馏：嵌入式场景的可靠性边界

### 10.1 物理世界的容错率是零

Hermes Agent 的"自进化"机制——Agent 完成任务后反思、提炼 SKILL.md、下次复用——在数字世界里非常优雅。一个 API 调用失败，重试 3 次；一个脚本写错了，改完再跑。**失败了没有物理后果。**

但在嵌入式系统中，一个错误的 GPIO 操作意味着：

```
# Agent 推理错误: "把 0x20 的 LED 翻转"
# 实际执行:
relay = Pin(5, Pin.OUT)
relay.on()    # ← 这是控制 220V 电源的继电器，不是 LED
```

**物理世界的试错成本是不可逆的。** 你不能让 Agent 在产线上"慢慢学"——它必须在第一次操作前就是对的。

### 10.2 个人开发者 vs 工程级的可靠性模型

Hermes 的自进化模型解决的是"个人开发者的效率问题"——Agent 帮你记住你过去的偏好、项目规范、常用工作流。它本质上是**经验的自动化积累**。这在以下场景中非常有效：

- 个人开发者长期使用同一台机器的环境
- 代码编写、文件管理、API 调用等**可逆操作**
- "上次你怎么配置这个项目的"——省去重复沟通

但在工程级的嵌入式场景中，可靠性模型是相反的：

| | 自进化模型 (Hermes) | 预蒸馏模型 (工程级 PAL) |
|---|---|---|
| **知识来源** | Agent 从自己的经验中**事后**提炼 | 开发者**事前**喂入经过验证的代码 |
| **可靠性保证** | "上次成功了，这次也应该成功" | "这段代码在产线上跑了 3000 小时没出过错" |
| **适合场景** | 个人开发者，快速迭代 | 产线、仓库、基站，**不能犯错** |
| **Agent 的角色** | 学习者和执行者 | **纯执行者**（决策在云端，终端只执行已验证的指令） |
| **出错后果** | 改一行代码，再跑一次 | **物理损伤、物料损失、产线停机** |

### 10.3 PAL 的答案：预蒸馏 + 自进化的混合模型

PAL 不选边。Core 0 和 Core 1 的分界线恰好是预蒸馏和自进化的分界线：

**预蒸馏（Pre-Distilled）— Core 0 的地盘：**

这里的代码**永不变**。烧录后锁死，OTA 更新需物理确认：

```python
# board.py — 预蒸馏的硬件抽象层
# 这段代码是开发者在部署前写好的。
# Agent 可以调用 toggle_led()，但不能修改它的实现。
# Agent 不知道背后是 GPIO 5、也不知道 high 是开还是关。

from machine import Pin, ADC, I2C

LED_STATUS = Pin(5, Pin.OUT)
RELAY_POWER = Pin(12, Pin.OUT)
TEMP_SENSOR = ADC(Pin(1))
I2C_BUS = I2C(0, freq=100000)

def toggle_led():
    """翻转状态指示灯。Agent 只能调用，不能修改。"""
    LED_STATUS.value(not LED_STATUS.value())

def read_temperature():
    """返回温度值。校准曲线已在部署前验证。"""
    raw = TEMP_SENSOR.read()
    return raw * 3.3 / 4095 * 100  # 已验证的转换公式

def power_off():
    """安全断电。Agent 只能调用，不能绕过。"""
    RELAY_POWER.off()
```

预蒸馏的内容：
- ✅ 引脚定义（`Pin(5, Pin.OUT)`）
- ✅ 外设驱动（`I2C(0, freq=100000)`）
- ✅ 安全函数（`power_off()` — 部署前经过硬件测试）
- ✅ 转换公式（`raw * 3.3 / 4095 * 100` — 校准曲线在产线上验证）

**自进化（Self-Evolving）— Core 1 的地盘：**

Agent 在云端推理，生成 Python 代码，通过 PAL JSON 协议发到 Core 1 执行：

```python
# Agent 当场写的代码（通过 WebSocket JSON 到达 Core 1）
# 这段代码昨天不存在，今天 Agent 因为用户的需求而当场生成。

temp = read_temperature()          # 调用预蒸馏的积木
if temp > 60:
    power_off()                    # 调用预蒸馏的积木
    event_push("overtemp_shutdown")
elif temp > 45:
    toggle_led()                   # 调用预蒸馏的积木
    event_push("temp_warning", {"temp": temp})
```

Agent 自进化的内容：
- ✅ 判断逻辑（`if temp > 60` — 阈值是 Agent 根据今天的数据调的）
- ✅ 工作流编排（"读温度 → 判断 → 关电源 / 闪灯"）
- ✅ 事件策略（什么情况下推送、推送什么内容）

Agent 不能碰的内容（预蒸馏层拒绝）：
- ❌ 不能改 `read_temperature()` 的转换公式（board.py 不可运行时修改）
- ❌ 不能把 `Pin(5)` 换成 `Pin(12)`（引脚所有权已在 Core 0 锁死）
- ❌ 不能绕过 `power_off()` 直接操作继电器寄存器

### 10.4 为什么是混合模型

纯预蒸馏的问题：**太死。** 如果所有硬件操作都固化为预定义函数，Agent 只能用"工具箱"里的有限工具。产线换了新传感器、增加了新外设、业务逻辑变了——你必须改 board.py、重新烧录。这跟 Agent-on-Device 的 C 工具注册表没有本质区别。

纯自进化的问题：**太危险。** 如果 Agent 可以写任意 Python 控制任意引脚，它在物理世界里的权限和开发者一样大。一个幻觉、一次 prompt injection、一个推理错误——硬件可能烧、产线可能停。

PAL 的混合模型：**预蒸馏保证了安全下限，自进化提供了灵活上限。**

```
         预蒸馏 (不可变)                自进化 (可变)
    ┌─────────────────────┐     ┌─────────────────────┐
    │ Core 0 C 驱动       │     │ Agent 生成的 Python  │
    │ machine 库          │     │ 工作流编排            │
    │ board.py 安全函数   │     │ 判断逻辑              │
    │ 引脚所有权表        │     │ 事件策略              │
    │                     │     │ Skills 积累           │
    │ "刹车永远有效"       │     │ "怎么开可以随时改"     │
    └─────────────────────┘     └─────────────────────┘
              ↓                           ↓
         永不妥协                       可以试错
```

**这就是 PAL 对"自进化 vs 预蒸馏"争论的答案：不是说哪一个更好——是说它们该待在各自的核里。** Core 0 是物理世界的刹车，永远不动。Core 1 是 Agent 的方向盘，Agent 可以随时换握法。

### 10.5 对社区的意见

Hermes 证明了"自进化 Agent"在数字世界的巨大价值。ESP-Claw 证明了 Agent 可以跑在 MCU 上。PAL 的立场是两者的交集：**物理世界的安全边界必须预蒸馏（Core 0），但 Agent 的决策灵活性可以通过自进化实现（Core 1）。** "先蒸馏再部署"和"先部署再学习"不是二选一——它们可以住在同一块芯片的不同核上。

**两种模式的理想融合：** Agent 在云端通过仿真和数字孪生预蒸馏新的硬件知识（验证过的 board.py 更新），然后通过 OTA 更新 Core 0。同时，Agent 在 Core 1 上自进化——从每次交互中学习更好的工作流编排方式。**预蒸馏更新是慢的、审慎的、经过硬件测试的。自进化是快的、实时的、可逆的。**

---

## 11. AI 在嵌入式系统中的决策边界

> *"有些地方就是不能上 AI，就是得实时。"*

AI 进入物理世界，必须回答一个根本问题：**哪里是 AI 可以走的，哪里是 AI 绝对不能碰的。** 这一章定义 PAL 的决策边界——这不是在限制 AI，而是在保护物理世界。

### 11.1 三层决策模型

```
┌──────────────────────────────────────────────────────┐
│ Layer 3: AI 决策域 (云端 Agent)                       │
│ ─────────────────────────────────────────────────── │
│ · 工作流编排: "先扫描所有传感器 → 检查数据 → 生成报告"    │
│ · 策略优化: "根据历史数据调整采样频率"                        │
│ · 异常处理: "温度传感器 3 连续超阈值，可能是设备故障，建议排查" │
│ · 技能组合: "把读温度 + 判断阈值 + 开风扇拼成一个自动化"       │
│                                                      │
│ 延迟: 秒级 ~ 分钟级                                    │
│ 出错后果: 效率损失，可纠正                              │
├──────────────────────────────────────────────────────┤
│ Layer 2: 软实时决策域 (PAL Core 1 — MicroPython)      │
│ ─────────────────────────────────────────────────── │
│ · 事件路由: "传感器超阈值 → 立刻推送给云端"                │
│ · 协议转换: "云端 JSON → SPI 命令帧"                   │
│ · 本地缓存: "设备状态快照，断网时提供最后已知状态"          │
│                                                      │
│ 延迟: 毫秒级 ~ 百毫秒级                                │
│ 出错后果: 数据丢失或延迟，可恢复                        │
├──────────────────────────────────────────────────────┤
│ Layer 1: 硬实时域 (实时 MCU / PAL Core 0 — C)         │
│ ─────────────────────────────────────────────────── │
│ · 传感器轮询 (10ms 周期)                               │
│ · 硬件看门狗 (~10s 超时)                               │
│ · 总线状态监控                                         │
│ · 通信总线恢复                                         │
│                                                      │
│ 延迟: 微秒级                                          │
│ 出错后果: 设备离线、总线锁死、系统级故障                 │
│                                                      │
│ ⛔ AI 禁止进入这一层                                   │
└──────────────────────────────────────────────────────┘
```

**AI 的决策权限从 Layer 1 到 Layer 3 逐步递增。Layer 1 完全不开放给 AI——这不是"建议"，是硬件的物理隔离。**

### 11.2 AI 可以做什么：拼积木

在 Layer 3，AI 的角色是**把已有的硬件原语组合成工作流**：

```python
# AI 生成的 glue code（运行在云端推理，通过 PAL 协议发到终端执行）:

# 场景: "检测温度传感器，如果超过阈值就关断电源并告警"
temperature = i2c.readfrom(0x48, 2)       # 积木 1: 读温度传感器
temp_c = (temperature[0] << 8 | temperature[1]) * 0.0625

if temp_c > 60:                            # 判断
    relay_power.off()                      # 积木 2: 关继电器（硬断电）
    event_push("overtemp", {"sensor": "temp_3", "value": temp_c})  # 积木 3: 上报
```

AI 做的事情：
- ✅ 判断温度阈值
- ✅ 决定关哪个继电器
- ✅ 组合"读传感器 → 判断 → 执行 → 上报"的流程

AI 不做的事情：
- ❌ 调 I2C 时序参数（那是 `machine.I2C` 的事）
- ❌ 配置 GPIO 寄存器（那是 `machine.Pin` 的事）
- ❌ 判断总线是否锁死（那是 Layer 1 C 驱动的事）

**AI 只需要知道"有一个叫温度的东西，读出来是数字，高了就断电"。这就是"拼积木"。**

在开发板上，积木（引脚定义、外设信息）由开发者通过 `board.py` 提供。在工程级系统中，积木在 PCB 设计阶段就已经确定。

### 11.3 AI 不可以做什么：硬实时域

以下操作**永远不经过 AI**，由 Layer 1 实时层独立执行：

| 操作 | 原因 | 谁执行 |
|---|---|---|
| 传感器轮询 (每 10ms) | 错过一轮 = 数据滞后，AI 推理延迟不可控 | Layer 1 实时循环 |
| 硬件看门狗 | ~10s 超时复位，必须独立于 AI | 硬件振荡器 |
| 总线恢复 | 总线锁死必须毫秒级响应 | Layer 1 ISR |
| 设备发现与枚举 | 多节点插入的碰撞窗口必须实时处理 | Layer 1 协议栈 |
| 电源管理 / 安全停机 | 过流/过温/急停，不可有任何延迟 | 硬件电路 + Core 0 |
| 脉冲/编码器计数 | μs 级脉冲，丢一个就错位 | Layer 1 中断 |

**这些操作如果经过 AI → 推理 → 决策 → 执行，延迟是不可接受的。AI 被禁止进入这一层。**

### 11.4 紧急程度分级：AI 的决策权限表

物理世界的事件不是二元的"能/不能"——是按紧急程度分级的：

```
─────────────── 紧急程度 ───────────────→
│                                      │
紧急 (μs-ms)    亚紧急 (ms-s)          非紧急 (s-min)
│                │                     │
▼                ▼                     ▼
⛔ AI 禁止       ⚠️ AI 可观察           ✅ AI 可决策
                不可直接决策             
                                        
例:              例:                   例:
· 看门狗超时      · 传感器连续 2 次超时   · 优化采样策略
· 过流保护        · 温度接近阈值          · 调整设备参数
· 急停按钮        · WiFi 信号弱          · 生成维护计划
· 总线锁死        · 设备状态表接近满      · 预测性维护
```

**Layer 1 实时层负责紧急和亚紧急的实时响应。亚紧急事件可以通过 Core 1 推送给云端 AI 作为**观察输入**，但 AI 的决策在云端完成，且只能影响 Layer 3 的行为——不能越过 Layer 2 直接操作 Layer 1。**

### 11.5 AI 被污染：物理世界的特殊风险

**这是所有 AI 系统的共性弱点，但在物理世界中后果是指数级放大的。**

```
数字世界:  AI 被污染 → 生成错误代码 → CI 报错 → 修 Bug → 恢复
           影响: 一次失败的部署，可回滚

物理世界:  AI 被污染 → 生成错误指令 → GPIO 错误翻转 → 
           220V 继电器误关闭 → 产线停机 / 设备损坏 / 人员安全风险
           影响: 不可逆，不可回滚
```

PAL 没有能力解决"AI 被污染"这个问题——这是 AI 安全领域的基础性挑战。但 PAL 可以做的是**限制被污染后的爆炸半径**：

| 防护层 | 机制 | 限制了什么 |
|---|---|---|
| **硬件隔离** | Layer 1 实时 MCU 不接收来自上层的命令修改 | AI 无法修改看门狗、无法跳过安全停机 |
| **引脚所有权** | Core 0 的 `OWNER_SYSTEM` vs `OWNER_AGENT` | AI 只能操作被标记为"安全"的引脚 |
| **执行超时** | 每条 AI 代码最长执行 30s | 死循环不会永久占用 Core 1 |
| **Core 1 隔离** | Core 0 独立于 MicroPython VM | AI 搞崩 Python VM → Core 0 重启 Core 1 → 物理系统不受影响 |
| **云端沙箱** | Agent 在云端推理，不直接操作硬件 | 被污染的 Agent 生成的指令在 JSON 层可见、可审计、可切断 |

**最重要的防线：AI 永远不能直接操作 Layer 1 硬件。** AI 的所有指令必须经过至少一层翻译（云端 JSON → Core 1 Python → machine 库 C → 硬件寄存器）。每一层都是审计点和拦截点。

### 11.6 明确适用场景：AI 在嵌入式中的边界清单

**AI 适合做：**
- ✅ 技能组合：把已有外设原语拼成工作流
- ✅ 参数调优：基于历史数据调整非实时的系统参数（扫描周期、上报频率）
- ✅ 异常诊断：分析离线模式、识别故障趋势
- ✅ 策略决策：库存管理、补货计划、设备调度

**AI 不适合做：**
- ❌ 实时控制：任何 μs-ms 级的闭环控制
- ❌ 安全关键：紧急停机、过流保护、安全联锁
- ❌ 协议栈实现：I2C/SPI/UART 的时序操作
- ❌ 硬件初始化：时钟配置、引脚模式设置、外设校准
- ❌ 看门狗管理：WDT 喂狗、复位策略

**一句话：AI 做上层决策（拼积木），C 做底层执行（造积木）。二者之间的线就是 PAL 的 Core 0 / Core 1 边界。**

---

## 12. FAQ

**Q: PAL 和 MicroPython 自带的 WebREPL 有什么区别？**

A: WebREPL 提供的是一个交互式的 Python REPL，没有安全边界——你可以 `import machine` 然后操作任何引脚，包括系统用的。PAL 在 WebREPL 的基础上加了：① 引脚所有权管理；② Core 0 系统保护；③ 结构化的 JSON 协议（不只是裸 REPL）；④ 事件推送机制。

**Q: 一定要用 ESP32-S3 吗？**

A: 不。PAL Level 1 可以在任何支持 MicroPython 的 MCU 上跑。PAL Level 2 建议双核 MCU 以实现 Core 0/Core 1 分离，ESP32-S3 是目前性价比最高的选项。

**Q: 安全吗？Agent 会把硬件搞坏吗？**

A: PAL Level 2+ 的 Core 0 负责保护系统完整性。Agent 只能操作被标记为 `OWNER_AGENT` 的引脚，不能禁用看门狗、不能改网络配置、不能操作系统总线。最坏情况：Agent 崩了 → Core 0 检测到心跳超时 → 自动重启 Core 1 MicroPython VM → 系统继续运行。

**Q: 延迟怎么样？**

A: Agent → WebSocket → JSON 解析 → Python 执行 → machine 库（C 底层）→ 硬件。典型往返：WiFi 局域网 <10ms，Python 执行 <1ms。总量 ~10-20ms。对于物理操控场景（开关继电器、读传感器、更新显示），这个延迟完全可接受。

---

## 13. 贡献与讨论

本规范处于草案阶段。以下问题需要社区的输入：

1. **Core 0 的边界应该定在哪里？** 哪些功能必须锁死在 Core 0，哪些可以下沉？
2. **PAL 协议是否需要支持流式执行？** 即 Agent 持续发送代码块，终端持续返回结果？
3. **多终端协调**：多个 PAL 终端是否需要一个上层的协调协议？
4. **认证与安全**：Agent ↔ 终端之间的认证机制应该如何设计？
5. **Level 3 的冗余策略**：双 MCU 物理隔离的具体方案？

### Future Work：MCP 集成路线

PAL 的 JSON 协议与 MCP (Model Context Protocol) 是互补关系（详见 [§6.1](#61-pal-与-mcp物理世界的最后一段)）。以下是 PAL 与 MCP 集成的规划路线：

| 阶段 | 任务 | 说明 |
|---|---|---|
| **Phase 1** | 开发 `pal-mcp-bridge` | 一个 MCP Server 包装器，将 PAL 终端的 `board.py` 工具定义自动转换为 MCP tool schema，让任何支持 MCP 的 Agent 框架可以直接发现 PAL 终端的工具 |
| **Phase 2** | MCP Transport 适配 | 支持 MCP 的 stdio/SSE/WebSocket 传输层，让 PAL 终端可被 MCP 客户端直接连接 |
| **Phase 3** | 双向事件通道 | 将 PAL 的 `type: "event"` 消息映射为 MCP 的 server→client notifications，实现物理事件（引脚变化、ADC 阈值）的 MCP 原生推送 |
| **Phase 4** | 认证与授权 | 基于 MCP 的 auth 扩展，为 PAL 终端添加 Token/OAuth 认证，解决当前安全模型中的信任假设 |

目标：**一个 PAL 终端既可以通过原生 PAL JSON 协议操控（轻量、低延迟），也可以通过 MCP 协议被任何兼容 Agent 发现和调用（生态兼容）。**

欢迎通过 Issues 提交讨论或 Pull Request 参与规范修订。

---

## 14. 许可

本规范文档采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 许可。

参考实现代码（`impl/` 目录）采用 [MIT](https://opensource.org/license/MIT) 许可。

---

> *"The best way to predict the future is to define it."*
>
> *PAL v0.1 — 2026-06-28, 于安徽理工大学*
