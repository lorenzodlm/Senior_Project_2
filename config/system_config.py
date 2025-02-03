import json
import os
import logging
from pathlib import Path

class SystemConfig:
    def __init__(self, config_file='config/settings.json'):
        self.config_file = config_file
        self.logger = logging.getLogger('system_config')
        self.default_config = {
            'hardware': {
                'lock_pin': 18,
                'sensor_pin': 23,
                'emergency_pin': 24,
                'camera_index': 0,
                'camera_resolution': (640, 480)
            },
            'security': {
                'max_failed_attempts': 3,
                'lockout_duration': 300,
                'unlock_duration': 5,
                'emergency_timeout': 300,
                'face_detection_threshold': 0.6,
                'blink_threshold': 0.25,
                'motion_threshold': 30
            },
            'database': {
                'mongo_uri': 'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/',
                'database_name': 'afterfall',
                'collection_name': 'attendances'
            },
            'paths': {
                'dataset_path': 'data/dataset_faces',
                'logs_path': 'logs',
                'temp_path': 'temp'
            },
            'interface': {
                'window_size': (780, 450),
                'theme': 'dark-blue',
                'appearance_mode': 'System'
            }
        }
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with default config to ensure all fields exist
                    return self.merge_configs(self.default_config, loaded_config)
            else:
                self.save_config(self.default_config)
                return self.default_config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self.default_config

    def save_config(self, config):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    @staticmethod
    def merge_configs(default, custom):
        """Merge custom config with default config"""
        merged = default.copy()
        for key, value in custom.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = SystemConfig.merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def update_config(self, section, key, value):
        """Update specific configuration value"""
        try:
            if section in self.config and key in self.config[section]:
                self.config[section][key] = value
                self.save_config(self.config)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
            return False

    def get_value(self, section, key):
        """Get specific configuration value"""
        try:
            return self.config[section][key]
        except KeyError:
            return None

    def verify_paths(self):
        """Verify and create necessary directories"""
        try:
            for path_key, path_value in self.config['paths'].items():
                Path(path_value).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Error verifying paths: {e}")
            return False

# And now the system monitoring utility:

<antArtifact identifier="system-monitor" type="application/vnd.ant.code" language="python" title="utils/system_monitor.py">
import psutil
import time
import logging
from datetime import datetime
import json
import threading

class SystemMonitor:
    def __init__(self, config):
        self.logger = logging.getLogger('system_monitor')
        self.config = config
        self.monitoring = False
        self.monitor_thread = None
        self.stats = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': None,
            'camera_status': False,
            'door_status': None,
            'system_uptime': 0,
            'last_update': None
        }

    def start_monitoring(self):
        """Start system monitoring in a separate thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.logger.info("System monitoring started")

    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("System monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._update_stats()
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

    def _update_stats(self):
        """Update system statistics"""
        try:
            # Update CPU usage
            self.stats['cpu_usage'].append(psutil.cpu_percent())
            if len(self.stats['cpu_usage']) > 60:  # Keep last 5 minutes
                self.stats['cpu_usage'].pop(0)

            # Update memory usage
            memory = psutil.virtual_memory()
            self.stats['memory_usage'].append(memory.percent)
            if len(self.stats['memory_usage']) > 60:
                self.stats['memory_usage'].pop(0)

            # Update disk usage
            disk = psutil.disk_usage('/')
            self.stats['disk_usage'] = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }

            # Update system uptime
            self.stats['system_uptime'] = time.time() - psutil.boot_time()

            # Update timestamp
            self.stats['last_update'] = datetime.now().isoformat()

            # Save stats to file
            self._save_stats()

        except Exception as e:
            self.logger.error(f"Error updating system stats: {e}")

    def _save_stats(self):
        """Save statistics to file"""
        try:
            stats_file = f"{self.config.get_value('paths', 'logs_path')}/system_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving stats: {e}")

    def get_system_health(self):
        """Get current system health status"""
        try:
            cpu_avg = sum(self.stats['cpu_usage'][-5:]) / 5 if self.stats['cpu_usage'] else 0
            mem_avg = sum(self.stats['memory_usage'][-5:]) / 5 if self.stats['memory_usage'] else 0
            
            health_status = {
                'status': 'healthy',
                'warnings': [],
                'cpu_status': 'normal',
                'memory_status': 'normal',
                'disk_status': 'normal'
            }

            # Check CPU usage
            if cpu_avg > 90:
                health_status['status'] = 'critical'
                health_status['cpu_status'] = 'critical'
                health_status['warnings'].append('Critical CPU usage')
            elif cpu_avg > 70:
                health_status['status'] = 'warning'
                health_status['cpu_status'] = 'warning'
                health_status['warnings'].append('High CPU usage')

            # Check memory usage
            if mem_avg > 90:
                health_status['status'] = 'critical'
                health_status['memory_status'] = 'critical'
                health_status['warnings'].append('Critical memory usage')
            elif mem_avg > 70:
                health_status['status'] = 'warning'
                health_status['memory_status'] = 'warning'
                health_status['warnings'].append('High memory usage')

            # Check disk space
            if self.stats['disk_usage'] and self.stats['disk_usage']['percent'] > 90:
                health_status['status'] = 'critical'
                health_status['disk_status'] = 'critical'
                health_status['warnings'].append('Critical disk space')
            elif self.stats['disk_usage'] and self.stats['disk_usage']['percent'] > 70:
                health_status['status'] = 'warning'
                health_status['disk_status'] = 'warning'
                health_status['warnings'].append('Low disk space')

            return health_status

        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {'status': 'error', 'warnings': [str(e)]}

    def get_performance_report(self):
        """Generate a detailed performance report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_uptime': self.stats['system_uptime'],
                'cpu_usage': {
                    'current': self.stats['cpu_usage'][-1] if self.stats['cpu_usage'] else 0,
                    'average': sum(self.stats['cpu_usage']) / len(self.stats['cpu_usage']) if self.stats['cpu_usage'] else 0,
                    'peak': max(self.stats['cpu_usage']) if self.stats['cpu_usage'] else 0
                },
                'memory_usage': {
                    'current': self.stats['memory_usage'][-1] if self.stats['memory_usage'] else 0,
                    'average': sum(self.stats['memory_usage']) / len(self.stats['memory_usage']) if self.stats['memory_usage'] else 0,
                    'peak': max(self.stats['memory_usage']) if self.stats['memory_usage'] else 0
                },
                'disk_usage': self.stats['disk_usage'],
                'health_status': self.get_system_health()
            }
            return report
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return None

# These files add:

# 1. System Configuration:
#    - Centralized configuration management
#    - Default settings for all components
#    - Configuration file handling
#    - Path verification and creation

# 2. System Monitoring:
#    - Real-time system resource monitoring
#    - Health status checking
#    - Performance reporting
#    - Automated alerts for system issues

# To use these components:

# 1. Initialize the configuration:
# ```python
# from config.system_config import SystemConfig
# config = SystemConfig()
# ```

# 2. Start system monitoring:
# ```python
# from utils.system_monitor import SystemMonitor
# monitor = SystemMonitor(config)
# monitor.start_monitoring()
# ```

# This completes all the auxiliary files needed for the enhanced system. Would you like me to explain how to integrate these components with the main application or provide additional implementation details?