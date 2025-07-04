import asyncio
import json
import time
import subprocess
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
import sys

# Add the got.py directory to the path

from got import ArbitrageBettingSystem

class ArbitrageOpportunityManager:
    """
    Manages the arbitrage opportunity workflow:
    - Monitors arb_scraper_runner completion
    - Processes filtered opportunities
    - Executes betting via got.py
    - Handles scheduling and retries
    """
    
    def __init__(self):
        self.is_running = False
        self.arbitrage_system = ArbitrageBettingSystem()
        
        # File paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filtered_opportunities_path = os.path.join(self.base_dir, "filtered_opportunities.json")
        self.arb_scraper_runner_path = os.path.join(self.base_dir, "arb_scraper_runner.py")
        
        # Configuration
        self.max_opportunities_per_cycle = 3
        self.wait_time_minutes = 5
        self.wait_time_seconds = self.wait_time_minutes * 60
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.base_dir, 'opportunity_manager.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def switch_on(self):
        """Start the opportunity manager"""
        self.is_running = True
        self.logger.info("🟢 Arbitrage Opportunity Manager SWITCHED ON")
    
    def switch_off(self):
        """Stop the opportunity manager"""
        self.is_running = False
        self.logger.info("🔴 Arbitrage Opportunity Manager SWITCHED OFF")
    
    def is_switched_on(self) -> bool:
        """Check if the manager is currently running"""
        return self.is_running
    
    def debug_scraper_environment(self):
        """Debug the environment for the scraper"""
        self.logger.info(f"🔍 Current working directory: {os.getcwd()}")
        self.logger.info(f"🔍 Base directory: {self.base_dir}")
        self.logger.info(f"🔍 Scraper path exists: {os.path.exists(self.arb_scraper_runner_path)}")
        self.logger.info(f"🔍 Python executable: {sys.executable}")
    
    def run_arb_scraper_runner(self) -> bool:
        """
        Run the arb_scraper_runner.py script
        Returns True if successful, False otherwise
        """
        try:
            self.logger.info("🚀 Running arb_scraper_runner.py...")
            
            # Debug environment (optional - remove if not needed)
            self.debug_scraper_environment()
            
            # Run without capturing output to allow real-time interaction
            result = subprocess.run(
                ["python", "arb_scraper_runner.py"],
                cwd=self.base_dir,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                self.logger.info("✅ arb_scraper_runner.py completed successfully")
                return True
            else:
                self.logger.error(f"❌ arb_scraper_runner.py failed with return code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("⏰ arb_scraper_runner.py timed out after 1 hour")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error running arb_scraper_runner.py: {e}")
            return False
    
    def load_filtered_opportunities(self) -> List[Dict]:
        """
        Load opportunities from filtered_opportunities.json
        Returns list of opportunities or empty list if none found
        """
        try:
            if not os.path.exists(self.filtered_opportunities_path):
                self.logger.warning(f"📂 File not found: {self.filtered_opportunities_path}")
                return []
            
            with open(self.filtered_opportunities_path, 'r', encoding='utf-8') as f:
                opportunities = json.load(f)
            
            self.logger.info(f"📊 Loaded {len(opportunities)} filtered opportunities")
            return opportunities
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ JSON decode error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Error loading opportunities: {e}")
            return []
    
    def filter_required_fields(self, opportunity: Dict) -> Dict:
        """
        Extract only the required fields for got.py, ignoring miscellaneous keys
        """
        required_fields = [
            "profit", "sport", "event_time", "bookmaker1", "team1_bk1", "team2_bk1",
            "league_bk1", "bet_type_bk1", "odd_bk1", "link_bk1", "bookmaker2",
            "team1_bk2", "team2_bk2", "league_bk2", "bet_type_bk2", "odd_bk2", "link_bk2"
        ]
        
        filtered_opportunity = {}
        for field in required_fields:
            if field in opportunity:
                filtered_opportunity[field] = opportunity[field]
            else:
                self.logger.warning(f"⚠️ Missing required field: {field}")
                filtered_opportunity[field] = ""
        
        return filtered_opportunity
    
    def select_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Select up to max_opportunities_per_cycle opportunities
        If more than one opportunity exists, start with the first one
        """
        if not opportunities:
            return []
        
        # If only one opportunity, take it
        if len(opportunities) == 1:
            self.logger.info("📋 Only 1 opportunity available, selecting it")
            return [self.filter_required_fields(opportunities[0])]
        
        # If multiple opportunities, take up to max_opportunities_per_cycle starting from first
        selected_count = min(len(opportunities), self.max_opportunities_per_cycle)
        selected = opportunities[:selected_count]
        
        self.logger.info(f"📋 Selected {selected_count} opportunities out of {len(opportunities)} available")
        
        # Filter required fields for each selected opportunity
        return [self.filter_required_fields(opp) for opp in selected]
    
    async def process_opportunity(self, opportunity: Dict, index: int) -> bool:
        """
        Process a single opportunity using got.py
        Returns True if successful, False otherwise
        """
        try:
            self.logger.info(f"🎯 Processing opportunity {index + 1}:")
            self.logger.info(f"   Sport: {opportunity.get('sport', 'Unknown')}")
            self.logger.info(f"   Teams: {opportunity.get('team1_bk1', 'Unknown')} vs {opportunity.get('team2_bk1', 'Unknown')}")
            self.logger.info(f"   Bookmakers: {opportunity.get('bookmaker1', 'Unknown')} vs {opportunity.get('bookmaker2', 'Unknown')}")
            self.logger.info(f"   Profit: {opportunity.get('profit', 'Unknown')}")
            
            # Execute the arbitrage using got.py
            result = await self.arbitrage_system.execute_arbitrage(opportunity)
            
            if result.get('success', False):
                self.logger.info(f"✅ Opportunity {index + 1} processed successfully!")
                self.logger.info(f"   Arbitrage Profit: {result.get('summary', {}).get('arbitrage_profit', 'Unknown')}%")
                self.logger.info(f"   Total Stake: ${result.get('summary', {}).get('total_stake_usd', 'Unknown')} USD")
                self.logger.info(f"   BK1 Bet Placed: {result.get('summary', {}).get('bk1_bet_placed', False)}")
                self.logger.info(f"   BK2 Bet Placed: {result.get('summary', {}).get('bk2_bet_placed', False)}")
                return True
            else:
                self.logger.error(f"❌ Opportunity {index + 1} failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Unexpected error processing opportunity {index + 1}: {e}")
            return False
    
    async def process_opportunities_batch(self, opportunities: List[Dict]) -> Dict:
        """
        Process a batch of opportunities
        """
        results = {
            "total_processed": len(opportunities),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for i, opportunity in enumerate(opportunities):
            success = await self.process_opportunity(opportunity, i)
            
            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "index": i + 1,
                "success": success,
                "opportunity": opportunity
            })
            
            # Small delay between opportunities to prevent overwhelming the system
            if i < len(opportunities) - 1:  # Don't delay after the last one
                await asyncio.sleep(10)
        
        return results
    
    async def run_cycle(self) -> bool:
        """
        Run one complete cycle:
        1. Run arb_scraper_runner
        2. Check for opportunities
        3. Process opportunities if found
        4. Return True if opportunities were found and processed, False if no opportunities
        """
        if not self.is_running:
            return False
        
        self.logger.info("🔄 Starting new cycle...")
        
        # Step 1: Run arb_scraper_runner
        scraper_success = self.run_arb_scraper_runner()
        if not scraper_success:
            self.logger.warning("⚠️ Scraper run failed, but continuing to check for existing opportunities...")
        
        # Step 2: Load opportunities
        opportunities = self.load_filtered_opportunities()
        
        # Step 3: Check if opportunities exist
        if not opportunities:
            self.logger.info("📭 No opportunities found")
            return False
        
        # Step 4: Select and process opportunities
        selected_opportunities = self.select_opportunities(opportunities)
        
        if not selected_opportunities:
            self.logger.warning("⚠️ No valid opportunities selected")
            return False
        
        # Step 5: Process the selected opportunities
        self.logger.info(f"🎯 Processing {len(selected_opportunities)} opportunities...")
        results = await self.process_opportunities_batch(selected_opportunities)
        
        # Log results
        self.logger.info(f"📈 Cycle completed: {results['successful']} successful, {results['failed']} failed")
        
        return True  # Return True because we found and processed opportunities
    
    async def main_loop(self):
        """
        Main loop that runs the opportunity management workflow
        """
        self.logger.info("🚀 Starting Arbitrage Opportunity Manager main loop...")
        
        while self.is_running:
            try:
                cycle_start_time = datetime.now()
                
                # Run one cycle
                opportunities_found = await self.run_cycle()
                
                if not opportunities_found:
                    # No opportunities found, wait 5 minutes before retrying
                    self.logger.info(f"⏳ No opportunities found. Waiting {self.wait_time_minutes} minutes before next run...")
                    
                    # Wait in chunks so we can check is_running status
                    for _ in range(self.wait_time_seconds):
                        if not self.is_running:
                            break
                        await asyncio.sleep(1)
                else:
                    # Opportunities were processed, continue immediately to next cycle
                    self.logger.info("✅ Opportunities processed. Starting next cycle immediately...")
                
                cycle_duration = datetime.now() - cycle_start_time
                self.logger.info(f"⏱️ Cycle duration: {cycle_duration}")
                
            except KeyboardInterrupt:
                self.logger.info("⚠️ Keyboard interrupt received. Stopping...")
                self.switch_off()
                break
            except Exception as e:
                self.logger.error(f"❌ Unexpected error in main loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
        
        self.logger.info("🔴 Arbitrage Opportunity Manager stopped")


# Usage example and control interface
class OpportunityManagerControl:
    """Control interface for the Arbitrage Opportunity Manager"""
    
    def __init__(self):
        self.manager = ArbitrageOpportunityManager()
        self.task = None
        self.loop = None
        self.loop_thread = None
    
    def switch_on(self):
        """Start the manager in a separate thread with its own event loop"""
        if self.manager.is_switched_on():
            print("Manager is already running!")
            return
        
        import threading
        
        def run_manager():
            """Run the manager in its own event loop"""
            try:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                self.manager.switch_on()
                print("✅ Arbitrage Opportunity Manager started")
                self.loop.run_until_complete(self.manager.main_loop())
            except Exception as e:
                print(f"❌ Error in manager loop: {e}")
            finally:
                self.loop.close()
        
        # Start the manager in a separate thread
        self.loop_thread = threading.Thread(target=run_manager, daemon=True)
        self.loop_thread.start()
    
    def switch_off(self):
        """Stop the manager"""
        if not self.manager.is_switched_on():
            print("Manager is not running!")
            return
        
        self.manager.switch_off()
        
        # Give some time for graceful shutdown
        if self.loop_thread and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=5)
        
        print("✅ Arbitrage Opportunity Manager stopped")
    
    def status(self):
        """Get current status"""
        status = "RUNNING" if self.manager.is_switched_on() else "STOPPED"
        thread_status = "ACTIVE" if self.loop_thread and self.loop_thread.is_alive() else "INACTIVE"
        print(f"Status: {status} (Thread: {thread_status})")
        return status
    
    async def run_single_cycle(self):
        """Run a single cycle for testing"""
        if self.manager.is_switched_on():
            print("Manager is running in loop mode. Stop it first to run single cycle.")
            return
        
        print("Running single cycle...")
        await self.manager.run_cycle()
        print("Single cycle completed")


# Main execution for testing
async def main():
    """
    Example usage of the Arbitrage Opportunity Manager
    """
    control = OpportunityManagerControl()
    
    try:
        # Start the manager
        control.switch_on()
        
        # Let it run (in real usage, this would run indefinitely)
        await asyncio.sleep(300)  # Run for 5 minutes for testing
        
    except KeyboardInterrupt:
        print("Stopping due to keyboard interrupt...")
    finally:
        # Stop the manager
        control.switch_off()


def run_command_interface():
    """
    Run the command interface for manual control
    """
    print("Arbitrage Opportunity Manager")
    print("Commands: 'on' to start, 'off' to stop, 'status' to check, 'single' for single cycle, 'quit' to exit")
    
    control = OpportunityManagerControl()
    
    try:
        while True:
            command = input("\nEnter command: ").strip().lower()
            
            if command == 'on':
                control.switch_on()
            elif command == 'off':
                control.switch_off()
            elif command == 'status':
                control.status()
            elif command == 'single':
                # Run single cycle in a new event loop
                asyncio.run(control.run_single_cycle())
            elif command == 'quit':
                control.switch_off()
                break
            else:
                print("Unknown command. Use: on, off, status, single, quit")
    except KeyboardInterrupt:
        print("\nShutting down...")
        control.switch_off()


if __name__ == "__main__":
    # Run the command interface
    run_command_interface()