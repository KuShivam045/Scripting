import psutil
import logging

# Set your predefined thresholds
CPU_THRESHOLD = 80  # Percentage
MEMORY_THRESHOLD = 80  # Percentage
DISK_THRESHOLD = 80  # Percentage

# Configure logging
logging.basicConfig(filename='system_monitor.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def check_cpu_usage():
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > CPU_THRESHOLD:
        logging.warning(f'High CPU usage detected: {cpu_percent}%')

def check_memory_usage():
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > MEMORY_THRESHOLD:
        logging.warning(f'High memory usage detected: {memory_percent}%')

def check_disk_space():
    disk_percent = psutil.disk_usage('/').percent
    if disk_percent > DISK_THRESHOLD:
        logging.warning(f'Low disk space detected: {disk_percent}%')

def check_running_processes():
    processes = psutil.process_iter()
    for process in processes:
        try:
            process_info = process.as_dict(attrs=['pid', 'name', 'cpu_percent', 'memory_percent'])
            if process_info['cpu_percent'] > CPU_THRESHOLD or process_info['memory_percent'] > MEMORY_THRESHOLD:
                logging.warning(f'High resource usage in process {process_info}')

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
def main():
    check_cpu_usage()
    check_memory_usage()
    check_disk_space()
    check_running_processes()
    

if __name__ == "__main__":
    while True:
        main()