import os
import subprocess
import sys

def check_python_version():
    if sys.version_info < (3, 8):
        print("Python 3.8 or higher is required")
        sys.exit(1)

def create_directories():
    directories = ['src', 'tests', 'logs', 'config']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def install_requirements():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Successfully installed requirements")
    except subprocess.CalledProcessError:
        print("Failed to install requirements")
        sys.exit(1)

def setup_gpio():
    try:
        import RPi.GPIO as GPIO
        GPIO.setwarnings(False)
        GPIO.cleanup()
        print("GPIO setup completed")
    except ImportError:
        print("Warning: RPi.GPIO not available. Running in development mode.")

def main():
    print("Starting installation...")
    check_python_version()
    create_directories()
    install_requirements()
    setup_gpio()
    print("Installation completed successfully")

if __name__ == "__main__":
    main()

# To run the complete system:

# 1. Run the installation script:
# ```bash
# python install.py
# ```

# 2. Run the tests:
# ```bash
# python -m pytest tests/system_tests.py
# ```

# 3. Start the application:
# ```bash
# python main2.py
# ```

# Additional Notes:
# - Make sure to run the GPIO setup in development mode if not running on a Raspberry Pi
# - The system requires proper permissions to access the camera and GPIO pins
# - Configure MongoDB connection details in a separate configuration file for security
# - Regular backup of logs and attendance data is recommended

# Directory structure after complete setup:
# ```
# afterfall_system/
# ├── main2.py
# ├── install.py
# ├── requirements.txt
# ├── src/
# │   ├── __init__.py
# │   ├── DoorLockController.py
# │   ├── EnhancedAntiSpoofing.py
# │   └── FaceRecognitionAttendance2.py
# ├── tests/
# │   ├── __init__.py
# │   └── system_tests.py
# ├── config/
# │   ├── __init__.py
# │   └── logging_config.py
# └── logs/
#     ├── anti_spoofing.log
#     ├── door_lock.log
#     ├── main.log
#     └── door_status.json
# ```

# Would you like me to provide more details about any specific component or explain how to test specific features of the system?