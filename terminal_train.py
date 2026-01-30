import sys
import os

# Fix path to include src if running from src or parent
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from core.brain_manager import BrainManager
from core.headless_trainer import HeadlessTrainer

def main():
    if len(sys.argv) < 2:
        print("Usage: python terminal_train.py \"<folder_path>\"")
        print("Error: Missing folder path argument.")
        return

    folder_path = sys.argv[1].strip('"').strip("'")
    
    if not os.path.isdir(folder_path):
        print(f"Error: Directory not found: {folder_path}")
        return

    print("Initializing BrainManager and loading brains...")
    # Initialize Manager
    bm = BrainManager()
    
    # Ensure brains are loaded. 
    # BrainManager.__init__ usually initializes empty brains or loads from default paths.
    # We should verify if we need to call specific load methods.
    # Based on codebase knowledge, __init__ sets up the objects. 
    # If they exist on disk, RedCrecimientoInfinito might need explicit loading 
    # OR it loads in __init__. Let's assume standard behavior but force a check logic if needed.
    # For now, we trust BrainManager handling.
    
    print(f"Target Folder: {folder_path}")
    
    # Create Headless Trainer wrapper
    trainer = HeadlessTrainer(bm)
    
    # Run Job
    # This will block until finished or ESC is pressed
    trainer.run_job(bm.train_from_text_folder_gpu, folder_path=folder_path)

if __name__ == "__main__":
    main()
