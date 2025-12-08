import datetime

def require_key(config, key):
    if key not in config:
        raise KeyError(f"Missing required key in yaml config: '{key}'")
    return config[key]

# Class to add timestamps to logs
class TimestampedLogger:
    def __init__(self, stream, log_file):
        self.stream = stream
        self.log_file = log_file
        
    def write(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.stream.write(formatted_message)
        with open(self.log_file, "a") as f:
            f.write(formatted_message)
            
    def flush(self):
        self.stream.flush()
        
    def fileno(self):
        # Return the file descriptor of the underlying stream
        return self.stream.fileno() if hasattr(self.stream, 'fileno') else None
