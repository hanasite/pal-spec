"""
ESP32-S3 Bad Apple — Copy to W25Q64 then play on SSD1306
"""
from machine import Pin, SoftSPI, I2C
import ssd1306, time

cs  = Pin(14, Pin.OUT, value=1)
spi = SoftSPI(baudrate=8_000_000, sck=Pin(12), mosi=Pin(11), miso=Pin(13))
i2c = I2C(0, scl=Pin(7), sda=Pin(6), freq=1_000_000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
led = Pin(21, Pin.OUT)
FRAME_SIZE = 1024

def w25_wait():
    while True:
        cs.value(0); spi.write(b'\x05'); s = spi.read(1); cs.value(1)
        if not (s[0] & 1): break

def w25_write(addr, data):
    cs.value(0); spi.write(b'\x06'); cs.value(1)
    cs.value(0)
    spi.write(bytes([0x02, addr>>16&0xFF, addr>>8&0xFF, addr&0xFF]))
    spi.write(data)
    cs.value(1)
    w25_wait()

def w25_read(addr, n):
    cs.value(0)
    spi.write(bytes([0x03, addr>>16&0xFF, addr>>8&0xFF, addr&0xFF]))
    d = spi.read(n)
    cs.value(1)
    return d

# Phase 1: Copy badapple.bin from internal flash to W25Q64
oled.fill(0)
oled.text("COPY TO W25Q64", 5, 20)
oled.show()

with open('badapple.bin', 'rb') as f:
    header = f.read(16)
    total_frames = int.from_bytes(header[:4], 'little')
    w, h = int.from_bytes(header[4:6], 'little'), int.from_bytes(header[6:8], 'little')
    print(f"Frames: {total_frames}, {w}x{h}")

    total = total_frames * FRAME_SIZE
    addr = 0
    while True:
        chunk = f.read(256)
        if not chunk: break
        w25_write(addr, chunk)
        addr += len(chunk)
        if addr % (FRAME_SIZE * 200) == 0:
            pct = addr * 100 // total
            oled.fill_rect(0, 56, 128, 8, 0)
            oled.fill_rect(0, 57, pct * 128 // 100, 4, 1)
            oled.show()

oled.fill(0)
oled.text("COPY DONE!", 15, 28)
oled.show()
print(f"Copied {total_frames} frames")

# Phase 2: Play
time.sleep(1)
oled.fill(0); oled.show()

t0 = time.ticks_ms()
for f in range(total_frames):
    ft = time.ticks_ms()

    data = w25_read(f * FRAME_SIZE, FRAME_SIZE)
    oled.buffer[:] = data
    oled.show()

    led.value(f % 12 < 2)

    dt = time.ticks_diff(time.ticks_ms(), ft)
    if dt < 40:
        time.sleep_ms(40 - dt)

led.off()
total_ms = time.ticks_diff(time.ticks_ms(), t0)
fps = total_frames * 1000 // total_ms if total_ms else 0
oled.fill(0)
oled.text("BAD APPLE DONE", 5, 15)
oled.text(f"{total_frames}f {fps}fps", 15, 35)
oled.show()
print(f"Done: {total_frames}f in {total_ms}ms ~{fps}fps")
