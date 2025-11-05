import threading
import time

class Consumer:
    def __init__(self, buffer, name, consumption_delay, status_callback):
        self.buffer = buffer
        self.name = name
        self.consumption_delay = consumption_delay
        self.status_callback = status_callback
        self.running = False
        self.thread = None
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
    
    def run(self):
        try:
            while self.running:
                # Update status
                self.update_status("Requesting item...")
                
                # Consume from buffer
                item = self.buffer.consume(self.name)
                
                # Update status
                self.update_status(f"Consuming item: {item}")
                
                # Simulate consumption time
                time.sleep(self.consumption_delay)
                
                # Update status
                self.update_status("Idle")
        except Exception as e:
            self.update_status(f"Error: {e}")
    
    def update_status(self, status):
        if self.status_callback:
            self.status_callback(f"{self.name}: {status}")
    
    def stop(self):
        self.running = False
