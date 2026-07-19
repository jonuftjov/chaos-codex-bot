import os
import sys
from bot import run_bot

if __name__ == '__main__':
    # Ensure we are in the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the bot (which also starts Ghost API in background)
    run_bot()
