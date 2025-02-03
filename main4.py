import tkinter
import customtkinter
import os
import shutil
from src.FaceCaptureAndAugmentation import FaceCaptureAndAugmentation
from src.FaceRecognitionAttendance2 import FaceRecognitionAttendance
from config.system_config import SystemConfig
from utils.system_monitor import SystemMonitor
from pymongo import MongoClient
import certifi
import datetime
import pytz
import logging
import threading
import time

# Configure logging
logging.basicConfig(filename='logs/afterfall.log', level=logging.INFO)
logger = logging.getLogger('afterfall')

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Initialize system configuration
        self.config = SystemConfig()
        
        # Initialize system monitor
        self.system_monitor = SystemMonitor(self.config)
        self.system_monitor.start_monitoring()

        # MongoDB Configuration
        try:
            client = MongoClient(
                'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
                tlsCAFile=certifi.where()
            )
            db = client['afterfall']
            collection = db['attendances']
            logger.info("MongoDB connection established")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

        # Initialize FaceRecognitionAttendance instance
        self.face_recognition_attendance = FaceRecognitionAttendance(
            dataset_path=self.config.get_value('paths', 'dataset_path'),
            mongo_collection=collection
        )

        # Security monitoring
        self.failed_attempts = 0
        self.max_failed_attempts = self.config.get_value('security', 'max_failed_attempts')
        self.lockout_duration = self.config.get_value('security', 'lockout_duration')
        self.last_failure_time = None

        # Class-level variable to store the matched classCode
        self.matched_class_code = None

        # Configure window
        self.title("AfterFall Face Recognition")
        window_size = self.config.get_value('interface', 'window_size')
        self.geometry(f"{window_size[0]}x{window_size[1]}")

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # Create sidebar frame with widgets
        self.create_sidebar()
        
        # Create main content area
        self.create_main_content()

        # Initially hide all delete widgets
        self.hide_all_delete_widgets()

        # Set default values
        self.appearance_mode_optionemenu.set(
            self.config.get_value('interface', 'appearance_mode')
        )
        
        # Start status monitoring thread
        self.status_thread = threading.Thread(target=self.monitor_system_status, daemon=True)
        self.status_thread.start()

        # Set up periodic health checks
        self.schedule_health_check()

        # Welcome message
        self.textbox.insert("0.0", "Hello, welcome to our Assumption University Senior Project 1\n\n"
                                "Contributors (AfterFall team):\n"
                                "- LORENZO MARTINS DALMEIDA\n"
                                "- ARCHIT CHANGCHREONKUL\n"
                                "- KRITSADA KRUAPAT\n\n"
                                "Advisor of this project:\n"
                                "- DOBRI ATANASSOV BATOVSKI\n")

    def create_sidebar(self):
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        # Logo
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame, 
            text="AfterFall", 
            font=customtkinter.CTkFont(size=40, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Face Recognition Button
        self.display_classes_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Face Recognition",
            command=self.show_display_classes_button,
            fg_color="blue",
            hover_color="darkblue"
        )
        self.display_classes_button.grid(row=1, column=0, padx=20, pady=10)

        # Attendance Button
        self.display_attendance_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Attendance",
            command=self.display_attendance,
            fg_color="blue",
            hover_color="darkblue"
        )
        self.display_attendance_button.grid(row=2, column=0, padx=20, pady=10)

        # Face Record Button
        self.display_folders_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Face Record",
            command=self.display_user_folders,
            fg_color="blue",
            hover_color="darkblue"
        )
        self.display_folders_button.grid(row=3, column=0, padx=20, pady=10)

        # System Health Button
        self.health_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="System Health",
            command=self.check_system_health,
            fg_color="blue",
            hover_color="darkblue"
        )
        self.health_button.grid(row=4, column=0, padx=20, pady=10)

        # Appearance Mode Controls
        self.appearance_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, 
            text="Appearance Mode:", 
            anchor="w"
        )
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))

    def create_main_content(self):
        # Create textbox for displaying data
        self.textbox = customtkinter.CTkTextbox(self, width=250)
        self.textbox.grid(row=0, column=1, padx=(20, 20), pady=(20, 10), sticky="nsew")

        # Create entry for user ID
        self.user_entry = customtkinter.CTkEntry(self, placeholder_text="Enter user ID")
        self.user_entry.grid(row=1, column=1, padx=(20, 20), pady=(10, 5), sticky="ew")

        # Create button for adding user
        self.add_user_button = customtkinter.CTkButton(
            self,
            text="Add user",
            command=self.add_user_folder,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.add_user_button.grid(row=2, column=1, padx=(20, 20), pady=(5, 5), sticky="ew")

        # Create button for deleting user
        self.delete_user_button = customtkinter.CTkButton(
            self,
            text="Delete User",
            command=self.delete_user_folder,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_user_button.grid(row=3, column=1, padx=(20, 20), pady=(5, 20), sticky="ew")

        # Create button for deleting attendance records
        self.delete_attendance_button = customtkinter.CTkButton(
            self,
            text="Delete Attendance",
            command=self.delete_attendance_records,
            fg_color="red",
            hover_color="darkred"
        )

        # Class-related widgets
        self.class_id_entry = customtkinter.CTkEntry(
            self, 
            placeholder_text="Enter Class ID to Check"
        )
        self.class_id_entry.grid_forget()  # Initially hide

        self.check_class_button = customtkinter.CTkButton(
            self,
            text="Check Class ID",
            command=self.check_class_id_match,
            fg_color="blue",
            hover_color="darkblue"
        )
        self.check_class_button.grid_forget()  # Initially hide

    def monitor_system_status(self):
        while True:
            try:
                health_status = self.system_monitor.get_system_health()
                if health_status['status'] != 'healthy':
                    self.show_health_warning(health_status)
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in status monitoring: {e}")
                time.sleep(60)

    def schedule_health_check(self):
        self.after(300000, self.perform_health_check)  # Every 5 minutes

    def perform_health_check(self):
        try:
            health_status = self.system_monitor.get_system_health()
            if health_status['status'] != 'healthy':
                self.show_health_warning(health_status)
            self.schedule_health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.schedule_health_check()

    def show_health_warning(self, health_status):
        warnings = "\n".join(health_status['warnings'])
        tkinter.messagebox.showwarning(
            "System Health Warning",
            f"System health issues detected:\n{warnings}"
        )

    def check_system_health(self):
        try:
            report = self.system_monitor.get_performance_report()
            if report:
                health_text = (
                    f"System Health Report:\n\n"
                    f"Status: {report['health_status']['status']}\n"
                    f"CPU Usage: {report['cpu_usage']['current']}%\n"
                    f"Memory Usage: {report['memory_usage']['current']}%\n"
                    f"Disk Usage: {report['disk_usage']['percent']}%\n"
                    f"System Uptime: {int(report['system_uptime'] / 3600)} hours\n\n"
                    f"Warnings:\n{chr(10).join(report['health_status']['warnings'])}"
                )
                self.textbox.delete("1.0", tkinter.END)
                self.textbox.insert("1.0", health_text)
            else:
                tkinter.messagebox.showerror(
                    "Error",
                    "Failed to generate system health report"
                )
        except Exception as e:
            tkinter.messagebox.showerror(
                "Error",
                f"Failed to check system health: {e}"
            )
            logger.error(f"Health check failed: {e}")

    def initialize_face_recognition(self):
        if self.check_security_timeout():
            tkinter.messagebox.showinfo(
                "Webcam Instruction",
                "Press 'q' to end the webcam."
            )

            matched_class_code = self.matched_class_code

            if matched_class_code:
                try:
                    self.face_recognition_attendance.process_video_stream(matched_class_code)
                except Exception as e:
                    self.handle_recognition_error(e)
            else:
                tkinter.messagebox.showerror("Error", "No matched class code found.")
        else:
            remaining_time = self.lockout_duration - (time.time() - self.last_failure_time)
            tkinter.messagebox.showerror(
                "Security Lockout",
                f"System is locked due to multiple failed attempts. "
                f"Please wait {int(remaining_time)} seconds."
            )

    def check_security_timeout(self):
        if self.failed_attempts >= self.max_failed_attempts:
            if time.time() - self.last_failure_time < self.lockout_duration:
                return False
            self.failed_attempts = 0
        return True

    def handle_recognition_error(self, error):
        self.failed_attempts += 1
        if self.failed_attempts >= self.max_failed_attempts:
            self.last_failure_time = time.time()
            tkinter.messagebox.showerror(
                "Security Alert",
                "Multiple authentication failures detected. System will be locked temporarily."
            )
            logger.warning("System locked due to multiple authentication failures")
        else:
            tkinter.messagebox.showerror("Error", f"Recognition failed: {str(error)}")
            logger.error(f"Recognition error: {str(error)}")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        self.hide_all_delete_widgets()
        self.config.update_config('interface', 'appearance_mode', new_appearance_mode)

    def display_attendance(self):
        try:
            # Fetch all attendance records from the MongoDB collection
            attendance_records = list(self.face_recognition_attendance.mongo_collection.find({}))

            if not attendance_records:
                self.textbox.delete("1.0", tkinter.END)
                self.textbox.insert("1.0", "No attendance records found.")
                return

            # Prepare a string to hold all the attendance data
            attendance_data = ""

            # Define the Thai timezone
            thai_timezone = pytz.timezone('Asia/Bangkok')

            # Iterate over all attendance records
            for record in attendance_records:
                user_id = record.get('UserID', 'Unknown')
                class_id = record.get('classID', 'Unknown')
                attendance_list = record.get('attendance', [])

                # Add the user and class information
                attendance_data += f"UserID: {user_id} ClassID: {class_id}\n"

                # Append each attendance timestamp
                for timestamp in attendance_list:
                    utc_time = timestamp
                    utc_time = utc_time.replace(tzinfo=pytz.utc)
                    thai_time = utc_time.astimezone(thai_timezone)
                    formatted_time = thai_time.strftime('%Y-%m-%d %H:%M:%S')
                    attendance_data += f"  - {formatted_time} (Thai Time)\n"

                attendance_data += "\n"

            self.textbox.delete("1.0", tkinter.END)
            self.textbox.insert("1.0", attendance_data)

            self.hide_all_delete_widgets()
            self.delete_attendance_button.grid(row=3, column=1, padx=(20, 20), pady=(5, 20), sticky="ew")

        except Exception as e:
            self.textbox.delete("1.0", tkinter.END)
            self.textbox.insert("1.0", f"Error retrieving attendance data: {e}")
            logger.error(f"Error displaying attendance: {e}")

    def display_user_folders(self):
        self.hide_all_delete_widgets()
        self.show_delete_user_widgets()
        folder_path = self.config.get_value('paths', 'dataset_path')

        try:
            # Fetch all users from MongoDB
            mongo_users = list(self.face_recognition_attendance.mongo_collection.find({}, {'UserID': 1, '_id': 0}))
            if not mongo_users:
                tkinter.messagebox.showinfo("Info", "No users found in MongoDB.")
                return

            folders = [f for f in os.listdir(folder_path) if f != ".DS_Store"]
            mongo_user_ids = [user.get("UserID") for user in mongo_users]

            user_data = "No faces record on this local device, please add the green button below\n"

            for user_id in mongo_user_ids:
                if user_id not in folders:
                    user_data += f"UserID {user_id}: No faces record\n"

            user_data += "\nAll users:\n"
            for user_id in mongo_user_ids:
                user_data += f"UserID {user_id}\n"

            self.textbox.delete("1.0", tkinter.END)
            self.textbox.insert("1.0", user_data)

        except FileNotFoundError:
            tkinter.messagebox.showerror("Error", f"The folder path '{folder_path}' was not found.")
            logger.error(f"Folder not found: {folder_path}")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred: {str(e)}")
            logger.error(f"Error displaying user folders: {e}")

    def add_user_folder(self):
        user_id = self.user_entry.get()

        if not user_id:
            tkinter.messagebox.showerror("Error", "Please enter a user ID to add.")
            return

        try:
            face_capture = FaceCaptureAndAugmentation(user_id=user_id)
            face_capture.capture_faces()
            face_capture.augment_faces()

            tkinter.messagebox.showinfo("Success", 
                f"User with ID '{user_id}' has been added with captured and augmented faces.")
            self.display_user_folders()
            logger.info(f"User added successfully: {user_id}")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred while adding the user: {str(e)}")
            logger.error(f"Error adding user: {e}")

    def delete_user_folder(self):
        user_id = self.user_entry.get()

        if not user_id:
            tkinter.messagebox.showerror("Error", "Please enter a user ID to delete.")
            return

        target_folder = os.path.join(self.config.get_value('paths', 'dataset_path'), user_id)

        if os.path.exists(target_folder):
            try:
                shutil.rmtree(target_folder)
                tkinter.messagebox.showinfo("Success", f"User with ID '{user_id}' has been deleted.")
                self.display_user_folders()
                logger.info(f"User deleted successfully: {user_id}")
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"An error occurred while deleting the user: {str(e)}")
                logger.error(f"Error deleting user: {e}")
        else:
            tkinter.messagebox.showerror("Error", f"The user with ID '{user_id}' does not exist.")

    def delete_attendance_records(self):
        try:
            result = self.face_recognition_attendance.mongo_collection.delete_many({})
            if result.deleted_count > 0:
                tkinter.messagebox.showinfo("Success", "Attendance data deleted from MongoDB.")
                logger.info(f"Deleted {result.deleted_count} attendance records")
            else:
                tkinter.messagebox.showinfo("Info", "No data to delete in MongoDB.")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred while deleting attendance data: {str(e)}")
            logger.error(f"Error deleting attendance records: {e}")

    def show_display_classes_button(self):
        self.hide_all_delete_widgets()

        try:
            mongo_data = list(self.face_recognition_attendance.mongo_collection.find({}, {'classID': 1, '_id': 0}))

            if not mongo_data:
                tkinter.messagebox.showinfo("Info", "No classes found in MongoDB.")
                return

            class_data = "Class IDs in the Database:\n\n"
            class_ids = set()

            for record in mongo_data:
                class_id = record.get("classID", "Unknown")
                class_ids.add(class_id)

            for class_id in class_ids:
                class_data += f"Class ID: {class_id}\n"

            self.textbox.delete("1.0", tkinter.END)
            self.textbox.insert("1.0", class_data)

            self.class_id_entry.grid(row=3, column=1, padx=(20, 20), pady=(5, 5), sticky="ew")
            self.check_class_button.grid(row=4, column=1, padx=(20, 20), pady=(5, 20), sticky="ew")

        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred while fetching class IDs: {str(e)}")
            logger.error(f"Error displaying class IDs: {e}")

    def check_class_id_match(self):
        input_class_id = self.class_id_entry.get().strip()

        if not input_class_id:
            tkinter.messagebox.showinfo("Info", "Please enter a class ID.")
            return

        try:
            mongo_data = list(self.face_recognition_attendance.mongo_collection.find({}, {'classID': 1, '_id': 0}))
            class_ids = {record.get("classID", "Unknown") for record in mongo_data}

            if input_class_id in class_ids:
                self.matched_class_code = input_class_id
                tkinter.messagebox.showinfo("Match Found", 
                    f"The class ID '{self.matched_class_code}' matches a class in the database.\n"
                    "Starting webcam for face detection...")
                self.initialize_face_recognition()
            else:
                tkinter.messagebox.showinfo("No Match", 
                    f"The class ID '{input_class_id}' does not match any class in the database.")

        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred while checking class IDs: {str(e)}")
            logger.error(f"Error checking class ID: {e}")

    def show_delete_user_widgets(self):
        self.user_entry.grid(row=1, column=1, padx=(20, 20), pady=(10, 5), sticky="ew")
        self.add_user_button.grid(row=2, column=1, padx=(20, 20), pady=(5, 5), sticky="ew")
        self.delete_user_button.grid(row=3, column=1, padx=(20, 20), pady=(5, 20), sticky="ew")
        self.hide_delete_attendance_widgets()

    def show_delete_attendance_button(self):
        self.delete_attendance_button.grid(row=2, column=1, padx=(20, 20), pady=(5, 20), sticky="ew")
        self.hide_delete_user_widgets()

    def hide_delete_user_widgets(self):
        self.user_entry.grid_forget()
        self.add_user_button.grid_forget()
        self.delete_user_button.grid_forget()

    def hide_delete_attendance_widgets(self):
        self.delete_attendance_button.grid_forget()

    def hide_class_widgets(self):
        self.class_id_entry.grid_forget()
        self.check_class_button.grid_forget()

    def hide_all_delete_widgets(self):
        self.hide_delete_user_widgets()
        self.hide_delete_attendance_widgets()
        self.hide_class_widgets()

    def on_closing(self):
        """Cleanup and close the application"""
        try:
            self.system_monitor.stop_monitoring()
            logger.info("Application shutting down normally")
            self.quit()
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            self.quit()

if __name__ == "__main__":
    try:
        app = App()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except Exception as e:
        logger.critical(f"Application failed to start: {e}")
        raise