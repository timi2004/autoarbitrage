from currency_converter import CurrencyConverter
import requests
from config_manager import ConfigManager

# Import all your existing bookmaker functions
from sporty import balance_checker, bet_placer
from leon import leon_balance_checker, leon_bet_placer
from marathon import marathonbet_balance_checker, marathonbet_bet_placer
from zenit import zenitbet_balance_checker, zenitbet_bet_placer
from vbet import vbet_balance_checker, vbet_bet_placer
from sports888 import sport888_balance_checker, sport888_bet_placer
from bet9ja import bet9ja_balance_checker, bet9ja_bet_placer
from nairabet import nairabet_balance_checker, nairabet_bet_placer


class BettingBot:
    def __init__(self):
        self.config = ConfigManager()

    def get_credentials(self, bookmaker_name: str) -> dict:
        """Get credentials for a bookmaker from config"""
        credentials = self.config.get_bookmaker_credentials(bookmaker_name)
        if credentials and credentials["username"] and credentials["password"]:
            return credentials
        else:
            print(f"⚠️ No credentials found for {bookmaker_name}")
            return {"username": "", "password": ""}

    def currency_converter(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Hybrid currency converter using currency_converter library with API fallback
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return amount
        
        def try_currency_converter_library():
            try:
                c = CurrencyConverter()
                result = c.convert(amount, from_currency, to_currency)
                return round(result, 2)
            except Exception as e:
                raise Exception(f"currency_converter library failed: {e}")
        
        def try_api_fallback():
            try:
                url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                if to_currency not in data['rates']:
                    raise Exception(f"Currency {to_currency} not supported by API")
                
                rate = data['rates'][to_currency]
                result = amount * rate
                return round(result, 2)
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"API request failed: {e}")
            except Exception as e:
                raise Exception(f"API conversion failed: {e}")
        
        api_required_currencies = {'NGN', 'RUB', 'TRY', 'IRR', 'PKR', 'BDT', 'LKR', 'VES', 'MMK'}
        
        if from_currency in api_required_currencies or to_currency in api_required_currencies:
            try:
                print(f"🌐 Using API for {from_currency}→{to_currency}")
                return try_api_fallback()
            except Exception as e:
                raise Exception(f"API failed for special currency conversion: {e}")
        
        try:
            print(f"📚 Using currency_converter library for {from_currency}→{to_currency}")
            return try_currency_converter_library()
        except Exception as library_error:
            print(f"❌ Library failed: {library_error}")
            print(f"🌐 Falling back to API for {from_currency}→{to_currency}")
            try:
                return try_api_fallback()
            except Exception as api_error:
                raise Exception(f"Both methods failed. Library: {library_error}, API: {api_error}")
    
    def calculate_arbitrage_stakes(self, odd1: float, odd2: float, max_stake: float) -> dict:
        """Calculate optimal stakes for arbitrage betting"""
        implied_prob1 = 1 / odd1
        implied_prob2 = 1 / odd2
        total_implied_prob = implied_prob1 + implied_prob2
        
        arbitrage_profit_percent = ((1 - total_implied_prob) / total_implied_prob) * 100
        
        if total_implied_prob > 1:
            return {"error": "No arbitrage opportunity exists with these odds"}
        
        total_stake = max_stake
        stake1 = total_stake * (implied_prob1 / total_implied_prob)
        stake2 = total_stake * (implied_prob2 / total_implied_prob)
        expected_profit = total_stake * (arbitrage_profit_percent / 100)
        
        profit_if_1_wins = stake1 * odd1 - total_stake
        profit_if_2_wins = stake2 * odd2 - total_stake
        
        return {
            "stake1": round(stake1, 2),
            "stake2": round(stake2, 2),
            "total_stake": round(total_stake, 2),
            "expected_profit": round(expected_profit, 2),
            "actual_profit_percent": round(arbitrage_profit_percent, 2),
            "profit_if_outcome1": round(profit_if_1_wins, 2),
            "profit_if_outcome2": round(profit_if_2_wins, 2),
            "verification": abs(profit_if_1_wins - profit_if_2_wins) < 0.01
        }
    
    def calculate_arbitrage_from_known_stake(self, odd1: float, odd2: float, 
                                           stake1: float = None, stake2: float = None) -> dict:
        """Calculate arbitrage betting when you know one stake"""
        if stake1 is not None and stake2 is not None:
            return {"error": "Provide only one known stake, not both"}
        
        if stake1 is None and stake2 is None:
            return {"error": "Must provide either stake1 or stake2"}
        
        implied_prob1 = 1 / odd1
        implied_prob2 = 1 / odd2
        total_implied_prob = implied_prob1 + implied_prob2
        
        if total_implied_prob >= 1:
            return {"error": "No arbitrage opportunity exists with these odds"}
        
        max_profit_percent = ((1 - total_implied_prob) / total_implied_prob) * 100
        
        if stake1 is not None:
            optimal_total_stake = stake1 / (implied_prob1 / total_implied_prob)
            stake2 = optimal_total_stake * (implied_prob2 / total_implied_prob)
            known_stake_type = "stake1"
            known_stake_value = stake1
        else:
            optimal_total_stake = stake2 / (implied_prob2 / total_implied_prob)
            stake1 = optimal_total_stake * (implied_prob1 / total_implied_prob)
            known_stake_type = "stake2"
            known_stake_value = stake2
        
        total_stake = stake1 + stake2
        profit_if_1_wins = stake1 * odd1 - total_stake
        profit_if_2_wins = stake2 * odd2 - total_stake
        actual_profit_percent = max_profit_percent
        
        return {
            "stake1": round(stake1, 2),
            "stake2": round(stake2, 2),
            "total_stake": round(total_stake, 2),
            "expected_profit": round(profit_if_1_wins, 2),
            "actual_profit_percent": round(actual_profit_percent, 2),
            "max_possible_profit_percent": round(max_profit_percent, 2),
            "profit_if_outcome1": round(profit_if_1_wins, 2),
            "profit_if_outcome2": round(profit_if_2_wins, 2),
            "known_stake_type": known_stake_type,
            "known_stake_value": known_stake_value,
            "verification": abs(profit_if_1_wins - profit_if_2_wins) < 0.01
        }
    
    # Balance checker methods
    async def sporty_balance_checker(self, executable_path: str, user_data_dir: str, email: str, password: str) -> dict:
        """Check balance on SportyBet for the logged-in user."""
        print("🔍 Starting SportyBet balance check...")
        try:
            creds = self.get_credentials("sportybet")
            if not email:
                email = creds["username"]
            if not password:
                password = creds["password"]
                
            balance_result = await balance_checker(executable_path, user_data_dir, email, password)
            
            if balance_result:
                print(f"✅ Direct balance result: {balance_result.balance}")
                return {
                    "is_logged_in": balance_result.is_logged_in,
                    "balance": balance_result.balance,
                    "currency": "NGN",  # SportyBet typically uses NGN
                    "error_message": balance_result.error_message
                }
            else:
                print("❌ No balance result returned from browser automation")
                return {
                    "is_logged_in": False,
                    "balance": "0.00",
                    "currency": "NGN",
                    "error_message": "Browser automation failed to return balance"
                }
                
        except Exception as e:
            print(f"❌ Error in SportyBet balance check: {e}")
            return {
                "is_logged_in": False,
                "balance": "0.00",
                "currency": "NGN",
                "error_message": str(e)
            }
    
    async def leon_balance_checker_tool(self, executable_path: str, user_data_dir: str, email: str, password: str) -> dict:
        """Check balance on Leon.ru for the logged-in user."""
        print("🔍 Starting Leon.ru balance check...")
        try:
            creds = self.get_credentials("leon")
            if not email:
                email = creds["username"]
            if not password:
                password = creds["password"]
                
            balance_result = await leon_balance_checker(executable_path, user_data_dir, email, password)
            
            if balance_result:
                return {
                    "is_logged_in": balance_result.is_logged_in,
                    "balance": balance_result.balance,
                    "currency": "RUB",  # Leon.ru typically uses RUB
                    "error_message": balance_result.error_message
                }
            else:
                return {
                    "is_logged_in": False,
                    "balance": "0,00 ₽",
                    "currency": "RUB",
                    "error_message": "Balance check failed"
                }
        except Exception as e:
            print(f"❌ Error in Leon.ru balance check: {e}")
            return {
                "is_logged_in": False,
                "balance": "0,00 ₽",
                "currency": "RUB",
                "error_message": str(e)
            }
    
    async def marathonbet_balance_checker_tool(self, executable_path: str, user_data_dir: str, email: str, password: str) -> dict:
        """Check balance on Marathonbet for the logged-in user."""
        print("🔍 Starting Marathonbet balance check...")
        try:
            creds = self.get_credentials("marathonbet")
            if not email:
                email = creds["username"]
            if not password:
                password = creds["password"]
                
            balance_result = await marathonbet_balance_checker(executable_path, user_data_dir, email, password)
            
            if balance_result:
                return {
                    "is_logged_in": balance_result.is_logged_in,
                    "balance": balance_result.balance,
                    "currency": "NGN",  # Marathonbet typically uses NGN
                    "error_message": balance_result.error_message
                }
            else:
                return {
                    "is_logged_in": False,
                    "balance": "₦ 0.00",
                    "currency": "NGN",
                    "error_message": "Balance check failed"
                }
        except Exception as e:
            print(f"❌ Error in Marathonbet balance check: {e}")
            return {
                "is_logged_in": False,
                "balance": "₦ 0.00",
                "currency": "NGN",
                "error_message": str(e)
            }
    
    async def zenitbet_balance_checker_tool(self, executable_path: str, user_data_dir: str, email: str, password: str) -> dict:
        """Check balance on Zenitbet for the logged-in user."""
        print("🔍 Starting Zenitbet balance check...")
        try:
            creds = self.get_credentials("zenitbet")
            if not email:
                email = creds["username"]
            if not password:
                password = creds["password"]
                
            balance_result = await zenitbet_balance_checker(executable_path, user_data_dir, email, password)
            
            if balance_result:
                return {
                    "is_logged_in": balance_result.is_logged_in,
                    "balance": balance_result.balance,
                    "currency": "RUB",  # Zenitbet typically uses RUB
                    "error_message": balance_result.error_message
                }
            else:
                return {
                    "is_logged_in": False,
                    "balance": "₽ 0.00",
                    "currency": "RUB",
                    "error_message": "Balance check failed"
                }
        except Exception as e:
            print(f"❌ Error in Zenitbet balance check: {e}")
            return {
                "is_logged_in": False,
                "balance": "₽ 0.00",
                "currency": "RUB",
                "error_message": str(e)
            }
    
    async def vbet_balance_checker_tool(self, executable_path: str, user_data_dir: str, email: str, password: str) -> dict:
        """Check balance on Vbet for the logged-in user."""
        print("🔍 Starting Vbet balance check...")
        try:
            creds = self.get_credentials("vbet")
            if not email:
                email = creds["username"]
            if not password:
                password = creds["password"]
                
            balance_result = await vbet_balance_checker(executable_path, user_data_dir, email, password)
            
            if balance_result:
                return {
                    "is_logged_in": balance_result.is_logged_in,
                    "balance": balance_result.balance,
                    "currency": "USD",  # Vbet typically uses USD
                    "error_message": balance_result.error_message
                }
            else:
                return {
                    "is_logged_in": False,
                    "balance": "$0.00",
                    "currency": "USD",
                    "error_message": "Balance check failed"
                }
        except Exception as e:
            print(f"❌ Error in Vbet balance check: {e}")
            return {
                "is_logged_in": False,
                "balance": "$0.00",
                "currency": "USD",
                "error_message": str(e)
            }
    
    async def sports888_balance_checker_tool(self, executable_path: str, user_data_dir: str, email: str, password: str) -> dict:
        """Check balance on Sports888 for the logged-in user."""
        print("🔍 Starting 888Sports balance check...")
        try:
            creds = self.get_credentials("sports888")
            if not email:
                email = creds["username"]
            if not password:
                password = creds["password"]
                
            balance_result = await sport888_balance_checker(executable_path, user_data_dir, email, password)
            
            if balance_result:
                return {
                    "is_logged_in": balance_result.is_logged_in,
                    "balance": balance_result.balance,
                    "currency": "USD",  # 888Sports typically uses USD
                    "error_message": balance_result.error_message
                }
            else:
                return {
                    "is_logged_in": False,
                    "balance": "$0.00",
                    "currency": "USD",
                    "error_message": "Balance check failed"
                }
        except Exception as e:
            print(f"❌ Error in 888Sports balance check: {e}")
            return {
                "is_logged_in": False,
                "balance": "$0.00",
                "currency": "USD",
                "error_message": str(e)
            }
    
    async def bet9ja_balance_checker_tool(self, executable_path: str, user_data_dir: str, email: str, password: str) -> dict:
        """Check balance on Bet9ja for the logged-in user."""
        print("🔍 Starting Bet9ja balance check...")
        try:
            creds = self.get_credentials("bet9ja")
            if not email:
                email = creds["username"]
            if not password:
                password = creds["password"]
                
            balance_result = await bet9ja_balance_checker(executable_path, user_data_dir, email, password)
            
            if balance_result:
                return {
                    "is_logged_in": balance_result.is_logged_in,
                    "balance": balance_result.balance,
                    "currency": "NGN",  # Bet9ja typically uses NGN
                    "error_message": balance_result.error_message
                }
            else:
                return {
                    "is_logged_in": False,
                    "balance": "₦ 0.00",
                    "currency": "NGN",
                    "error_message": "Balance check failed"
                }
        except Exception as e:
            print(f"❌ Error in Bet9ja balance check: {e}")
            return {
                "is_logged_in": False,
                "balance": "₦ 0.00",
                "currency": "NGN",
                "error_message": str(e)
            }
    
    async def nairabet_balance_checker_tool(self, executable_path: str, user_data_dir: str, email: str, password: str) -> dict:
        """Check balance on NairaBet for the logged-in user."""
        print("🔍 Starting NairaBet balance check...")
        try:
            creds = self.get_credentials("nairabet")
            if not email:
                email = creds["username"]
            if not password:
                password = creds["password"]
                
            balance_result = await nairabet_balance_checker(executable_path, user_data_dir, email, password)
            
            if balance_result:
                return {
                    "is_logged_in": balance_result.is_logged_in,
                    "balance": balance_result.balance,
                    "currency": "NGN",  # NairaBet typically uses NGN
                    "error_message": balance_result.error_message
                }
            else:
                return {
                    "is_logged_in": False,
                    "balance": "₦ 0.00",
                    "currency": "NGN",
                    "error_message": "Balance check failed"
                }
        except Exception as e:
            print(f"❌ Error in NairaBet balance check: {e}")
            return {
                "is_logged_in": False,
                "balance": "₦ 0.00",
                "currency": "NGN",
                "error_message": str(e)
            }
    
    # Bet placer methods
    async def sporty_bet_placer(self, betting_data: dict, executable_path: str, user_data_dir: str) -> dict:
        """Place a bet on SportyBet with the provided betting information."""
        print("🔍 Starting SportyBet bet placement...")
        try:
            sporty_betting_data = {
                "profit": betting_data.get("profit", ""),
                "sport": betting_data.get("sport", ""),
                "event_time": betting_data.get("event_time", ""),
                "bookmaker": "SportyBet",
                "team1_bk": betting_data.get("team1_bk", ""),
                "team2_bk": betting_data.get("team2_bk", ""),
                "league_bk": betting_data.get("league_bk", ""),
                "bet_type_bk": betting_data.get("bet_type_bk", ""),
                "odd_bk": betting_data.get("odd_bk", ""),
                "link_bk": betting_data.get("link_bk", ""),
                "stake_amount": float(betting_data.get("stake_amount", 0))
            }
            
            result = await bet_placer(sporty_betting_data, executable_path, user_data_dir)
            
            if result:
                return {
                    "bet_placement_result": result.get("bet_placement_result"),
                    "betslip_verification_result": result.get("betslip_verification_result"),
                    "workflow_summary": result.get("workflow_summary", {})
                }
            else:
                return {
                    "bet_placement_result": None,
                    "betslip_verification_result": None,
                    "workflow_summary": {
                        "bet_placed": False,
                        "verification_completed": False,
                        "stake_amount": betting_data.get("stake_amount", 0),
                        "error": "No result returned"
                    }
                }
                
        except Exception as e:
            print(f"❌ Error in SportyBet bet placement: {e}")
            return {
                "bet_placement_result": None,
                "betslip_verification_result": None,
                "workflow_summary": {
                    "bet_placed": False,
                    "verification_completed": False,
                    "stake_amount": betting_data.get("stake_amount", 0),
                    "error": str(e)
                }
            }
    
    async def leon_bet_placer_tool(self, betting_data: dict, executable_path: str, user_data_dir: str) -> dict:
        """Place a bet on Leon.ru with the provided betting information."""
        print("🔍 Starting Leon.ru bet placement...")
        try:
            input_data = {
                "profit": betting_data.get("profit", ""),
                "sport": betting_data.get("sport", ""),
                "event_time": betting_data.get("event_time", ""),
                "bookmaker": "Leon.ru",
                "team1_bk": betting_data.get("team1_bk", ""),
                "team2_bk": betting_data.get("team2_bk", ""),
                "league_bk": betting_data.get("league_bk", ""),
                "bet_type_bk": betting_data.get("bet_type_bk", ""),
                "odd_bk": betting_data.get("odd_bk", ""),
                "link_bk": betting_data.get("link_bk", ""),
                "stake_amount": float(betting_data.get("stake_amount", 100))
            }
            
            result = await leon_bet_placer(input_data, executable_path, user_data_dir)
            
            if result:
                return {
                    "bet_placement_result": result.get("bet_placement_result"),
                    "betslip_verification_result": result.get("betslip_verification_result"),
                    "workflow_summary": result.get("workflow_summary", {})
                }
            else:
                return {
                    "bet_placement_result": None,
                    "betslip_verification_result": None,
                    "workflow_summary": {
                        "error": "Leon.ru bet placement failed",
                        "bet_placed": False
                    }
                }
        except Exception as e:
            print(f"❌ Error in Leon.ru bet placement: {e}")
            return {
                "bet_placement_result": None,
                "betslip_verification_result": None,
                "workflow_summary": {
                    "error": str(e),
                    "bet_placed": False
                }
            }
    
    async def marathonbet_bet_placer_tool(self, betting_data: dict, executable_path: str, user_data_dir: str) -> dict:
        """Place a bet on Marathonbet with the provided betting information."""
        print("🔍 Starting Marathonbet bet placement...")
        try:
            input_data = {
                "profit": betting_data.get("profit", ""),
                "sport": betting_data.get("sport", ""),
                "event_time": betting_data.get("event_time", ""),
                "bookmaker": "Marathonbet",
                "team1_bk": betting_data.get("team1_bk", ""),
                "team2_bk": betting_data.get("team2_bk", ""),
                "league_bk": betting_data.get("league_bk", ""),
                "bet_type_bk": betting_data.get("bet_type_bk", ""),
                "odd_bk": betting_data.get("odd_bk", ""),
                "link_bk": betting_data.get("link_bk", ""),
                "stake_amount": float(betting_data.get("stake_amount", 0))
            }
            
            result = await marathonbet_bet_placer(input_data, executable_path, user_data_dir)
            
            if result:
                return {
                    "bet_placement_result": result.get("bet_placement_result"),
                    "betslip_verification_result": result.get("betslip_verification_result"),
                    "workflow_summary": result.get("workflow_summary", {})
                }
            else:
                return {
                    "bet_placement_result": None,
                    "betslip_verification_result": None,
                    "workflow_summary": {
                        "error": "Marathonbet bet placement failed",
                        "bet_placed": False
                    }
                }
        except Exception as e:
            print(f"❌ Error in Marathonbet bet placement: {e}")
            return {
                "bet_placement_result": None,
                "betslip_verification_result": None,
                "workflow_summary": {
                    "error": str(e),
                    "bet_placed": False
                }
            }
    
    async def zenitbet_bet_placer_tool(self, betting_data: dict, executable_path: str, user_data_dir: str) -> dict:
        """Place a bet on Zenitbet with the provided betting information."""
        print("🔍 Starting Zenitbet bet placement...")
        try:
            input_data = {
                "profit": betting_data.get("profit", ""),
                "sport": betting_data.get("sport", ""),
                "event_time": betting_data.get("event_time", ""),
                "bookmaker": "Zenitbet",
                "team1_bk": betting_data.get("team1_bk", ""),
                "team2_bk": betting_data.get("team2_bk", ""),
                "league_bk": betting_data.get("league_bk", ""),
                "bet_type_bk": betting_data.get("bet_type_bk", ""),
                "odd_bk": betting_data.get("odd_bk", ""),
                "link_bk": betting_data.get("link_bk", ""),
                "stake_amount": float(betting_data.get("stake_amount", 0))
            }
            
            result = await zenitbet_bet_placer(input_data, executable_path, user_data_dir)
            
            if result:
                return {
                    "bet_placement_result": result.get("bet_placement_result"),
                    "betslip_verification_result": result.get("betslip_verification_result"),
                    "workflow_summary": result.get("workflow_summary", {})
                }
            else:
                return {
                    "bet_placement_result": None,
                    "betslip_verification_result": None,
                    "workflow_summary": {
                        "error": "Zenitbet bet placement failed",
                        "bet_placed": False
                    }
                }
        except Exception as e:
            print(f"❌ Error in Zenitbet bet placement: {e}")
            return {
                "bet_placement_result": None,
                "betslip_verification_result": None,
                "workflow_summary": {
                    "error": str(e),
                    "bet_placed": False
                }
            }
    
    async def vbet_bet_placer_tool(self, betting_data: dict, executable_path: str, user_data_dir: str) -> dict:
        """Place a bet on Vbet with the provided betting information."""
        print("🔍 Starting Vbet bet placement...")
        try:
            input_data = {
                "profit": betting_data.get("profit", ""),
                "sport": betting_data.get("sport", ""),
                "event_time": betting_data.get("event_time", ""),
                "bookmaker": "Vbet",
                "team1_bk": betting_data.get("team1_bk", ""),
                "team2_bk": betting_data.get("team2_bk", ""),
                "league_bk": betting_data.get("league_bk", ""),
                "bet_type_bk": betting_data.get("bet_type_bk", ""),
                "odd_bk": betting_data.get("odd_bk", ""),
                "link_bk": betting_data.get("link_bk", ""),
                "stake_amount": float(betting_data.get("stake_amount", 0))
            }
            
            result = await vbet_bet_placer(input_data, executable_path, user_data_dir)
            
            if result:
                return {
                    "bet_placement_result": result.get("bet_placement_result"),
                    "betslip_verification_result": result.get("betslip_verification_result"),
                    "workflow_summary": result.get("workflow_summary", {})
                }
            else:
                return {
                    "bet_placement_result": None,
                    "betslip_verification_result": None,
                    "workflow_summary": {
                        "error": "Vbet bet placement failed",
                        "bet_placed": False
                    }
                }
        except Exception as e:
            print(f"❌ Error in Vbet bet placement: {e}")
            return {
                "bet_placement_result": None,
                "betslip_verification_result": None,
                "workflow_summary": {
                    "error": str(e),
                    "bet_placed": False
                }
            }
    
    async def sports888_bet_placer_tool(self, betting_data: dict, executable_path: str, user_data_dir: str) -> dict:
        """Place a bet on 888Sports with the provided betting information."""
        print("🔍 Starting 888Sports bet placement...")
        try:
            input_data = {
                "profit": betting_data.get("profit", ""),
                "sport": betting_data.get("sport", ""),
                "event_time": betting_data.get("event_time", ""),
                "bookmaker": "888Sports",
                "team1_bk": betting_data.get("team1_bk", ""),
                "team2_bk": betting_data.get("team2_bk", ""),
                "league_bk": betting_data.get("league_bk", ""),
                "bet_type_bk": betting_data.get("bet_type_bk", ""),
                "odd_bk": betting_data.get("odd_bk", ""),
                "link_bk": betting_data.get("link_bk", ""),
                "stake_amount": float(betting_data.get("stake_amount", 0))
            }
            
            result = await sport888_bet_placer(input_data, executable_path, user_data_dir)
            
            if result:
                return {
                    "bet_placement_result": result.get("bet_placement_result"),
                    "betslip_verification_result": result.get("betslip_verification_result"),
                    "workflow_summary": result.get("workflow_summary", {})
                }
            else:
                return {
                    "bet_placement_result": None,
                    "betslip_verification_result": None,
                    "workflow_summary": {
                        "error": "888Sports bet placement failed",
                        "bet_placed": False
                    }
                }
        except Exception as e:
            print(f"❌ Error in 888Sports bet placement: {e}")
            return {
                "bet_placement_result": None,
                "betslip_verification_result": None,
                "workflow_summary": {
                    "error": str(e),
                    "bet_placed": False
                }
            }
    
    async def bet9ja_bet_placer_tool(self, betting_data: dict, executable_path: str, user_data_dir: str) -> dict:
        """Place a bet on Bet9ja with the provided betting information."""
        print("🔍 Starting Bet9ja bet placement...")
        try:
            input_data = {
                "profit": betting_data.get("profit", ""),
                "sport": betting_data.get("sport", ""),
                "event_time": betting_data.get("event_time", ""),
                "bookmaker": "Bet9ja",
                "team1_bk": betting_data.get("team1_bk", ""),
                "team2_bk": betting_data.get("team2_bk", ""),
                "league_bk": betting_data.get("league_bk", ""),
                "bet_type_bk": betting_data.get("bet_type_bk", ""),
                "odd_bk": betting_data.get("odd_bk", ""),
                "link_bk": betting_data.get("link_bk", ""),
                "stake_amount": float(betting_data.get("stake_amount", 0))
            }
            
            result = await bet9ja_bet_placer(input_data, executable_path, user_data_dir)
            
            if result:
                return {
                    "bet_placement_result": result.get("bet_placement_result"),
                    "betslip_verification_result": result.get("betslip_verification_result"),
                    "workflow_summary": result.get("workflow_summary", {})
                }
            else:
                return {
                    "bet_placement_result": None,
                    "betslip_verification_result": None,
                    "workflow_summary": {
                        "error": "Bet9ja bet placement failed",
                        "bet_placed": False
                    }
                }
        except Exception as e:
            print(f"❌ Error in Bet9ja bet placement: {e}")
            return {
                "bet_placement_result": None,
                "betslip_verification_result": None,
                "workflow_summary": {
                    "error": str(e),
                    "bet_placed": False
                }
            }
    
    async def nairabet_bet_placer_tool(self, betting_data: dict, executable_path: str, user_data_dir: str) -> dict:
        """Place a bet on NairaBet with the provided betting information."""
        print("🔍 Starting NairaBet bet placement...")
        try:
            input_data = {
                "profit": betting_data.get("profit", ""),
                "sport": betting_data.get("sport", ""),
                "event_time": betting_data.get("event_time", ""),
                "bookmaker": "NairaBet",
                "team1_bk": betting_data.get("team1_bk", ""),
                "team2_bk": betting_data.get("team2_bk", ""),
                "league_bk": betting_data.get("league_bk", ""),
                "bet_type_bk": betting_data.get("bet_type_bk", ""),
                "odd_bk": betting_data.get("odd_bk", ""),
                "link_bk": betting_data.get("link_bk", ""),
                "stake_amount": float(betting_data.get("stake_amount", 0))
            }
            
            result = await nairabet_bet_placer(input_data, executable_path, user_data_dir)
            
            if result:
                return {
                    "bet_placement_result": result.get("bet_placement_result"),
                    "betslip_verification_result": result.get("betslip_verification_result"),
                    "workflow_summary": result.get("workflow_summary", {})
                }
            else:
                return {
                    "bet_placement_result": None,
                    "betslip_verification_result": None,
                    "workflow_summary": {
                        "error": "NairaBet bet placement failed",
                        "bet_placed": False
                    }
                }
        except Exception as e:
            print(f"❌ Error in NairaBet bet placement: {e}")
            return {
                "bet_placement_result": None,
                "betslip_verification_result": None,
                "workflow_summary": {
                    "error": str(e),
                    "bet_placed": False
                }
            }


# Example usage:
if __name__ == "__main__":
    bot = BettingBot()
    
    # Example arbitrage calculation
    result = bot.calculate_arbitrage_stakes(2.1, 2.2, 1000)
    print(result)