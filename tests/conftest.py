import sys
import os

# Add the project root directory to the Python path
# This allows tests to import modules from the 'src' directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# You can add other test-wide fixtures or hooks here if needed in the future 