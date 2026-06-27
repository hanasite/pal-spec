# PAL: Giving AI Agents Hands in the Physical World

> *REPL Is All You Need.*
>
> A 19-year-old's proposal for an open standard that lets Claude and GPT control hardware directly.

---

## The Problem: AI Agents Are Trapped in Screens

AI agents can write code, search the web, deploy servers, and manage databases. They're incredibly capable — inside a container.

But ask your favorite AI to **flip a relay**, **read a temperature sensor**, or **scan an I2C bus** — and it can't. Not because it doesn't know how. It knows exactly what `machine.Pin(5, Pin.OUT)` does. It just has nowhere to run that code.

**AI agents lack a physical execution terminal.**

CLI tools gave LLMs hands in the digital world (`df -h`, `pip install`, `docker compose up`). Embedded systems can give them hands in the real world (`GPIO.on()`, `ADC.read()`, `I2C.scan()`). But nobody has defined a standard for how agents should talk to hardware.

That's what PAL is.

---

## The Landscape: What Exists, and Why It Falls Short

### ESP-Claw (Espressif Official)

Espressif's "Chat Coding" framework puts a full AI agent on an ESP32-S3 — ReAct loop, LLM calls, tool registry, IM channels (Telegram, WeChat), Event Router. It's impressive engineering. It's also the wrong architecture.

- **Agent runs on the MCU** — 8MB PSRAM minimum, $15+ BOM
- **Uses Lua** — LLMs generate Python 50x more accurately than Lua
- **Pre-registration required** — every GPIO needs a C struct registered as a Lua tool module
- **LLM API calls from MCU** — one network timeout can stall the entire FreeRTOS task

### mimiclaw

A lighter ESP32 agent. Same architecture, GPIO bugs confirmed. Toy-grade.

### Bare-metal C + UART commands

Rock solid. But adding a new operation means: write C → compile → flash → reboot. 10 minutes minimum. Agents can't iterate at that speed.

### Raspberry Pi + GPIO

Python libraries everywhere, but 30-second boot, 5W power draw, $35+ cost, no hard real-time. Overkill for controlling a relay.

---

## The Core Insight: MicroPython REPL IS the Agent Interface

Here's what everyone missed: **Python's REPL and an AI agent's interaction model are isomorphic.**

```
REPL loop:                    Agent loop:
  >>> type code                 receive task
  execute                       reason → generate code
  see output                    send code to REPL
  >>> type next                 observe result → adjust
```

You don't need a tool registry. You don't need JSON schema. You don't need a Skill Registry. **The REPL is the world's simplest IPC.**

And Python? It's the language LLMs generate best — 25% of GitHub public repos, versus <0.5% for Lua. Claude has seen millions of `machine.Pin()` calls in training data. It knows how to write this code.

---

## The Architecture: PAL in Two Cores

```
┌──────────────────────────────────────┐
│         Cloud Agent (AstrBot)         │  ← Reasoning, planning
└──────────────┬───────────────────────┘
               │ WebSocket JSON
┌──────────────▼───────────────────────┐
│        ESP32-S3 PAL Terminal          │
│                                       │
│  Core 0 (C, FreeRTOS, NEVER CHANGES): │  ← Hard real-time
│  · SPI/I2C/UART drivers               │
│  · Hardware watchdog                  │
│  · WiFi auto-reconnect               │
│  · Pin ownership table                │
│                                       │
│  Core 1 (MicroPython, ANYTHING GOES): │  ← Agent playground
│  · WebSocket → JSON → Python exec     │
│  · machine module → hardware          │
│  · uasyncio → concurrent tasks        │
│  · Crash? Core 0 restarts you.        │
└──────────────────────────────────────┘
```

**Core 0 is the brake pedal. It never changes. Core 1 is the steering wheel. The agent can grip it however it wants.**

If the agent writes an infinite loop? Core 0 detects heartbeat timeout → restarts Core 1 VM. If the agent tries to access system pins? `machine.Pin()` returns `OSError`. If the agent crashes? Core 0 keeps running. Physical control link never breaks.

---

## The Protocol: JSON That Executes Python

No tool schemas. No pre-registration. Just Python code over WebSocket:

**Agent → Terminal:**
```json
{
  "version": "1",
  "id": "msg_001",
  "type": "exec",
  "code": "from machine import Pin; Pin(5, Pin.OUT).on()",
  "timeout_ms": 10000
}
```

**Terminal → Agent:**
```json
{
  "version": "1",
  "id": "msg_001",
  "type": "result",
  "stdout": "",
  "stderr": "",
  "error": false,
  "exec_time_ms": 12
}
```

That's it. One round-trip over WiFi: <10ms. Python execution: <1ms.

---

## Why Cloud Agent, Not On-Device Agent

### 1. Brain and hands should use different hardware

Physical execution needs determinism, low latency, 24/7 stability. AI reasoning needs elastic compute, large memory, frequent iteration. Forcing both onto one MCU is asking one chip to do two contradictory things.

### 2. One brain, many hands

A single cloud agent can manage dozens of PAL terminals across a factory floor. Agent-on-Device requires one agent instance per node — no global perspective.

### 3. You can stop the brain anytime

Cloud agent misbehaving? Cut the WebSocket. It's over. Agent-on-Device misbehaving on an MCU? You wait for the hardware watchdog to trigger — that's your only recovery mechanism.

### 4. Skills, MCP, tools run on cloud infrastructure

Hermes-style skill accumulation, vector databases, MCP tool chains, SQLite persistence — all mature AI infrastructure. None of it needs to be squeezed into 8MB of PSRAM.

---

## What PAL Is, and What It Isn't

**PAL IS:**
- ✅ An agent-friendly embedded terminal standard (ESP32-class, MicroPython, dual-core)
- ✅ A JSON protocol for executing Python code on hardware
- ✅ A safety model (5-layer defense, pin ownership, Core 0 isolation)

**PAL IS NOT:**
- ❌ An I2C/SPI bus protocol
- ❌ An Agent framework
- ❌ A hardware reference design
- ❌ Tied to any specific MCU or peripheral

---

## Current Status

PAL is a **draft specification (v0.1)**. I'm a freshman at Anhui University of Science and Technology. The reference implementation (ESP32-S3 Core 0/1) is under development.

*Note: I'm currently preparing for exams and still learning how to express technical ideas fluently in English, so I used Claude to help draft and polish this post. All ideas, architecture, and the PAL specification itself are my own work.*

This spec is open for discussion. I'm looking for:
- Feedback on the architecture
- Core 0 boundary definition
- Multi-terminal coordination
- MCP integration (Phase 1-4 roadmap in the repo)

---

## Links

- **GitHub (International):** [github.com/hanasite/pal-spec](https://github.com/hanasite/pal-spec)
- **Gitee (China):** [gitee.com/yosakun/pal-spec](https://gitee.com/yosakun/pal-spec)

---

> *"The best way to predict the future is to define it."*
>
> *— PAL v0.1, 2026*
