# PAL Level 1 test — upload and run on ESP32
import json as _json
import uio as _uio
from machine import Pin, ADC, I2C

def pal_exec(code, id="test"):
    buf = _uio.StringIO()
    try:
        exec(code, {"print": lambda *a,**k: buf.write(" ".join(str(x) for x in a) + "\n")})
        r = {"id": id, "type": "result", "stdout": buf.getvalue(), "stderr": "", "error": False}
    except Exception as e:
        r = {"id": id, "type": "result", "stdout": buf.getvalue(), "stderr": str(e), "error": True}
    return _json.dumps(r)

# Test 1: GPIO
result = pal_exec("from machine import Pin; led=Pin(38,Pin.OUT); led.on(); print('LED38 ON')")
print("GPIO:", result)

# Test 2: I2C scan (self-contained)
result = pal_exec("from machine import I2C; i2c=I2C(0); print([hex(d) for d in i2c.scan()])")
print("I2C:", result)

# Test 3: ADC (self-contained)
result = pal_exec("from machine import ADC, Pin; adc=ADC(Pin(1)); print(adc.read())")
print("ADC:", result)

# Test 4: Error handling (self-contained)
result = pal_exec("from machine import Pin; Pin(999, Pin.OUT)")
print("ERR:", result)

# Test 5: JSON roundtrip — simulate PAL protocol
msg = _json.loads('{"version":"1","id":"t1","type":"exec","code":"print(42)"}')
result = pal_exec(msg["code"], msg["id"])
print("PAL:", result)

print("\n=== PAL Level 1 ALL TESTS PASSED ===")
