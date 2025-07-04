import asyncio
import re
from tools import BettingBot
from config_manager import ConfigManager

class ArbitrageBettingSystem:
    def __init__(self):
        self.betting_bot = BettingBot()
        self.config = ConfigManager()
        
        # Get Chrome profiles from config
        self.chrome_profiles = self.config.get_all_executable_configs()
        
        # Default max stake in USD
        self.default_max_stake_usd = 30
    
    def force_close_browser_sessions(self):
        """
        Force close any existing browser sessions to prevent conflicts
        """
        print("🔒 Force closing any existing browser sessions...")
        try:
            import subprocess
            import time
            
            # Kill Chrome processes that might be using our profiles
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], 
                         capture_output=True, check=False)
            
            # Wait a moment for processes to fully close
            time.sleep(3)
            print("✅ Browser sessions force closed successfully")
            
        except Exception as e:
            print(f"⚠️ Warning during browser cleanup: {e}")
        
    def extract_numeric_balance(self, balance_input) -> float:
        """Extract numeric value from balance string"""
        if not balance_input:
            return 0.0
        
        if isinstance(balance_input, (int, float)):
            return float(balance_input)
    
    # If it's a string, process it
    
        
        # Remove currency symbols and extract numeric value
        if isinstance(balance_input, str):
        # Remove currency symbols and extract numeric value
           numeric_str = re.sub(r'[^\d.,]', '', balance_input)
           numeric_str = numeric_str.replace(',', '.')
        
           try:
            return float(numeric_str)
           except ValueError:
            return 0.0
        
   # Fallback for any other type
        try:
            return float(balance_input)
        except (ValueError, TypeError):
             return 0.0
    
    async def balance_checker(self, arbitrage_data: dict) -> dict:
        """
        Check balances for both bookmakers using their respective Chrome profiles
        """
        print("🔍 Starting balance check for both bookmakers...")
        
        bookmaker1 = arbitrage_data["bookmaker1"].lower()
        bookmaker2 = arbitrage_data["bookmaker2"].lower()
        
        # Profile assignments from config
        profile1 = self.chrome_profiles.get("path1", {})
        profile2 = self.chrome_profiles.get("path2", {})
        
        results = {
            "bookmaker1": {
                "name": bookmaker1,
                "balance_result": None
            },
            "bookmaker2": {
                "name": bookmaker2, 
                "balance_result": None
            }
        }
        
        # Check bookmaker1 balance
        print(f"📊 Checking {bookmaker1} balance with Profile 1...")
        try:
            if bookmaker1 == "sportybet":
                results["bookmaker1"]["balance_result"] = await self.betting_bot.sporty_balance_checker(
                    profile1.get("executable_path", ""), profile1.get("user_data_dir", ""), "", ""
                )
            elif bookmaker1 == "leon":
                results["bookmaker1"]["balance_result"] = await self.betting_bot.leon_balance_checker_tool(
                    profile1.get("executable_path", ""), profile1.get("user_data_dir", ""), "", ""
                )
            elif bookmaker1 == "marathonbet":
                results["bookmaker1"]["balance_result"] = await self.betting_bot.marathonbet_balance_checker_tool(
                    profile1.get("executable_path", ""), profile1.get("user_data_dir", ""), "", ""
                )
            elif bookmaker1 == "zenitbet":
                results["bookmaker1"]["balance_result"] = await self.betting_bot.zenitbet_balance_checker_tool(
                    profile1.get("executable_path", ""), profile1.get("user_data_dir", ""), "", ""
                )
            elif bookmaker1 == "vbet":
                results["bookmaker1"]["balance_result"] = await self.betting_bot.vbet_balance_checker_tool(
                    profile1.get("executable_path", ""), profile1.get("user_data_dir", ""), "", ""
                )
            elif bookmaker1 == "sports888":
                results["bookmaker1"]["balance_result"] = await self.betting_bot.sports888_balance_checker_tool(
                    profile1.get("executable_path", ""), profile1.get("user_data_dir", ""), "", ""
                )
            elif bookmaker1 == "bet9ja":
                results["bookmaker1"]["balance_result"] = await self.betting_bot.bet9ja_balance_checker_tool(
                    profile1.get("executable_path", ""), profile1.get("user_data_dir", ""), "", ""
                )
            elif bookmaker1 == "nairabet":
                results["bookmaker1"]["balance_result"] = await self.betting_bot.nairabet_balance_checker_tool(
                    profile1.get("executable_path", ""), profile1.get("user_data_dir", ""), "", ""
                )
            else:
                print(f"❌ Unknown bookmaker1: {bookmaker1}")
                results["bookmaker1"]["balance_result"] = {
                    "is_logged_in": False,
                    "balance": "0.00",
                    "currency": "USD",
                    "error_message": f"Unknown bookmaker: {bookmaker1}"
                }
        except Exception as e:
            print(f"❌ Error checking {bookmaker1} balance: {e}")
            results["bookmaker1"]["balance_result"] = {
                "is_logged_in": False,
                "balance": "0.00", 
                "currency": "USD",
                "error_message": str(e)
            }
        
        # Check bookmaker2 balance
        print(f"📊 Checking {bookmaker2} balance with Profile 2...")
        try:
            if bookmaker2 == "sportybet":
                results["bookmaker2"]["balance_result"] = await self.betting_bot.sporty_balance_checker(
                    profile2.get("executable_path", ""), profile2.get("user_data_dir", ""), "", ""
                )
            elif bookmaker2 == "leon":
                results["bookmaker2"]["balance_result"] = await self.betting_bot.leon_balance_checker_tool(
                    profile2.get("executable_path", ""), profile2.get("user_data_dir", ""), "", ""
                )
            elif bookmaker2 == "marathonbet":
                results["bookmaker2"]["balance_result"] = await self.betting_bot.marathonbet_balance_checker_tool(
                    profile2.get("executable_path", ""), profile2.get("user_data_dir", ""), "", ""
                )
            elif bookmaker2 == "zenitbet":
                results["bookmaker2"]["balance_result"] = await self.betting_bot.zenitbet_balance_checker_tool(
                    profile2.get("executable_path", ""), profile2.get("user_data_dir", ""), "", ""
                )
            elif bookmaker2 == "vbet":
                results["bookmaker2"]["balance_result"] = await self.betting_bot.vbet_balance_checker_tool(
                    profile2.get("executable_path", ""), profile2.get("user_data_dir", ""), "", ""
                )
            elif bookmaker2 == "sports888":
                results["bookmaker2"]["balance_result"] = await self.betting_bot.sports888_balance_checker_tool(
                    profile2.get("executable_path", ""), profile2.get("user_data_dir", ""), "", ""
                )
            elif bookmaker2 == "bet9ja":
                results["bookmaker2"]["balance_result"] = await self.betting_bot.bet9ja_balance_checker_tool(
                    profile2.get("executable_path", ""), profile2.get("user_data_dir", ""), "", ""
                )
            elif bookmaker2 == "nairabet":
                results["bookmaker2"]["balance_result"] = await self.betting_bot.nairabet_balance_checker_tool(
                    profile2.get("executable_path", ""), profile2.get("user_data_dir", ""), "", ""
                )
            else:
                print(f"❌ Unknown bookmaker2: {bookmaker2}")
                results["bookmaker2"]["balance_result"] = {
                    "is_logged_in": False,
                    "balance": "0.00",
                    "currency": "USD", 
                    "error_message": f"Unknown bookmaker: {bookmaker2}"
                }
        except Exception as e:
            print(f"❌ Error checking {bookmaker2} balance: {e}")
            results["bookmaker2"]["balance_result"] = {
                "is_logged_in": False,
                "balance": "0.00",
                "currency": "USD",
                "error_message": str(e)
            }
        
        print("✅ Balance checking completed for both bookmakers")
        return results
    
    def stake_calculation(self, arbitrage_data: dict, balance_results: dict) -> dict:
        """
        Calculate optimal stakes for both bookmakers after currency conversion
        """
        print("💰 Starting stake calculation...")
        
        # Extract balance information
        bk1_balance_result = balance_results["bookmaker1"]["balance_result"]
        bk2_balance_result = balance_results["bookmaker2"]["balance_result"]
        
        bk1_balance_numeric = self.extract_numeric_balance(bk1_balance_result["balance"])
        bk2_balance_numeric = self.extract_numeric_balance(bk2_balance_result["balance"])
        
        bk1_currency = bk1_balance_result["currency"]
        bk2_currency = bk2_balance_result["currency"]
        
        print(f"📊 Bookmaker1 ({arbitrage_data['bookmaker1']}): {bk1_balance_numeric} {bk1_currency}")
        print(f"📊 Bookmaker2 ({arbitrage_data['bookmaker2']}): {bk2_balance_numeric} {bk2_currency}")
        
        # Convert balances to USD
        try:
            bk1_balance_usd = self.betting_bot.currency_converter(bk1_balance_numeric, bk1_currency, "USD")
            bk2_balance_usd = self.betting_bot.currency_converter(bk2_balance_numeric, bk2_currency, "USD")
        except Exception as e:
            print(f"❌ Currency conversion error: {e}")
            return {"error": f"Currency conversion failed: {e}"}
        
        print(f"💵 Converted balances - BK1: ${bk1_balance_usd} USD, BK2: ${bk2_balance_usd} USD")
        
        # Extract odds
        odd1 = float(arbitrage_data["odd_bk1"])
        odd2 = float(arbitrage_data["odd_bk2"])
        
        # Initial stake calculation with default max stake
        initial_stakes = self.betting_bot.calculate_arbitrage_stakes(odd1, odd2, self.default_max_stake_usd)
        
        if "error" in initial_stakes:
            return {"error": initial_stakes["error"]}
        
        stake1_usd = initial_stakes["stake1"]
        stake2_usd = initial_stakes["stake2"]
        
        print(f"📈 Initial stakes: BK1: ${stake1_usd} USD, BK2: ${stake2_usd} USD")
        
        # Check if stakes exceed available balances and recalculate if needed
        max_available_stake = min(bk1_balance_usd, bk2_balance_usd, self.default_max_stake_usd)
        
        if stake1_usd > bk1_balance_usd or stake2_usd > bk2_balance_usd:
            print("⚠️ Stakes exceed available balances, recalculating...")
            
            # Use the limiting balance to recalculate
            if stake1_usd > bk1_balance_usd:
                # Recalculate using bookmaker1's balance as known stake
                adjusted_stakes = self.betting_bot.calculate_arbitrage_stakes(
                    odd1, odd2, bk1_balance_usd
                )
            else:
                # Recalculate using bookmaker2's balance as known stake
                adjusted_stakes = self.betting_bot.calculate_arbitrage_stakes(
                    odd1, odd2, bk2_balance_usd
                )
            
            if "error" in adjusted_stakes:
                return {"error": adjusted_stakes["error"]}
            
            stake1_usd = adjusted_stakes["stake1"]
            stake2_usd = adjusted_stakes["stake2"]
            
            print(f"🔄 Adjusted stakes: BK1: ${stake1_usd} USD, BK2: ${stake2_usd} USD")
        
        # Convert stakes back to bookmaker currencies
        try:
            stake1_original_currency = self.betting_bot.currency_converter(stake1_usd, "USD", bk1_currency)
            stake2_original_currency = self.betting_bot.currency_converter(stake2_usd, "USD", bk2_currency)
        except Exception as e:
            print(f"❌ Stake currency conversion error: {e}")
            return {"error": f"Stake currency conversion failed: {e}"}
        
        result = {
            "bookmaker1": {
                "stake_usd": round(stake1_usd, 2),
                "stake_original_currency": round(stake1_original_currency, 2),
                "currency": bk1_currency,
                "balance_available": round(bk1_balance_numeric, 2)
            },
            "bookmaker2": {
                "stake_usd": round(stake2_usd, 2),
                "stake_original_currency": round(stake2_original_currency, 2),
                "currency": bk2_currency,
                "balance_available": round(bk2_balance_numeric, 2)
            },
            "arbitrage_info": initial_stakes
        }
        
        print("✅ Stake calculation completed")
        return result
    
    def format_bet_data(self, arbitrage_data: dict, stake_info: dict, bookmaker_num: int) -> dict:
        """
        Format betting data for individual bookmaker
        """
        if bookmaker_num == 1:
            return {
                "profit": arbitrage_data["profit"],
                "sport": arbitrage_data["sport"],
                "event_time": arbitrage_data["event_time"],
                "team1_bk": arbitrage_data["team1_bk1"],
                "team2_bk": arbitrage_data["team2_bk1"],
                "league_bk": arbitrage_data["league_bk1"],
                "bet_type_bk": arbitrage_data["bet_type_bk1"],
                "odd_bk": arbitrage_data["odd_bk1"],
                "link_bk": arbitrage_data["link_bk1"],
                "stake_amount": stake_info["bookmaker1"]["stake_original_currency"]
            }
        else:
            return {
                "profit": arbitrage_data["profit"],
                "sport": arbitrage_data["sport"],
                "event_time": arbitrage_data["event_time"],
                "team1_bk": arbitrage_data["team1_bk2"],
                "team2_bk": arbitrage_data["team2_bk2"],
                "league_bk": arbitrage_data["league_bk2"],
                "bet_type_bk": arbitrage_data["bet_type_bk2"],
                "odd_bk": arbitrage_data["odd_bk2"],
                "link_bk": arbitrage_data["link_bk2"],
                "stake_amount": stake_info["bookmaker2"]["stake_original_currency"]
            }
    
    async def bet_placer(self, arbitrage_data: dict, stake_info: dict) -> dict:
        """
        Place bets on both bookmakers sequentially
        """
        print("🎯 Starting bet placement process...")
        
        bookmaker1 = arbitrage_data["bookmaker1"].lower()
        bookmaker2 = arbitrage_data["bookmaker2"].lower()
        
        # Profile assignments from config
        profile1 = self.chrome_profiles.get("path1", {})
        profile2 = self.chrome_profiles.get("path2", {})
        
        results = {
            "bookmaker1": {"name": bookmaker1, "result": None},
            "bookmaker2": {"name": bookmaker2, "result": None}
        }
        
        # Format betting data for both bookmakers
        bet_data_bk1 = self.format_bet_data(arbitrage_data, stake_info, 1)
        bet_data_bk2 = self.format_bet_data(arbitrage_data, stake_info, 2)
        
        # Place bet on bookmaker1
        print(f"🎯 Placing bet on {bookmaker1}...")
        try:
            if bookmaker1 == "sportybet":
                results["bookmaker1"]["result"] = await self.betting_bot.sporty_bet_placer(
                    bet_data_bk1, profile1.get("executable_path", ""), profile1.get("user_data_dir", "")
                )
            elif bookmaker1 == "leon":
                results["bookmaker1"]["result"] = await self.betting_bot.leon_bet_placer_tool(
                    bet_data_bk1, profile1.get("executable_path", ""), profile1.get("user_data_dir", "")
                )
            elif bookmaker1 == "marathonbet":
                results["bookmaker1"]["result"] = await self.betting_bot.marathonbet_bet_placer_tool(
                    bet_data_bk1, profile1.get("executable_path", ""), profile1.get("user_data_dir", "")
                )
            elif bookmaker1 == "zenitbet":
                results["bookmaker1"]["result"] = await self.betting_bot.zenitbet_bet_placer_tool(
                    bet_data_bk1, profile1.get("executable_path", ""), profile1.get("user_data_dir", "")
                )
            elif bookmaker1 == "vbet":
                results["bookmaker1"]["result"] = await self.betting_bot.vbet_bet_placer_tool(
                    bet_data_bk1, profile1.get("executable_path", ""), profile1.get("user_data_dir", "")
                )
            elif bookmaker1 == "sports888":
                results["bookmaker1"]["result"] = await self.betting_bot.sports888_bet_placer_tool(
                    bet_data_bk1, profile1.get("executable_path", ""), profile1.get("user_data_dir", "")
                )
            elif bookmaker1 == "bet9ja":
                results["bookmaker1"]["result"] = await self.betting_bot.bet9ja_bet_placer_tool(
                    bet_data_bk1, profile1.get("executable_path", ""), profile1.get("user_data_dir", "")
                )
            elif bookmaker1 == "nairabet":
                results["bookmaker1"]["result"] = await self.betting_bot.nairabet_bet_placer_tool(
                    bet_data_bk1, profile1.get("executable_path", ""), profile1.get("user_data_dir", "")
                )
        except Exception as e:
            print(f"❌ Error placing bet on {bookmaker1}: {e}")
            results["bookmaker1"]["result"] = {
                "workflow_summary": {"error": str(e), "bet_placed": False}
            }
        
        print(f"✅ {bookmaker1} bet placement completed")
        
        # Place bet on bookmaker2
        print(f"🎯 Placing bet on {bookmaker2}...")
        try:
            if bookmaker2 == "sportybet":
                results["bookmaker2"]["result"] = await self.betting_bot.sporty_bet_placer(
                    bet_data_bk2, profile2.get("executable_path", ""), profile2.get("user_data_dir", "")
                )
            elif bookmaker2 == "leon":
                results["bookmaker2"]["result"] = await self.betting_bot.leon_bet_placer_tool(
                    bet_data_bk2, profile2.get("executable_path", ""), profile2.get("user_data_dir", "")
                )
            elif bookmaker2 == "marathonbet":
                results["bookmaker2"]["result"] = await self.betting_bot.marathonbet_bet_placer_tool(
                    bet_data_bk2, profile2.get("executable_path", ""), profile2.get("user_data_dir", "")
                )
            elif bookmaker2 == "zenitbet":
                results["bookmaker2"]["result"] = await self.betting_bot.zenitbet_bet_placer_tool(
                    bet_data_bk2, profile2.get("executable_path", ""), profile2.get("user_data_dir", "")
                )
            elif bookmaker2 == "vbet":
                results["bookmaker2"]["result"] = await self.betting_bot.vbet_bet_placer_tool(
                    bet_data_bk2, profile2.get("executable_path", ""), profile2.get("user_data_dir", "")
                )
            elif bookmaker2 == "sports888":
                results["bookmaker2"]["result"] = await self.betting_bot.sports888_bet_placer_tool(
                    bet_data_bk2, profile2.get("executable_path", ""), profile2.get("user_data_dir", "")
                )
            elif bookmaker2 == "bet9ja":
                results["bookmaker2"]["result"] = await self.betting_bot.bet9ja_bet_placer_tool(
                    bet_data_bk2, profile2.get("executable_path", ""), profile2.get("user_data_dir", "")
                )
            elif bookmaker2 == "nairabet":
                results["bookmaker2"]["result"] = await self.betting_bot.nairabet_bet_placer_tool(
                    bet_data_bk2, profile2.get("executable_path", ""), profile2.get("user_data_dir", "")
                )
        except Exception as e:
            print(f"❌ Error placing bet on {bookmaker2}: {e}")
            results["bookmaker2"]["result"] = {
                "workflow_summary": {"error": str(e), "bet_placed": False}
            }
        
        print(f"✅ {bookmaker2} bet placement completed")
        print("🎉 All bets placement process completed!")
        
        return results
    
    async def execute_arbitrage(self, arbitrage_data: dict) -> dict:
        """
        Main function to execute the complete arbitrage betting process
        """
        print("🚀 Starting Arbitrage Betting Automation...")
        print(f"📊 Processing: {arbitrage_data['sport']} - {arbitrage_data['team1_bk1']} vs {arbitrage_data['team2_bk1']}")
        print(f"🏪 Bookmakers: {arbitrage_data['bookmaker1']} vs {arbitrage_data['bookmaker2']}")
        
        try:
            # Step 1: Check balances
            print("🔍 Phase 1: Balance Checking...")
            balance_results = await self.balance_checker(arbitrage_data)
            
            # Verify both bookmakers are logged in
            bk1_logged_in = balance_results["bookmaker1"]["balance_result"]["is_logged_in"]
            bk2_logged_in = balance_results["bookmaker2"]["balance_result"]["is_logged_in"]
            
            if not bk1_logged_in or not bk2_logged_in:
                return {
                    "success": False,
                    "error": "One or both bookmakers are not logged in",
                    "balance_results": balance_results
                }
            
            print("✅ Phase 1 completed: Balance checking successful")
            
            # CRITICAL: Force close browser sessions after balance checking
            print("🔄 Closing browser sessions before bet placement...")
            self.force_close_browser_sessions()
            
            # Step 2: Calculate stakes
            print("💰 Phase 2: Stake Calculation...")
            stake_info = self.stake_calculation(arbitrage_data, balance_results)
            
            if "error" in stake_info:
                return {
                    "success": False,
                    "error": stake_info["error"],
                    "balance_results": balance_results
                }
            
            print("✅ Phase 2 completed: Stake calculation successful")
            
            # Step 3: Place bets (with fresh browser sessions)
            print("🎯 Phase 3: Bet Placement (Fresh Browser Sessions)...")
            bet_results = await self.bet_placer(arbitrage_data, stake_info)
            
            print("✅ Phase 3 completed: Bet placement attempted")
            
            # Final result
            return {
                "success": True,
                "balance_results": balance_results,
                "stake_info": stake_info,
                "bet_results": bet_results,
                "summary": {
                    "arbitrage_profit": stake_info["arbitrage_info"]["actual_profit_percent"],
                    "total_stake_usd": round(stake_info["bookmaker1"]["stake_usd"] + stake_info["bookmaker2"]["stake_usd"], 2),
                    "bk1_bet_placed": bet_results["bookmaker1"]["result"]["workflow_summary"].get("bet_placed", False),
                    "bk2_bet_placed": bet_results["bookmaker2"]["result"]["workflow_summary"].get("bet_placed", False)
                }
            }
            
        except Exception as e:
            print(f"❌ Critical error in arbitrage execution: {e}")
            # Ensure cleanup even if there's an error
            try:
                self.force_close_browser_sessions()
            except:
                pass
            return {
                "success": False,
                "error": str(e)
            }


# Example usage and testing
async def main():
    # Example arbitrage data
    example_data = {
        "profit": "0.48%",
        "sport": "Baseball",
        "event_time": "Jul 04, 10:35",
        "bookmaker1": "nairabet",
        "team1_bk1": "Rakuten Monkeys",
        "team2_bk1": "Fubon Guardians",
        "league_bk1": "Baseball. China. Chinese Professional Baseball League",
        "bet_type_bk1": "DNB2",
        "odd_bk1": "2.5",
        "link_bk1": "https://nairabet.com/event/14758410",
        "bookmaker2": "bet9ja",
        "team1_bk2": "Rakuten Monkeys", 
        "team2_bk2": "Fubon Guardians",
        "league_bk2": "Baseball. Chinese Taipei. CPBL",
        "bet_type_bk2": "DNB1",
        "odd_bk2": "1.68",
        "link_bk2": "https://sports.bet9ja.com/event/618948749"
    }
    
    # Initialize the system
    arbitrage_system = ArbitrageBettingSystem()
    
    # Execute the arbitrage
    result = await arbitrage_system.execute_arbitrage(example_data)
    
    print("\n" + "="*50)
    print("FINAL RESULT:")
    print("="*50)
    print(f"Success: {result['success']}")
    
    if result['success']:
        print(f"Arbitrage Profit: {result['summary']['arbitrage_profit']}%")
        print(f"Total Stake: ${result['summary']['total_stake_usd']} USD")
        print(f"BK1 Bet Placed: {result['summary']['bk1_bet_placed']}")
        print(f"BK2 Bet Placed: {result['summary']['bk2_bet_placed']}")
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())