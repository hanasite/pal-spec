# PAL Level 1 — Minimal Protocol Handler (ESP32-S3)
import json
from machine import Pin, ADC, I2C, SPI, PWM, UART
import uio

# Use UART(0) — at boot time REPL hasn't claimed it yet
uart = UART(0, 115200)

def execute(code, timeout_ms=30000):
    buf_out = uio.StringIO()
    try:
        exec(code, {
            "__builtins__": __builtins__,
            "Pin": Pin, "ADC": ADC, "I2C": I2C,
            "SPI": SPI, "PWM": PWM, "UART": UART,
            "print": lambda *a, **k: buf_out.write(" ".join(str(x) for x in a) + "\r\n"),
        })
        return {
            "stdout": buf_out.getvalue(),
            "stderr": "",
            "error": False
        }
    except Exception as e:
        return {
            "stdout": buf_out.getvalue(),
            "stderr": str(e),
            "error": True
        }

def main():
    uart.write("PAL v1.0 ready\r\n")
    buf = b""
    while True:
        if uart.any():
            buf += uart.read()
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                try:
                    msg = json.loads(line.decode())
                    result = execute(msg.get("code", ""), msg.get("timeout_ms", 30000))
                    result["id"] = msg.get("id", "")
                    result["type"] = "result"
                    result["version"] = "1"
                    uart.write(json.dumps(result) + "\r\n")
                except Exception as e:
                    err = {"version": "1", "id": "", "type": "result", "error": True, "stderr": str(e)}
                    uart.write(json.dumps(err) + "\r\n")

main()
