"""
File Organization Check Script

This script checks the organization of files in the UIAPP directory and ensures that all necessary files are present.
"""

import os
import sys

# Define the expected files
EXPECTED_FILES = {
    # Core modules
    "simulation_core.py": "Core simulation functionality",
    "data_processor.py": "Data processing functionality",
    "ml_analyzer.py": "Machine learning functionality",
    "visualization.py": "Visualization functionality",
    
    # UI modules
    "main_app.py": "Main application",
    "simulation_tab.py": "Simulation tab UI",
    "analysis_tab.py": "Analysis tab UI",
    "ml_tab.py": "Machine learning tab UI",
    "data_export_tab.py": "Data export tab UI",
    
    # Documentation
    "README.md": "Project overview",
    "user_guide_ja.md": "Japanese user guide",
    "INSTALL.md": "Installation guide",
    
    # Package files
    "requirements.txt": "Dependencies list",
    "setup.py": "Installation script",
    
    # Test files
    "test_core_functionality.py": "Core functionality test script"
}

# Define expected directories
EXPECTED_DIRS = [
    "results",  # For simulation results
    "ml_results",  # For machine learning results
    "test_results"  # For test results
]

def check_files():
    """Check if all expected files are present."""
    print("Checking files...")
    
    missing_files = []
    
    for filename, description in EXPECTED_FILES.items():
        if not os.path.isfile(filename):
            missing_files.append(filename)
        else:
            print(f"✓ {filename} - {description}")
    
    if missing_files:
        print("\nMissing files:")
        for filename in missing_files:
            print(f"✗ {filename} - {EXPECTED_FILES[filename]}")
    else:
        print("\nAll expected files are present.")
    
    return len(missing_files) == 0

def check_directories():
    """Check if all expected directories are present and create them if not."""
    print("\nChecking directories...")
    
    for dirname in EXPECTED_DIRS:
        if not os.path.isdir(dirname):
            print(f"Creating directory: {dirname}")
            os.makedirs(dirname, exist_ok=True)
        else:
            print(f"✓ {dirname} directory exists")
    
    print("\nAll expected directories are present.")
    return True

def main():
    """Main function."""
    print("=== File Organization Check ===")
    
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    print(f"Working directory: {os.getcwd()}")
    
    # Check files
    files_ok = check_files()
    
    # Check directories
    dirs_ok = check_directories()
    
    # Print summary
    print("\n=== Summary ===")
    if files_ok and dirs_ok:
        print("All files and directories are properly organized.")
        return 0
    else:
        print("Some files or directories are missing. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())