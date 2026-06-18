import os
import sys
import re
import tkinter as tk
from tkinter import filedialog
from send2trash import send2trash

# Enable ANSI colors for Windows 10/11 console
if os.name == 'nt':
    os.system('')
    
# ==========================================
# SET TERMINAL TAB TITLE
# ==========================================
APP_TITLE = "Clone Hero No Part Deleter"
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetConsoleTitleW(APP_TITLE)
else:
    sys.stdout.write(f'\033]0;{APP_TITLE}\007')
    sys.stdout.flush()

# ==========================================
# CONFIGURATION & FIRST RUN SETUP
# ==========================================
CONFIG_FILE = "CH_Settings.txt"
songs_directory = None

# 1. Try to read the directory from the config file if it exists
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        lines = [line for line in f if line.strip() and not line.strip().startswith('#')]
        if lines:
            songs_directory = lines[0].strip()

# 2. Check if the directory we found actually exists
is_valid_dir = songs_directory and os.path.isdir(songs_directory)

if is_valid_dir:
    print(f"\033[36mLoaded Songs directory from {CONFIG_FILE}:\033[0m")
    print(f"\033[90m{songs_directory}\033[0m\n")

# 3. If missing or invalid, prompt the user with the modern GUI
if not is_valid_dir:
    print("\033[36mFirst time setup: Please select your Clone Hero 'songs' folder from the popup window...\033[0m")
    
    # Initialize tkinter and hide the main background window
    root = tk.Tk()
    root.withdraw()
    # Force the dialog to pop up in front of the console
    root.attributes('-topmost', True) 
    
    songs_directory = filedialog.askdirectory(title="Select your Clone Hero 'songs' folder")
    
    if not songs_directory:
        print("\n\033[31mFolder selection cancelled. Exiting.\033[0m")
        input("Press Enter to exit...")
        exit()

    # Normalize path slashes for Windows
    songs_directory = os.path.normpath(songs_directory)

    # 4. Generate the config file for Notepad editing later
    config_template = f"""# Clone Hero Batch-Deleter Configuration
# You can safely edit the path below using Notepad.
# Just make sure it points to your actual Clone Hero Songs directory.

{songs_directory}
"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(config_template)
    print(f"\033[32mSaved! You can change this path anytime by editing {CONFIG_FILE} in Notepad.\033[0m\n")

# Assign the validated directory to your original variable
SONGS_DIR = songs_directory

# Set to False once you are ready to actually move the folders to the Recycle Bin
DRY_RUN = False  

# ==========================================
# PATTERNS TO KEEP
# ==========================================
# If a song has AT LEAST ONE of these, it will be kept. 
# If it has none of these, it goes to the trash.

# .chart files use plain text brackets
CHART_PARTS_TO_KEEP = [
    "Single]",        # Lead Guitar
    "DoubleGuitar]",  # Co-op Guitar
    "DoubleBass]",    # Bass
    "DoubleRhythm]",  # Rhythm
    "Keyboard]"       # Keys
]

# .mid files use track names. Using negative lookahead to ignore 6-fret (GHL)
MID_REGEX_TO_KEEP = [
    rb"PART GUITAR(?!\sGHL)",
    rb"PART BASS(?!\sGHL)",
    rb"PART RHYTHM(?!\sGHL)",
    rb"PART KEYS",
    rb"T1 GEMS"       # Phase Shift fallback for Guitar
]

def has_required_instruments(folder_path):
    """Returns True if Guitar, Bass, Rhythm, or Keys are found."""
    for file in os.listdir(folder_path):
        file_lower = file.lower()
        file_path = os.path.join(folder_path, file)
        
        # Check .chart files
        if file_lower.endswith('.chart'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if any(part in content for part in CHART_PARTS_TO_KEEP):
                        return True
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                
        # Check .mid / .midi files
        elif file_lower.endswith(('.mid', '.midi')):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    for pattern in MID_REGEX_TO_KEEP:
                        if re.search(pattern, content):
                            return True
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    return False

def clean_songs(songs_directory):
    folders_to_trash = []
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(songs_directory):
        # Identify a song folder
        is_song_folder = any(f.lower() in ['song.ini', 'notes.chart', 'notes.mid'] for f in files)
        
        if is_song_folder:
            # If it DOES NOT have guitar, bass, rhythm, or keys, flag it for deletion
            if not has_required_instruments(root):
                folders_to_trash.append(root)
            
            # Stop os.walk from searching subfolders inside this specific song folder
            dirs[:] = []
                
    if not folders_to_trash:
        print("\033[32mAll songs have Guitar, Bass, Rhythm, or Keys. Nothing to delete!\033[0m")
        return

    print(f"\033[33mFound {len(folders_to_trash)} songs missing Guitar, Bass, Rhythm, or Keys.\033[0m")
    print("-" * 50)
    
    for folder in folders_to_trash:
        if DRY_RUN:
            print(f"\033[36m[DRY RUN] Would delete:\033[0m {os.path.basename(folder)}")
        else:
            print(f"\033[31mMoving to Recycle Bin:\033[0m {os.path.basename(folder)}")
            try:
                send2trash(folder)
            except Exception as e:
                print(f"Failed to delete {folder}: {e}")

    print("-" * 50)
    if DRY_RUN:
        print("Dry run complete. No files were actually moved.")
        print("To actually delete files, change DRY_RUN = False in the script.")
    else:
        print("\033[35mCleanup complete! Check your Recycle Bin if you need to restore anything.\033[0m")

if __name__ == "__main__":
    # Print the startup message immediately when the script runs
    print("Clone Hero No Part Deleter v1.0.1 initialized...\n") 
    
    if not os.path.exists(SONGS_DIR):
        print(f"\033[31mError: The directory '{SONGS_DIR}' does not exist.\033[0m")
    else:
        clean_songs(SONGS_DIR)
        
    # This prevents the window from closing instantly when double-clicked
    print("\n")
    input("Press Enter to exit...")