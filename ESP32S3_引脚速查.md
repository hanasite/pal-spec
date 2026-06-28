# ESP32-S3 引脚速查表

> 芯片：ESP32-S3 (QFN56, rev v0.2) | MicroPython v1.28.0
> 安全可用 GPIO：避开 strapping / flash / JTAG
> 标注 ⚡ 的为已接线引脚

## 当前已用引脚

| GPIO | 功能 | 说明 |
|---|---|---|
| 21 ⚡ | 白色 LED | 高电平点亮 |
| 38 | 蓝色 LED | 已移除 |

## 当前已接线外设

| 外设 | 引脚 | 协议 |
|---|---|---|
| W25Q64 (8MB Flash) | CS=14, SCK=12, MOSI=11, MISO=13 | SPI2 |
| SSD1306 0.96" OLED | SCL=7, SDA=6 | I2C0 |
| 白色 LED | GPIO 21 | GPIO |

---

## ⛔ 绝对不要用（系统保留）

| 引脚 | 原因 |
|---|---|
| **GPIO 0** | Strapping 引脚 — 启动模式选择（拉低=下载模式） |
| **GPIO 3** | Strapping 引脚 — JTAG 信号控制 |
| **GPIO 46** | Strapping 引脚 — VDD_SPI 电压控制 |
| **GPIO 26-32** | 封装内 Flash/PSRAM 占用，不可他用 |
| **GPIO 33-37** | 八线 PSRAM 时占用（你的板子有 PSRAM 则避用） |
| **GPIO 19, 20** | USB D+ / USB D-（USB-Serial-JTAG） |
| **GPIO 43, 44** | U0TXD / U0RXD（默认串口，调试用） |

---

## ✅ 安全可用 GPIO

### GPIO 1-18 区（RTC 域，可用）

| GPIO | MicroPython 引脚 | 备注 |
|---|---|---|
| **GPIO 1** | `Pin(1)` | ADC1_CH0，可做模拟输入 |
| **GPIO 2** | `Pin(2)` | ADC1_CH1 |
| **GPIO 4** | `Pin(4)` | ADC1_CH3，触摸传感器 |
| **GPIO 5** | `Pin(5)` | ADC1_CH4 |
| **GPIO 6** | `Pin(6)` | ADC1_CH5 |
| **GPIO 7** | `Pin(7)` | ADC1_CH6 |
| **GPIO 8** | `Pin(8)` | ADC1_CH7 |
| **GPIO 9** | `Pin(9)` | — |
| **GPIO 10** | `Pin(10)` | — |
| **GPIO 11** | `Pin(11)` | — |
| **GPIO 12** | `Pin(12)` | — |
| **GPIO 13** | `Pin(13)` | — |
| **GPIO 14** | `Pin(14)` | — |
| **GPIO 15** | `Pin(15)` | — |
| **GPIO 16** | `Pin(16)` | — |
| **GPIO 17** | `Pin(17)` | — |
| **GPIO 18** | `Pin(18)` | — |

### GPIO 21, 38, 39-42, 45, 47-48 区

| GPIO | 状态 | 备注 |
|---|---|---|
| **GPIO 21** ⚡ | 已用 | 白色 LED |
| **GPIO 38** ⚡ | 已用 | 蓝色 LED |
| **GPIO 39** | ✅ 安全 | — |
| **GPIO 40** | ✅ 安全 | — |
| **GPIO 41** | ✅ 安全 | — |
| **GPIO 42** | ✅ 安全 | — |
| **GPIO 45** | ✅ 安全 | — |
| **GPIO 47** | ✅ 安全 | — |
| **GPIO 48** | ✅ 安全 | — |

---

## 常用外设推荐引脚

| 外设 | 推荐引脚 | MicroPython 代码 |
|---|---|---|
| **I2C (SDA, SCL)** | GPIO 5, GPIO 6 | `I2C(0, scl=Pin(6), sda=Pin(5))` |
| **SPI (SCK, MOSI, MISO, CS)** | 12, 11, 13, 10 | `SPI(2, sck=Pin(12), mosi=Pin(11), miso=Pin(13))` |
| **UART (TX, RX)** | GPIO 17, GPIO 18 | `UART(1, tx=Pin(17), rx=Pin(18))` |
| **PWM（任意安全 GPIO）** | — | `PWM(Pin(4), freq=1000)` |
| **ADC** | GPIO 1-8 | `ADC(Pin(1)).read()` |
| **触摸** | GPIO 4 | `TouchPad(Pin(4)).read()` |

---

## MicroPython 快速参考

```python
from machine import Pin, ADC, I2C, SPI, PWM, UART

# GPIO
led = Pin(38, Pin.OUT)
led.on()

# ADC
adc = ADC(Pin(1))
print(adc.read())  # 0-4095

# I2C
i2c = I2C(0, scl=Pin(6), sda=Pin(5), freq=100000)
print([hex(d) for d in i2c.scan()])

# PWM
pwm = PWM(Pin(4), freq=1000, duty=512)  # 0-1023

# 列出当前已用引脚
# 记在这里：
#   Pin 38 → 蓝色 LED
#   Pin 21 → 白色 LED
#   Pin __ → __________
#   Pin __ → __________
```

---

> **接外设前看一眼**：避开 ⛔ 区，用 ✅ 区。新接的设备记在上面的清单里，下次 Claude 直接看这个文件就知道板子状态。
