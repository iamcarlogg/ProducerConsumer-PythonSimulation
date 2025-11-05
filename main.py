import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QProgressBar, QGroupBox, QFormLayout)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
from shared_buffer import SharedBuffer
from producer import Producer
from consumer import Consumer

class SignalEmitter(QObject):
    """Helper class to emit signals from worker threads"""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal()

class ProducerConsumerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Producer-Consumer Simulation")
        self.setGeometry(100, 100, 900, 750)
        
        self.buffer = None
        self.producers = []
        self.consumers = []
        
        # Signal emitter for thread-safe GUI updates
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.log_signal.connect(self.log_message_safe)
        self.signal_emitter.status_signal.connect(self.update_status_display)
        
        self.init_ui()
        
        # Timer for buffer updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_buffer_visualization)
        self.timer.start(100)
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Configuration Panel
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout()
        
        self.buffer_capacity_input = QLineEdit("5")
        self.buffer_capacity_input.setMaximumWidth(100)
        config_layout.addRow("Buffer Capacity:", self.buffer_capacity_input)
        
        self.num_producers_input = QLineEdit("2")
        self.num_producers_input.setMaximumWidth(100)
        config_layout.addRow("Number of Producers:", self.num_producers_input)
        
        self.num_consumers_input = QLineEdit("2")
        self.num_consumers_input.setMaximumWidth(100)
        config_layout.addRow("Number of Consumers:", self.num_consumers_input)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # Buffer Visualization
        buffer_group = QGroupBox("Buffer Status")
        buffer_layout = QVBoxLayout()
        
        self.buffer_label = QLabel("Buffer: 0 / 0")
        self.buffer_label.setAlignment(Qt.AlignCenter)
        self.buffer_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        buffer_layout.addWidget(self.buffer_label)
        
        self.buffer_progress = QProgressBar()
        self.buffer_progress.setMinimum(0)
        self.buffer_progress.setMaximum(100)
        self.buffer_progress.setValue(0)
        self.buffer_progress.setMinimumHeight(30)
        buffer_layout.addWidget(self.buffer_progress)
        
        buffer_group.setLayout(buffer_layout)
        main_layout.addWidget(buffer_group)
        
        # Status Area
        status_group = QGroupBox("Thread Status")
        status_layout = QVBoxLayout()
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        self.status_text.setStyleSheet("font-family: Arial; font-size: 11px;")
        status_layout.addWidget(self.status_text)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # Log Area
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: Monaco, Menlo, monospace; font-size: 10px;")
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Control Panel
        control_layout = QHBoxLayout()
        control_layout.addStretch()
        
        self.start_button = QPushButton("Start Simulation")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_button.clicked.connect(self.start_simulation)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
    
    def log_message_safe(self, message):
        """Thread-safe log message handler"""
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def log_message_from_thread(self, message):
        """Called from worker threads - emits signal"""
        self.signal_emitter.log_signal.emit(message)
    
    def update_status_display(self):
        """Thread-safe status update"""
        status_text = ""
        for producer in self.producers:
            status = getattr(producer, 'last_status', 'Not started')
            status_text += f"<span style='color: #2196F3;'>{status}</span><br>"
        for consumer in self.consumers:
            status = getattr(consumer, 'last_status', 'Not started')
            status_text += f"<span style='color: #FF9800;'>{status}</span><br>"
        
        self.status_text.setHtml(status_text)
    
    def clear_log(self):
        self.log_text.clear()
    
    def start_simulation(self):
        try:
            buffer_capacity = int(self.buffer_capacity_input.text())
            num_producers = int(self.num_producers_input.text())
            num_consumers = int(self.num_consumers_input.text())
        except ValueError:
            self.log_message_safe("Error: Please enter valid numbers")
            return
        
        # Create buffer with thread-safe logging
        self.buffer = SharedBuffer(buffer_capacity, self.log_message_from_thread)
        
        # Clear status
        self.status_text.clear()
        
        # Create producers
        for i in range(num_producers):
            def make_status_callback(p, emitter):
                def callback(status):
                    p.last_status = status
                    emitter.status_signal.emit()
                return callback
            
            producer = Producer(self.buffer, f"Producer-{i+1}", 1.0, None)
            producer.last_status = "Starting..."
            producer.status_callback = make_status_callback(producer, self.signal_emitter)
            self.producers.append(producer)
            producer.start()
        
        # Create consumers
        for i in range(num_consumers):
            def make_status_callback(c, emitter):
                def callback(status):
                    c.last_status = status
                    emitter.status_signal.emit()
                return callback
            
            consumer = Consumer(self.buffer, f"Consumer-{i+1}", 1.5, None)
            consumer.last_status = "Starting..."
            consumer.status_callback = make_status_callback(consumer, self.signal_emitter)
            self.consumers.append(consumer)
            consumer.start()
        
        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        self.log_message_safe("=== Simulation Started ===")
    
    def stop_simulation(self):
        # Stop all threads
        for producer in self.producers:
            producer.stop()
        for consumer in self.consumers:
            consumer.stop()
        
        # Clear lists
        self.producers.clear()
        self.consumers.clear()
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        self.log_message_safe("=== Simulation Stopped ===")
    
    def update_buffer_visualization(self):
        if self.buffer:
            size = self.buffer.get_size()
            capacity = self.buffer.get_capacity()
            percentage = int((size / capacity * 100)) if capacity > 0 else 0
            
            self.buffer_label.setText(f"Buffer: {size} / {capacity}")
            self.buffer_progress.setValue(percentage)
            
            # Change color based on fullness
            if percentage > 80:
                self.buffer_progress.setStyleSheet("""
                    QProgressBar {
                        border: 2px solid grey;
                        border-radius: 5px;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: #f44336;
                    }
                """)
            elif percentage > 50:
                self.buffer_progress.setStyleSheet("""
                    QProgressBar {
                        border: 2px solid grey;
                        border-radius: 5px;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: #FF9800;
                    }
                """)
            else:
                self.buffer_progress.setStyleSheet("""
                    QProgressBar {
                        border: 2px solid grey;
                        border-radius: 5px;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: #4CAF50;
                    }
                """)

def main():
    app = QApplication(sys.argv)
    window = ProducerConsumerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()