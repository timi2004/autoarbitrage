import time
import subprocess
import logging
import sys
import os
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_scraper():
    """
    Runs the arb_scraper.py script.
    """
    try:
        logger.info("Starting arb_scraper.py...")
        # Run the arb_scraper.py script
        subprocess.run(["python", "arb_scraper.py"], check=True)
        logger.info("arb_scraper.py completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while running arb_scraper.py: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
def run_file():
    """
    Runs the f.py script.
    """
    try:
        logger.info("Starting f.py...")
        # Run the arb_calc.py script
        subprocess.run(["python", "f.py"], check=True)
        logger.info("f.py completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while running f.py: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    logger.info("=== Starting Arb Scraper Runner ===")
 # Run the scraper
    run_scraper()
    run_file()
            
            
           