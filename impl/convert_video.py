"""Bad Apple MP4 → 128x64 1-bit binary (SSD1306 PAGE-MAJOR format)"""
import cv2, struct, sys
from PIL import Image

VIDEO = r"C:\Users\kakun\Downloads\【東方】Bad Apple!! ＰＶ【影絵】.mp4"
OUTPUT = r"F:\MCU\DA_CHUANG\esp32_pal\badapple.bin"
TARGET_FPS = 25
W, H = 128, 64

cap = cv2.VideoCapture(VIDEO)
orig_fps = cap.get(cv2.CAP_PROP_FPS)
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Original: {total} frames, {orig_fps:.1f} fps")
interval = orig_fps / TARGET_FPS

frames = []
idx = 0
while True:
    ret, frame = cap.read()
    if not ret: break
    if int(idx % interval) == 0:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (W, H))
        _, binary = cv2.threshold(resized, 128, 255, cv2.THRESH_BINARY)
        # SSR1306 PAGE-MAJOR: page * 128 + col, bit=vertical pixel (LSB = top)
        data = bytearray(W * H // 8)
        for page in range(8):
            for col in range(128):
                byte = 0
                for bit in range(8):
                    if binary[page * 8 + bit, col] > 0:
                        byte |= 1 << bit
                data[page * 128 + col] = byte
        frames.append(data)
    idx += 1
    if idx % 500 == 0: print(f"  {idx}/{total}")
cap.release()

# Write binary
with open(OUTPUT, 'wb') as f:
    f.write(struct.pack('<IHH', len(frames), W, H))
    f.write(b'\x00' * 8)
    for data in frames:
        f.write(data)

mb = len(frames) * (W * H // 8) / 1024 / 1024
print(f"\nOutput: {len(frames)} frames, {W}x{H}, {mb:.2f} MB")
print(f"Duration: {len(frames)/TARGET_FPS:.1f}s @ {TARGET_FPS}fps")

# Verify: render frame 500 to PNG
fdata = frames[min(500, len(frames)-1)]
img = Image.new('1', (W, H))
px = img.load()
for page in range(8):
    for col in range(128):
        for bit in range(8):
            if fdata[page * 128 + col] & (1 << bit):
                px[int(col), int(page * 8 + bit)] = 1
img = img.resize((512, 256), Image.NEAREST)
img.save(r"F:\MCU\DA_CHUANG\esp32_pal\frame500.png")
print("Saved frame500.png — check this file on PC first!")
