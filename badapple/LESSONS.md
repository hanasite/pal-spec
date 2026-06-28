# Bad Apple on ESP32-S3 + SSD1306 + W25Q64 — 踩坑记录

> 5478 帧, 128×64, 25fps, 5.3MB → W25Q64 8MB Flash → SSD1306 OLED
> 总耗时：约 3 小时

## 硬件

| 外设 | 接口 | 引脚 |
|---|---|---|
| SSD1306 128×64 OLED | I2C | SCL=7, SDA=6 |
| W25Q64 8MB Flash | SPI | CS=14, SCK=12, MOSI=11, MISO=13 |
| 白灯 | GPIO | 21 |

## 踩坑清单

### 1. 视频字节打包方向（最坑，反复 3 次）

**现象**：画面出现 8 个重复的异常宽度的拷贝。

**根因**：SSD1306 的 framebuf.MONO_VLSB 要求字节按**垂直**方向打包（1 字节 = 8 个垂直像素，bit 0 = 顶部），但我先用了水平打包（1 字节 = 8 个水平像素），导致图像被"旋转"显示。

**修复**：
```python
# 正确：垂直打包 (PAGE-MAJOR)
# buffer[page * 128 + col], byte bit = 垂直像素 (0=top)
for page in range(8):
    for col in range(128):
        byte = 0
        for bit in range(8):
            if binary[page * 8 + bit, col] > 0:
                byte |= 1 << bit
        data[page * 128 + col] = byte
```

**教训**：先用已知测试图案（如单个像素、棋盘格）验证显示映射，再处理所有帧。

### 2. USB D+ 上拉电阻导致 GPIO 20 无法拉低

**现象**：白灯接到 GPIO 20 后始终微亮，`off()` 无效。

**根因**：ESP32-S3 的 GPIO 20 是 USB D+，PCB 上有 1.5kΩ 上拉到 3.3V（USB 规范要求）。

**修复**：换到 GPIO 21。

### 3. 串口传输太慢

**现象**：5.3MB 通过 UART 115200 传输需 ~8 分钟。

**方案**：改用 WiFi TCP 传输（~10 秒）。

**关键代码**：
```python
# ESP32 端：WiFi + TCP server
wlan.connect(ssid, password)
s = socket.socket(); s.bind(('0.0.0.0', 8888)); s.listen(1)
conn, _ = s.accept()
# 接收数据直接写 W25Q64
```

### 4. WiFi 密码中的全角字符

**现象**：SSID 含全角字符时连接失败。

**根因**：SSID 末尾有全角感叹号（如 `MyWiFi！`），`wlan.scan()` 结果不显示此字符。

**修复**：直接 `wlan.scan()` 拿到的 SSID 包含全角字符。

### 5. W25Q64 旧数据没清除

**现象**：内部 Flash 播放正常，搬到 W25Q64 后仍然出现"8 个"异常。

**根因**：W25Q64 中残留之前的错误格式数据，新write只覆盖了前 256KB（文件不完整）。

**修复**：全片擦除（Chip Erase, 0xC7）后再写入。

```python
cs.value(0); spi.write(b'\x06'); cs.value(1)  # Write Enable
cs.value(0); spi.write(b'\xC7'); cs.value(1)  # Chip Erase
# 等待 BUSY 位清零（~10-50秒）
```

### 6. sendall() 完成 ≠ 数据到达

**现象**：`socket.sendall()` 在 Python 侧瞬间返回（0.0s），但 ESP32 收到的文件只有 353 KB / 5.3 MB。

**根因**：`sendall()` 只是把数据推到 OS 的 TCP 缓冲区就返回了。ESP32 端 `recv()` 需要等待实际网络传输。WiFi 信号波动可能导致传输中断。

**验证**：接收完后检查文件大小 `os.stat('badapple.bin')[6]`。

### 7. COM 口释放

**现象**：`mpremote: failed to access COM9`，背景任务占着串口。

**方案**：按 RST 键强制释放，或让后台任务自然结束。

### 8. SoftI2C 带宽不够 25fps

**现象**：25fps 时画面抖动丢帧。

**修复**：切到硬件 I2C `I2C(0, scl=Pin(7), sda=Pin(6), freq=1_000_000)`，传输从 ~20ms 降到 ~8ms/帧。

## 验证流程（推荐顺序）

1. 直接 I2C 写测试图案验证像素映射
2. 提取单帧 → 显示验证格式
3. 小批量帧（100 帧）内部 Flash 播放验证
4. 全部帧 WiFi 传输 → 内部 Flash
5. W25Q64 全片擦除 → 搬家 → 播放

## 文件清单

```
badapple/
├── convert_video.py   # MP4 → 128×64 1-bit 二进制
├── wifi_play.py       # WiFi TCP 接收 + 内部 Flash 播放
├── play_badapple.py   # 内部 Flash → W25Q64 → 播放
├── ssd1306.py         # SSD1306 驱动 (MicroPython 官方)
└── LESSONS.md         # 本文件
```
