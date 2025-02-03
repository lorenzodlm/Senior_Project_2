import serial
import time

arduino = serial.Serial('/dev/cu.usbmodemD83BDA8CFBEC2', 115200, timeout=1)
time.sleep(2)  

def openDoor():
    print("Opening the door...")
    arduino.write(b'openDoor')  
    response = arduino.readline().decode('utf-8').strip()
    print("Arduino Response:\n", response)

def closeDoor():
    print("Closing the door...")
    arduino.write(b'closeDoor')  
    response = arduino.readline().decode('utf-8').strip()  
    print("Arduino Response:\n", response)


# if __name__ == '__main__':
#     flag = True
#     while flag:
#         inp = input("Enter 'o' to open the door, 'c' to close the door, 'q' to quit: ")
#         if inp == 'o':
#             openDoor()
#         elif inp == 'c':
#             closeDoor()
#         elif inp == 'q':
#             flag = False
#         else:
#             print("Invalid input. Please try again.")
