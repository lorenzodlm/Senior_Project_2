import serial
import time
import threading


arduino = serial.Serial('/dev/cu.usbmodemD83BDA8CFBEC2', 115200, timeout=1)
time.sleep(2)  

def read_arduino_response():
    while arduino.in_waiting:  
        response = arduino.readline().decode('utf-8').strip()
        if response:
            print("Arduino Response:", response)

def openDoor():
    print("Py: Opening the door")
    arduino.write(b'openDoor') 

def closeDoor():
    print("Py: Closing the door")
    arduino.write(b'closeDoor')  


