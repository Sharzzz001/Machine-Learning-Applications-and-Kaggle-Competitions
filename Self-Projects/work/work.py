import time
from datetime import datetime
import sys
import traceback
import psutil  # Requires `psutil` package for memory/CPU tracking

class Main:
    def __init__(self, userid):
        self.userid = userid

    # Logging decorator as a method in the class
    def log_user_activity(func):
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cpu_before = psutil.cpu_percent()
            mem_before = psutil.virtual_memory().percent

            try:
                # Execute the function
                result = func(self, *args, **kwargs)
                status = "Success"
            except Exception as e:
                result = None
                status = f"Error: {str(e)}"
                # Optional: log the traceback
                error_trace = traceback.format_exc()
            finally:
                # Log after function completes or if an error occurs
                end_time = time.time()
                cpu_after = psutil.cpu_percent()
                mem_after = psutil.virtual_memory().percent
                with open("user_activity_log.txt", "a") as log_file:
                    log_file.write(
                        f"User: {self.userid}, Function: {func.__name__}, "
                        f"Execution Time: {end_time - start_time:.2f} seconds, "
                        f"Date and Time: {execution_time}, Status: {status}, "
                        f"Args: {args}, Kwargs: {kwargs}, "
                        f"Return Value: {result}, "
                        f"CPU Usage (Before/After): {cpu_before}%/{cpu_after}%, "
                        f"Memory Usage (Before/After): {mem_before}%/{mem_after}%\n"
                    )
                    if status != "Success":
                        log_file.write(f"Error Traceback:\n{error_trace}\n")

            return result
        return wrapper

    @log_user_activity
    def process(self):
        print("Running main process...")
        # Call the subprocess
        sub = self.SubProcess(self.userid)
        sub.subprocess()

    class SubProcess:
        def __init__(self, userid):
            self.userid = userid

        @Main.log_user_activity
        def subprocess(self):
            print("Running subprocess...")
            # Simulate some work
            time.sleep(1)
            return "Subprocess result"

# Usage
user = Main("User123")
user.process()