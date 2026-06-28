"""WiFi TCP recv → internal flash → Play"""
from machine import Pin, I2C
import ssd1306, network, socket, time, struct

i2c = I2C(0, scl=Pin(7), sda=Pin(6), freq=1_000_000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
led = Pin(21, Pin.OUT)

# WiFi
oled.fill(0); oled.text("WiFi...", 30, 28); oled.show()
wlan = network.WLAN(network.STA_IF)
wlan.active(False); time.sleep(0.3); wlan.active(True); time.sleep(0.3)
wlan.connect('YOUR_SSID', 'YOUR_PASSWORD')
for _ in range(30):
    if wlan.isconnected(): break
    time.sleep(0.5)
ip = wlan.ifconfig()[0]
oled.fill(0); oled.text("WiFi OK", 25, 20); oled.text(ip, 15, 40); oled.show()

# TCP recv → file
a = socket.getaddrinfo('0.0.0.0', 8888)[0][-1]
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(a); s.listen(1); s.settimeout(120)
oled.fill(0); oled.text("WAIT PC", 15, 28); oled.show()
c, _ = s.accept()
oled.fill(0); oled.text("RECV...", 10, 28); oled.show()

# Receive and save
hdr = b''
while len(hdr) < 4: hdr += c.recv(4 - len(hdr))
tf = struct.unpack('<I', hdr[:4])[0]
tb = tf * 1024 + 16
f = open('badapple.bin', 'wb')
f.write(hdr + b'\x80\x00\x40\x00' + b'\x00' * 8)  # header
received = 0
while received < tb - 16:
    ck = c.recv(8192)
    if not ck: break
    f.write(ck)
    received += len(ck)
    pct = received * 100 // (tb - 16)
    if pct % 10 < 1:
        oled.fill_rect(0, 56, 128, 8, 0)
        oled.fill_rect(0, 57, pct * 128 // 100, 4, 1)
        oled.show()
f.close(); c.close(); s.close()
oled.fill(0); oled.text(f"RECV {tf}f", 15, 28); oled.show()
time.sleep(0.5)

# Play from internal flash
oled.fill(0); oled.show()
f = open('badapple.bin', 'rb'); f.read(16)
t0 = time.ticks_ms()
for i in range(tf):
    ft = time.ticks_ms()
    f.seek(16 + i * 1024)
    oled.buffer[:] = f.read(1024)
    oled.show()
    led.value(i % 12 < 2)
    dt = time.ticks_diff(time.ticks_ms(), ft)
    if dt < 40: time.sleep_ms(40 - dt)
f.close(); led.off()
ms = time.ticks_diff(time.ticks_ms(), t0)
fps = tf * 1000 // ms if ms else 0
oled.fill(0); oled.text("DONE!", 30, 10)
oled.text(f"{tf}f {ms}ms", 10, 30); oled.text(f"~{fps}fps", 20, 50); oled.show()
print(f'PLAY {tf}f {ms}ms {fps}fps')
