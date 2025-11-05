import threading
import time

class Producer:
    def __init__(self, buffer, name, production_delay, status_callback):
        self.buffer = buffer
        self.name = name
        self.production_delay = production_delay
        self.status_callback = status_callback
        self.running = False
        self.thread = None
        self.item_counter = 0
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
    
    def run(self):
        try:
            while self.running:
                # Produce an item
                item = self.produce_item()
                
                # Update status
                self.update_status(f"Producing item: {item}")
                
                # Add to buffer
                self.buffer.produce(item, self.name)
                
                # Update status
                self.update_status("Idle")
                
                # Simulate production time
                time.sleep(self.production_delay)
        except Exception as e:
            self.update_status(f"Error: {e}")
    
    def produce_item(self):
        self.item_counter += 1
        return f"{self.name[9:]}-{self.item_counter}"  # Returns "1-1", "1-2", "2-1", "2-2"
    
    def update_status(self, status):
        if self.status_callback:
            self.status_callback(f"{self.name}: {status}")
    
    def stop(self):
        self.running = False
