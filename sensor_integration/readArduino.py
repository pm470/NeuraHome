import serial
import time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(2)  # wait for Arduino to reset

while True:
    line = ser.readline().decode('utf-8').rstrip()
    if line:
        print("Received:", line)
