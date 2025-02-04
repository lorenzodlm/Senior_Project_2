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
    threading.Thread(target=closeDoor(), daemon=True).start()

def closeDoor():
    time.sleep(5)
    print("Py: Closing the door")
    arduino.write(b'closeDoor')  

def delayed_close():
    """Wait 5 seconds, then close the door"""
    time.sleep(5)  
    closeDoor()


