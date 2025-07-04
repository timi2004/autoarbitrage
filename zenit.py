from langchain_anthropic import ChatAnthropic  
from browser_use import Agent, BrowserSession, Controller, ActionResult
from dotenv import load_dotenv  
import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any

load_dotenv()   

# Define the output format for Agent 2 (bet placement)
class BetPlacementResult(BaseModel):
    input_data: Dict[str, Any] 
    error_message: str

# Define the output format for Agent 3 (betslip verification)
class SiteAnalysis(BaseModel):
    url: str = Field(description="Website URL visited")
    title: str = Field(description="Page title")
    description: str = Field(description="What the site does in 1-2 sentences")
    main_sections: List[str] = Field(description="3-5 main sections or features")
    is_betting_site: bool = Field(description="Is this a betting/gambling website")

class Balance(BaseModel):
    is_logged_in: bool = Field(description="Whether the user is logged in")
    balance: str = Field(description="User's account balance with currency")
    error_message: str = Field(default="", description="Any error message encountered during balance check")

class Placer(BaseModel):
    is_place_bet: bool = Field(default=False, description="Whether the bet has been placed successfully")
    error_message: str = Field(default="", description="Any error message encountered during bet placement")

# Create controllers with different output models
controller = Controller(output_model=BetPlacementResult)
controller3 = Controller(output_model=SiteAnalysis)
controller4 = Controller(output_model=Balance)
controller5 = Controller(output_model=Placer)

# ==================== ZENITBET CONTROLLER ACTIONS ====================

@controller4.action('Login with ZenitBet credentials')
async def login_with_zenitbet_credentials(browser, login: str, password: str) -> ActionResult:
    """Login to ZenitBet with provided credentials"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (credentials) => {
            try {
                const { login, password } = credentials;
                
                // Check if already logged in by looking for balance
                const balanceElement = document.querySelector('.header-balance-amount');
                if (balanceElement && balanceElement.textContent.includes('RUB')) {
                    return {
                        success: true,
                        status: 'already_logged_in',
                        balance: balanceElement.textContent.trim()
                    };
                }
                
                // Look for login button to open modal
                const loginButton = document.querySelector('.login-group-login') ||
                                  document.querySelector('button:contains("Entrance")') ||
                                  document.querySelector('[class*="login"]');
                
                if (!loginButton) {
                    return {
                        success: false,
                        error: 'Login button not found'
                    };
                }
                
                // Click login button to open modal
                loginButton.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Find login and password inputs in the modal
                const loginInput = document.querySelector('input[name="login"]') ||
                                 document.querySelector('input[placeholder*="phone"]') ||
                                 document.querySelector('input[type="text"]');
                                 
                const passwordInput = document.querySelector('input[name="password"]') ||
                                    document.querySelector('input[type="password"]');
                                    
                const submitButton = document.querySelector('button[type="submit"]') ||
                                   document.querySelector('.flat_button_1') ||
                                   document.querySelector('button:contains("Entrance")');
                
                if (!loginInput || !passwordInput) {
                    return {
                        success: false,
                        error: 'Login form inputs not found in modal'
                    };
                }
                
                // Clear and fill login
                loginInput.value = '';
                loginInput.focus();
                loginInput.value = login;
                loginInput.dispatchEvent(new Event('input', { bubbles: true }));
                loginInput.dispatchEvent(new Event('change', { bubbles: true }));
                loginInput.blur();
                
                // Wait between fields
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Clear and fill password
                passwordInput.value = '';
                passwordInput.focus();
                passwordInput.value = password;
                passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                passwordInput.blur();
                
                // Wait for validation
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Click submit button
                if (submitButton) {
                    submitButton.click();
                    
                    // Wait for login to process
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    
                    // Check if login was successful
                    const balanceAfterLogin = document.querySelector('.header-balance-amount');
                    
                    if (balanceAfterLogin && balanceAfterLogin.textContent.includes('RUB')) {
                        return {
                            success: true,
                            status: 'login_successful',
                            balance: balanceAfterLogin.textContent.trim()
                        };
                    } else {
                        // Check if modal is still open (login failed)
                        const modalStillOpen = document.querySelector('.box__main');
                        if (modalStillOpen) {
                            return {
                                success: false,
                                status: 'login_failed',
                                error: 'Login modal still open after attempt'
                            };
                        }
                    }
                }
                
                return {
                    success: false,
                    status: 'unknown',
                    error: 'Could not determine login status'
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """, {"login": login, "password": password})
    
    return ActionResult(extracted_content=f"ZenitBet Login result: {result}")

@controller4.action('Ask human for help with issues')   
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller5.action('Ask human for help with issues')   
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller3.action('Count ZenitBet betslip games')
async def count_zenitbet_betslip_games(browser) -> ActionResult:
    """Count number of games in ZenitBet betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        () => {
            try {
                // Look for betslip items
                const basketItems = document.querySelectorAll('.basket-item');
                const stakeInputs = document.querySelectorAll('input[id*="|"]'); // Stakes have format "id|number"
                
                // Count using different methods for verification
                const basketCount = basketItems.length;
                const inputsCount = stakeInputs.length;
                
                // Use the most reliable count
                const finalCount = Math.max(basketCount, inputsCount);
                
                // Check betslip visibility
                const basketVisible = document.querySelector('.basket-item') !== null;
                
                return {
                    success: true,
                    bet_count: finalCount,
                    basket_count: basketCount,
                    inputs_count: inputsCount,
                    betslip_visible: basketVisible,
                    message: `${finalCount} games in ZenitBet betslip`
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"ZenitBet Betslip count: {result}")


    
    return ActionResult(extracted_content=f"ZenitBet Stake fill result: {result}")

@controller5.action('Click ZenitBet place bet button')
async def click_zenitbet_place_bet(browser) -> ActionResult:
    """Click the Place Bet button in ZenitBet"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for place bet button
                const placeBetButton = document.querySelector('.basket-make-bet-button') ||
                                     document.querySelector('.basket-dobet') ||
                                     document.querySelector('button:contains("Bet")') ||
                                     document.querySelector('.flat_button:contains("Bet")');
                
                if (!placeBetButton) {
                    return {
                        success: false,
                        error: 'Place bet button not found'
                    };
                }
                
                // Check if button is disabled
                if (placeBetButton.disabled || 
                    placeBetButton.classList.contains('disabled') ||
                    placeBetButton.style.display === 'none') {
                    return {
                        success: false,
                        error: 'Place bet button is disabled or hidden'
                    };
                }
                
                // Click the button
                placeBetButton.click();
                
                // Wait for response
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                // Check for success/error messages
                const successMessage = document.querySelector('.success, .confirmation, [class*="success"]');
                const errorMessage = document.querySelector('.error, .alert, [class*="error"], .basket-item-error');
                
                if (errorMessage && errorMessage.offsetParent !== null && errorMessage.textContent.trim()) {
                    return {
                        success: false,
                        error: `Bet placement failed: ${errorMessage.textContent.trim()}`
                    };
                }
                
                if (successMessage && successMessage.offsetParent !== null) {
                    return {
                        success: true,
                        message: `Bet placed successfully: ${successMessage.textContent.trim()}`
                    };
                }
                
                // Check if betslip is cleared (bet was placed)
                const remainingBets = document.querySelectorAll('.basket-item');
                if (remainingBets.length === 0) {
                    return {
                        success: true,
                        message: 'Bet placed successfully - betslip cleared'
                    };
                }
                
                return {
                    success: true,
                    message: 'Bet placement initiated - no immediate feedback'
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"ZenitBet Place bet result: {result}")

# ==================== MAIN AUTOMATION FUNCTIONS ====================

async def zenitbet_balance_checker(executable_path, user_data_dir, login, password):
    """Check ZenitBet balance"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"zenitbet_balance_{timestamp}.json")
    
    print(f"🚀 Starting ZenitBet balance check...")
    print(f"💾 Results will be saved to: {temp_path}")
    
    try:
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state=None,
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
        
        # Agent 4: Balance Checker
        agent4 = Agent(
            task=f"""You are a ZenitBet balance checker. Follow these exact steps:

STEP 1: Navigate to ZenitBet
- Navigate to https://zenitbet.com
- Wait 3 seconds for page to load

STEP 2: Check login status
Look for these indicators:
- IF YOU SEE: Balance display with "RUB" (Russian Rubles) in top-right corner
  → User is LOGGED IN, proceed to STEP 4
- IF YOU SEE: "ENTRANCE" and "SIGN UP" buttons in top-right
  → User is LOGGED OUT, proceed to STEP 3

STEP 3: Login process (only if logged out)
- Use the login_with_zenitbet_credentials controller action
- Pass login="{login}" and password="{password}" as parameters
- This will:
  * Click "Entrance" button to open login modal
  * Fill login/phone and password fields
  * Submit the form

- Ask for human input using the controller action 'Ask human for help with issues' if it encounters captcha or other issues
- Wait 5 seconds for login to process
- Verify login by checking for balance display with "RUB"

STEP 4: Get balance (only if logged in)
- visually look in top-right corner to retrieve current balance
- Report the balance amount with RUB currency

Expected output format:
- is_logged_in: true/false
- balance: actual amount with currency (e.g., "RUB0.00")
- currency: "rub"
- error_message: any issues encountered""",
            llm=ChatAnthropic(model="claude-3-5-sonnet-20241022"),
            browser_session=browser_session,
            sensitive_data={
                "login": login,
                "password": password
            },
            controller=controller4,
        )
        
        history4 = await agent4.run()
        result4 = history4.final_result()
        balance = None
        
        if result4:
            balance = Balance.model_validate_json(result4)
            print("✅ ZenitBet balance check completed!")
        else:
            print("❌ ZenitBet balance check failed")
        
        # Save results
        combined_results = {
            "timestamp": timestamp,
            "platform": "ZenitBet",
            "balance": balance.model_dump() if balance else None
        }

        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=2, ensure_ascii=False)
        print(f"✅ Results saved to: {temp_path}")
        
        return balance
        
    except Exception as browser_error:
        print(f"❌ Browser session error: {browser_error}")
        return None
    finally:
        try:
            await browser_session.close()
            print("🧹 Browser session closed successfully")
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup warning: {cleanup_error}")

async def zenitbet_bet_placer(input_data: dict, executable_path: str, user_data_dir: str):
    """Place bet on ZenitBet"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"zenitbet_bet_{timestamp}.json")
    
    print(f"🚀 Starting ZenitBet bet placement...")
    print(f"💾 Results will be saved to: {temp_path}")
    
    try:
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state=None,
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
        
        # Agent 2: Bet Placement
        agent2 = Agent(
            task=f"""You will place a bet on ZenitBet based on this input data: {input_data}

KEY CONVERSIONS FOR ZENITBET:
- DNB1 (Draw No Bet Team 1) → "Win 1" for Team 1
- DNB2 (Draw No Bet Team 2) → "Win 2" for Team 2  
- "Win 1" and "Win 2" are ZenitBet's equivalent of DNB (Draw No Bet)

WORKFLOW: 
1. Go to the provided link: {input_data.get('link_bk')} this will be the only approach you take to find the event 
do not search for the event by name or league
2. Wait for page to load (3 seconds)
3. Based on bet_type_bk: {input_data.get('bet_type_bk', '')}, click the appropriate odds button:
   - If DNB1 → click odds for "Win 1" (Team 1: {input_data.get('team1_bk', '')})
   - If DNB2 → click odds for "Win 2" (Team 2: {input_data.get('team2_bk', '')})
4. Verify the bet was added to basket (betslip) on the right side
5. Stop after successful selection

Your output should include:
- The input data you processed
- Success/failure status
- Any errors encountered""",
            llm=ChatAnthropic(model="claude-3-5-sonnet-20241022"),
            browser_session=browser_session,
            controller=controller
        )
        
        history2 = await agent2.run()
        result2 = history2.final_result()
        bet_result = None
        
        if result2:
            bet_result = BetPlacementResult.model_validate_json(result2)
            print("✅ Agent 2 (Bet placement) completed!")
        else:
            print("❌ Agent 2 failed")
            return

        # Agent 3: Betslip Verification
        agent3 = Agent(
            task=f"""Verify the ZenitBet betslip status after bet placement.

Your task:
1. Use the count_zenitbet_betslip_games controller action
2. Verify exactly 1 game is in the betslip (basket)
3. If betslip is empty or has more than 1 game, return an error
4. Look for the bet details including match name and odds
5. Describe what you see in the betslip

Previous bet placement result: {bet_result.input_data if bet_result else 'No result'}""",
            llm=ChatAnthropic(model="claude-3-5-sonnet-20241022"),
            browser_session=browser_session,
            controller=controller3,
        )
        
        history3 = await agent3.run()
        result3 = history3.final_result()
        site_analysis = None
        
        if result3:
            site_analysis = SiteAnalysis.model_validate_json(result3)
            print("✅ Agent 3 (Betslip verification) completed!")
        else:
            print("❌ Agent 3 failed")

        # Agent 5: Bet Placer
        stake_amount = input_data.get('stake_amount')
        agent5 = Agent(
            task=f"""You are the persisitent final bet placer for ZenitBet. Your stake amount is {stake_amount}.

STEPS:
1. Visually check the basket has exactly 1 game
2. If basket is not empty, visually Fill  stake amount with stake={stake_amount} 
3. Wait 5 seconds for the potential returns to calculate
4. Visually verify the stake is filled correctly
5. If stake is filled, use 'Click ZenitBet place bet button' to place the bet

6. Wait for confirmation and report success or failure
7. Ask for human help if you encounter any issues

Expected final result:
- is_place_bet: true/false
- error_message: any issues encountered""",
            llm=ChatAnthropic(model="claude-3-5-sonnet-20241022"),
            browser_session=browser_session,
            controller=controller5,
        )
        
        history5 = await agent5.run()
        result5 = history5.final_result()
        placer_result = None
        
        if result5:
            placer_result = Placer.model_validate_json(result5)
            print("✅ Agent 5 (Bet placer) completed!")
        else:
            print("❌ Agent 5 failed")
        
        # Save combined results
        combined_results = {
            "timestamp": timestamp,
            "platform": "ZenitBet",
            "input_data": input_data,
            "bet_placement_result": bet_result.model_dump() if bet_result else None,
            "betslip_verification_result": site_analysis.model_dump() if site_analysis else None,
            "bet_placer_result": placer_result.model_dump() if placer_result else None,
            "workflow_summary": {
                "bet_placed": placer_result.is_place_bet if placer_result else False,
                "verification_completed": site_analysis is not None,
                "stake_amount": stake_amount
            }
        }

        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=2, ensure_ascii=False)
        print(f"✅ Results saved to: {temp_path}")
        
        return combined_results
        
    except Exception as browser_error:
        print(f"❌ Browser session error: {browser_error}")
        return None
    finally:
        try:
            await browser_session.close()
            print("🧹 Browser session closed successfully")
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup warning: {cleanup_error}")

# ==================== USAGE EXAMPLES ====================

# Example usage for balance check
async def main_balance_check():
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    #login = ""         # Replace with actual login/phone
    #password = "" 
    login = ""         # Replace with actual login/phone
    password = ""     # Replace with actual password
    
    balance = await zenitbet_balance_checker(executable_path, user_data_dir, login, password)
    if balance:
        print(f"✅ Balance check result: {balance.model_dump()}")
    else:
        print("❌ Balance check failed")

# Example usage for bet placement
async def main_bet_placement():
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    # Sample betting input for ZenitBet (from your arbitrage data)
    sample_input = {
         "profit": "0.47%",
    "sport": "TableTennis", 
    "event_time": "Jun 23, 10:00",
    "bookmaker": "Zenit",
    "team1_bk": "Marek Kostal",
    "team2_bk": "Vladimir Postelt", 
    "league_bk": "Table Tennis. Czech Republic. League Pro. Men",
    "bet_type_bk": "DNB2",
    "odd_bk": "1.6",
    "link_bk": "https://zenitbet.com/line/table-tennis/l_246592_czech-republic-league-pro-men/g_19775182_marek-kostal-vladimir-postelt",
    "stake_amount": 20.00 
    }
    
    result = await zenitbet_bet_placer(sample_input, executable_path, user_data_dir)
    if result:
        print(f"✅ Bet placement result: {result['workflow_summary']}")
    else:
        print("❌ Bet placement failed")

if __name__ == "__main__":
    # Choose which function to run
    asyncio.run(main_balance_check())      # For balance checking
    #asyncio.run(main_bet_placement())      # For bet placement
    print("ZenitBet automation system ready!")
    print("Update the login/password and run the desired function.")
    
    
    
