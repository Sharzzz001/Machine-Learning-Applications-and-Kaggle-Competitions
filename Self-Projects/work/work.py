import time

class Main:
    def __init__(self, userid):
        self.userid = userid

    # Logging decorator as a method in the class
    def log_user_activity(func):
        def wrapper(self, *args, **kwargs):
            start_time = time.time()

            # Execute the function
            result = func(self, *args, **kwargs)

            # Log after function completes
            end_time = time.time()
            with open("user_activity_log.txt", "a") as log_file:
                log_file.write(
                    f"User: {self.userid}, Function: {func.__name__}, "
                    f"Execution Time: {end_time - start_time:.2f} seconds\n"
                )

            return result
        return wrapper

    @log_user_activity
    def some_process(self):
        # Simulate some process
        time.sleep(1)
        print("Process completed.")

    @log_user_activity
    def another_process(self):
        # Simulate another process
        time.sleep(2)
        print("Another process completed.")

# Usage
user = Main("User123")
user.some_process()
user.another_process()