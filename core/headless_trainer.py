import sys
import termios
import tty
import select
import threading
import time
import os

class HeadlessTrainer:
    """
    Manages training sessions in the terminal without GUI.
    Handles ESC key detection for interruption.
    """
    def __init__(self, brain_manager):
        self.brain_manager = brain_manager
        self.stop_event = threading.Event()
        self.training_thread = None
        self.input_thread = None
        self.is_running = False

    def get_key(self):
        """Reads a single keypress from stdin in raw mode (Unix/Mac)"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                ch = sys.stdin.read(1)
                return ch
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def monitor_keyboard(self):
        """Background thread to detect ESC key"""
        print("\n⌨️  Monitoring keyboard... Press [ESC] to stop.")
        while self.is_running and not self.stop_event.is_set():
            key = self.get_key()
            if key == '\x1b': # ESC key code
                print("\n🛑 ESC DETECTED! Stopping training gracefully...")
                self.stop_event.set()
                break
            time.sleep(0.05)

    def run_job(self, target_function, **kwargs):
        """
        Runs a training job in headless mode.
        blocks main thread until finished or stopped.
        """
        self.stop_event.clear()
        self.is_running = True
        
        # UI Banner
        os.system('cls' if os.name == 'nt' else 'clear')
        print("="*60)
        print("   🚀 MAGI HEADLESS TRAINING MODE (M4 OPTIMIZED)   ")
        print("="*60)
        print("Running job: " + target_function.__name__)
        print("STATUS: INITIALIZING VRAM SESSION...")
        print("-" * 60)
        print("PRESS [ESC] TO STOP AND RETURN TO GUI")
        print("-" * 60)

        # Start input monitor
        self.input_thread = threading.Thread(target=self.monitor_keyboard, daemon=True)
        self.input_thread.start()

        # Run training function
        # We inject 'console_mode=True' and 'stop_event=self.stop_event'
        kwargs['console_mode'] = True
        kwargs['stop_event'] = self.stop_event
        
        try:
            target_function(**kwargs)
        except Exception as e:
            print(f"\n❌ ERROR IN HEADLESS JOB: {e}")
        finally:
            self.is_running = False
            print("\n✅ Job finished/stopped. Returning to GUI...")
            time.sleep(2) # Give user a moment to see result
