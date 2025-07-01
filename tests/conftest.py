import sys
import os

# This adds the project root directory to the Python path.
# It allows tests to import modules from the 'app' directory as if they were run from the root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))