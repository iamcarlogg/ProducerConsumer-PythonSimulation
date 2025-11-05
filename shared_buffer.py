import threading 
from collections import deque 

class SharedBuffer:
    def __init__(self, capacity, log_callback):
        self.buffer = deque()
        self.capacity = capacity
        self.lock = threading.Lock()
        self.not_full = threading.Condition(self.lock)
        self.not_empty = threading.Condition(self.lock)
        self.log_callback = log_callback
    
    def produce(self, item, producer_name):
        with self.not_full:
        #wait while buffer is not full
            while len(self.buffer) >= self.capacity:
                self.log(f"{producer_name} waiting... Buffer is FULL")
                self.not_full.wait()
        # Add item to buffer
            self.buffer.append(item)
            self.log(f"{producer_name} produced: {item} | Buffer size: {len(self.buffer)}")
            
            # Notify waiting consumers
            self.not_empty.notify()

    def consume(self, consumer_name):
        with self.not_empty:
            while len(self.buffer) == 0:
                self.log(f"{consumer_name} waiting... Buffer is EMPTY")
                self.not_empty.wait()
            item = self.buffer.popleft()
            self.log(f"{consumer_name} consumed: {item} | Buffer size: {len(self.buffer)}")
            # Notify waiting producers
            self.not_full.notify()
            return item
        
    def get_size(self):
        with self.lock:
            return len(self.buffer)
    def get_capacity(self):
        return self.capacity
    def log(self, message):
        if self.log_callback:
            self.log_callback(message)