"""Bad Apple with button trigger — press GPIO8 to start"""
from machine import Pin, SoftSPI, I2C
import ssd1306, time

cs=Pin(14,Pin.OUT,value=1)
spi=SoftSPI(baudrate=8_000_000,sck=Pin(12),mosi=Pin(11),miso=Pin(13))
i2c=I2C(0,scl=Pin(7),sda=Pin(6),freq=1_000_000)
oled=ssd1306.SSD1306_I2C(128,64,i2c)
led=Pin(21,Pin.OUT)
btn=Pin(8,Pin.IN,Pin.PULL_DOWN)
TF=5478

def w25_rd(addr,n):
    cs.value(0);spi.write(bytes([0x03,addr>>16&0xFF,addr>>8&0xFF,addr&0xFF]))
    d=spi.read(n);cs.value(1);return d

def play():
    oled.fill(0);oled.text('GO!',50,28);oled.show()
    time.sleep(0.2)
    oled.fill(0);oled.show()
    t0=time.ticks_ms()
    for f in range(TF):
        ft=time.ticks_ms()
        oled.buffer[:]=w25_rd(f*1024,1024);oled.show()
        led.value(f%12<2)
        dt=time.ticks_diff(time.ticks_ms(),ft)
        if dt<40:time.sleep_ms(40-dt)
    led.off();ms=time.ticks_diff(time.ticks_ms(),t0)
    fps=TF*1000//ms if ms else 0
    oled.fill(0);oled.text('DONE!',30,10)
    oled.text(f'{TF}f {ms}ms',10,30);oled.text(f'~{fps}fps',20,50);oled.show()

while True:
    oled.fill(0);oled.text('BAD APPLE',20,5)
    oled.text('Press btn',25,30);oled.text('to play',30,45);oled.show()
    while not btn.value():time.sleep_ms(50)
    play()
