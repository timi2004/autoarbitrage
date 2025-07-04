from langchain_openai import ChatOpenAI  
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

# ==================== BETKING CONTROLLER ACTIONS ====================

@controller4.action('Login with BetKing credentials')
async def login_with_betking_credentials(browser, username: str, password: str ) -> ActionResult:
    """Login to BetKing with provided credentials"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (username, password) => {
            try {
                // Check if already logged in by looking for balance or welcome message
                const balanceElement = document.querySelector('.main-menu-balance span') ||
                                     document.querySelector('[ng-click="authCtrl.goToAccountBalance()"]');
                const welcomeElement = document.querySelector('*:contains("Welcome")');
                
                if (balanceElement && balanceElement.textContent.includes('₦')) {
                    return {
                        success: true,
                        status: 'already_logged_in',
                        balance: balanceElement.textContent.trim()
                    };
                }
                
                // Look for login panel (should be visible when not logged in)
                const loginPanel = document.querySelector('.login-panel');
                if (!loginPanel || loginPanel.style.display === 'none') {
                    return {
                        success: false,
                        error: 'Login panel not found or user might already be logged in'
                    };
                }
                
                // Find username and password inputs
                const usernameInput = document.querySelector('#txtLoginUsername') ||
                                    document.querySelector('input[placeholder*="Username"]') ||
                                    document.querySelector('input[placeholder*="Mobile"]');
                                    
                const passwordInput = document.querySelector('#txtLoginPassword') ||
                                    document.querySelector('input[type="password"]');
                                    
                const loginButton = document.querySelector('.login-button') ||
                                  document.querySelector('button:contains("Login")');
                
                if (!usernameInput || !passwordInput || !loginButton) {
                    return {
                        success: false,
                        error: 'Login form elements not found'
                    };
                }
                
                // Clear and fill username
                usernameInput.value = '';
                usernameInput.focus();
                usernameInput.value = username;
                usernameInput.dispatchEvent(new Event('input', { bubbles: true }));
                usernameInput.dispatchEvent(new Event('change', { bubbles: true }));
                usernameInput.blur();
                
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
                
                // Click login button
                loginButton.click();
                
                // Wait for login to process
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                // Check if login was successful by looking for balance or welcome message
                const balanceAfterLogin = document.querySelector('.main-menu-balance span') ||
                                        document.querySelector('[ng-click="authCtrl.goToAccountBalance()"]');
                const welcomeAfterLogin = document.querySelector('*:contains("Welcome")');
                
                if (balanceAfterLogin && balanceAfterLogin.textContent.includes('₦')) {
                    return {
                        success: true,
                        status: 'login_successful',
                        balance: balanceAfterLogin.textContent.trim()
                    };
                } else if (welcomeAfterLogin) {
                    return {
                        success: true,
                        status: 'login_successful',
                        balance: 'Balance element not found but welcome message present'
                    };
                } else {
                    // Check if login panel is still visible (login failed)
                    const loginPanelAfter = document.querySelector('.login-panel');
                    if (loginPanelAfter && loginPanelAfter.style.display !== 'none') {
                        return {
                            success: false,
                            status: 'login_failed',
                            error: 'Login panel still visible after attempt'
                        };
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
    """, username, password)
    
    return ActionResult(extracted_content=f"BetKing Login result: {result}")

@controller4.action('Ask human for help with issues')   
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller4.action('Get BetKing balance')
async def get_betking_balance(browser) -> ActionResult:
    """Get current balance from BetKing account"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for balance elements in different possible locations
                const balanceElement = document.querySelector('.main-menu-balance span') ||
                                     document.querySelector('[ng-click="authCtrl.goToAccountBalance()"]') ||
                                     document.querySelector('.view-balance-container span');
                
                const welcomeElement = document.querySelector('*:contains("Welcome")');
                const logoutElement = document.querySelector('*:contains("LOGOUT")');
                
                if (!balanceElement && !welcomeElement) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Balance element and welcome message not found - user might not be logged in'
                    };
                }
                
                let balanceText = '';
                if (balanceElement) {
                    balanceText = balanceElement.textContent.trim();
                    
                    // Check if balance contains Nigerian Naira symbol
                    if (!balanceText.includes('₦')) {
                        return {
                            success: false,
                            is_logged_in: false,
                            error: 'Balance does not contain ₦ symbol - user might not be logged in'
                        };
                    }
                } else if (welcomeElement) {
                    balanceText = 'Balance element not found but user appears logged in';
                }
                
                return {
                    success: true,
                    is_logged_in: true,
                    balance: balanceText,
                    has_welcome_message: !!welcomeElement,
                    has_logout_button: !!logoutElement
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"BetKing Balance result: {result}")

@controller3.action('Count BetKing betslip games')
async def count_betking_betslip_games(browser) -> ActionResult:
    """Count number of games in BetKing betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        () => {
            try {
                // Look for betslip items using different selectors
                const betslipContainer = document.querySelector('.coupon-tools') ||
                                       document.querySelector('[class*="betslip"]') ||
                                       document.querySelector('[class*="coupon"]');
                
                const oddDetailsRows = document.querySelectorAll('.oddDetailsRow');
                const currentBetslipSelections = document.querySelectorAll('[class*="selection"]');
                const closeButtons = document.querySelectorAll('.closeOdd');
                
                // Count using different methods for verification
                const oddRowsCount = oddDetailsRows.length;
                const selectionsCount = currentBetslipSelections.length;
                const closeButtonsCount = closeButtons.length;
                
                // Use the most reliable count
                const finalCount = Math.max(oddRowsCount, selectionsCount, closeButtonsCount);
                
                // Check betslip visibility
                const betslipVisible = betslipContainer !== null;
                
                // Look for selections indicator
                const selectionsText = document.querySelector('*:contains("Selections:")');
                let displayedCount = 0;
                if (selectionsText) {
                    const match = selectionsText.textContent.match(/Selections:\\s*(\\d+)/);
                    if (match) {
                        displayedCount = parseInt(match[1]);
                    }
                }
                
                return {
                    success: true,
                    bet_count: finalCount,
                    odds_rows_count: oddRowsCount,
                    selections_count: selectionsCount,
                    close_buttons_count: closeButtonsCount,
                    displayed_count: displayedCount,
                    betslip_visible: betslipVisible,
                    message: `${finalCount} games in BetKing betslip`
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"BetKing Betslip count: {result}")

@controller5.action('Fill BetKing stake amount')
async def fill_betking_stake_amount(browser, stake: float = 100) -> ActionResult:
    """Fill stake amount in BetKing betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (stakeAmount) => {
            try {
                // Look for stake input field
                const stakeInput = document.querySelector('#txtAmount') ||
                                 document.querySelector('input[ng-model*="StakeGrossValue"]') ||
                                 document.querySelector('input[type="text"][class*="amount"]');
                
                if (!stakeInput) {
                    return {
                        success: false,
                        error: 'Stake input field not found'
                    };
                }
                
                // Clear and set stake amount
                stakeInput.value = '';
                stakeInput.focus();
                stakeInput.value = stakeAmount.toString();
                stakeInput.dispatchEvent(new Event('input', { bubbles: true }));
                stakeInput.dispatchEvent(new Event('change', { bubbles: true }));
                stakeInput.dispatchEvent(new Event('blur', { bubbles: true }));
                stakeInput.blur();
                
                // Wait for calculation
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                // Check if potential returns were calculated
                const returnsElement = document.querySelector('[class*="returns"]') ||
                                     document.querySelector('[class*="payout"]');
                const returnsValue = returnsElement ? returnsElement.textContent.trim() : 'Not calculated';
                
                return {
                    success: true,
                    message: `Stake set to ${stakeAmount}`,
                    stake_amount: stakeAmount,
                    potential_returns: returnsValue
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """, stake)
    
    return ActionResult(extracted_content=f"BetKing Stake fill result: {result}")

@controller5.action('Click BetKing place bet button')
async def click_betking_place_bet(browser) -> ActionResult:
    """Click the Place Bet button in BetKing"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for place bet button
                const placeBetButton = document.querySelector('.placeBet') ||
                                     document.querySelector('button[ng-click*="placeBet"]') ||
                                     document.querySelector('button:contains("Proceed")');
                
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
                
                // Check for success/error messages or confirmation dialogs
                const successMessage = document.querySelector('.success, .confirmation, [class*="success"]');
                const errorMessage = document.querySelector('.error, .alert, [class*="error"]');
                const confirmationDialog = document.querySelector('[class*="confirm"], [class*="dialog"]');
                
                if (errorMessage && errorMessage.offsetParent !== null) {
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
                
                if (confirmationDialog && confirmationDialog.offsetParent !== null) {
                    return {
                        success: true,
                        message: 'Bet placement confirmation dialog appeared'
                    };
                }
                
                // Check if betslip is cleared (bet was placed)
                const remainingBets = document.querySelectorAll('.oddDetailsRow');
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
    
    return ActionResult(extracted_content=f"BetKing Place bet result: {result}")

# ==================== MAIN AUTOMATION FUNCTIONS ====================

async def betking_balance_checker(executable_path, user_data_dir, username, password):
    """Check BetKing balance"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"betking_balance_{timestamp}.json")
    
    print(f"🚀 Starting BetKing balance check...")
    print(f"💾 Results will be saved to: {temp_path}")
    
    try:
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state='/tmp/betking_cookies.json',
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
        
        # Agent 4: Balance Checker
        agent4 = Agent(
            task=f"""You are a BetKing balance checker. Follow these exact steps:

STEP 1: Navigate to BetKing
- Navigate to https://www.betking.com/sports
- Wait 3 seconds for page to load

STEP 2: Check login status
Look for these indicators:
- IF YOU SEE: Balance display with "₦" (Nigerian Naira) symbol in top-right header
  → User is LOGGED IN, proceed to STEP 4
- IF YOU SEE: Username/Mobile and Password input fields with "LOGIN" button in top-right
  → User is LOGGED OUT, proceed to STEP 3
- IF YOU SEE: "Welcome [username]" message in header
  → User is LOGGED IN, proceed to STEP 4

STEP 3: Login process (only if logged out)
- Use the login_with_betking_credentials controller action
- Pass username="{username}" and password="{password}" as parameters
- This will:
  * Find username input field (id="txtLoginUsername")
  * Find password input field (id="txtLoginPassword") 
  * Fill credentials and click login button

- Ask for human input using the controller action 'Ask human for help with issues' if it encounters captcha or other issues
- Wait 5 seconds for login to process

- Verify login by checking for balance display or welcome message

STEP 4: Get balance (only if logged in)
- Use the get_betking_balance controller action to retrieve current balance
- Report the balance amount with ₦ currency

Expected output format:
- is_logged_in: true/false
- balance: actual amount with currency (e.g., "₦1,000")
- Currency : "NGN"
- error_message: any issues encountered""",
            llm=ChatOpenAI(model="gpt-4o"),
            browser_session=browser_session,
            sensitive_data={
                "username": username,
                "password": password
            },
            controller=controller4,
        )
        
        history4 = await agent4.run()
        result4 = history4.final_result()
        balance = None
        
        if result4:
            balance = Balance.model_validate_json(result4)
            print("✅ BetKing balance check completed!")
        else:
            print("❌ BetKing balance check failed")
        
        # Save results
        combined_results = {
            "timestamp": timestamp,
            "platform": "BetKing",
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

async def betking_bet_placer(input_data: dict, executable_path: str, user_data_dir: str):
    """Place bet on BetKing"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"betking_bet_{timestamp}.json")
    
    print(f"🚀 Starting BetKing bet placement...")
    print(f"💾 Results will be saved to: {temp_path}")
    
    try:
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state='/tmp/betking_cookies.json',
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
        
        # Agent 2: Bet Placement
        agent2 = Agent(
            task=f"""You will place a bet on BetKing based on this input data: {input_data}

KEY CONVERSIONS FOR BETKING:
- DNB1 (Draw No Bet Team 1) → "1-2" market, select "1" option for Team 1
- DNB2 (Draw No Bet Team 2) → "1-2" market, select "2" option for Team 2
- "1-2" is BetKing's equivalent of DNB (1 = Team 1 wins, 2 = Team 2 wins)

WORKFLOW: 
1. Go to the provided link: {input_data.get('link_bk', '')}
2. Wait for page to load (3 seconds)
3. Look for the "1-2" betting market row
4. Based on bet_type_bk: {input_data.get('bet_type_bk', '')}, click the appropriate odds button:
   - If DNB1 → click odds button for "1" (Team 1: {input_data.get('team1_bk', '')})
   - If DNB2 → click odds button for "2" (Team 2: {input_data.get('team2_bk', '')})
5. Verify the bet was added to betslip on the right side
6. Stop after successful selection

Your output should include:
- The input data you processed
- Success/failure status
- Any errors encountered""",
            llm=ChatOpenAI(model="gpt-4o"),
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
            task=f"""Verify the BetKing betslip status after bet placement.

Your task:
1. Use the count_betking_betslip_games controller action
2. Verify exactly 1 game is in the betslip
3. If betslip is empty or has more than 1 game, return an error
4. Look for the bet details including match name and odds
5. Describe what you see in the betslip

Previous bet placement result: {bet_result.input_data if bet_result else 'No result'}""",
            llm=ChatOpenAI(model="gpt-4o"),
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
        stake_amount = input_data.get('stake_amount', 100)
        agent5 = Agent(
            task=f"""You are the final bet placer for BetKing. Your stake amount is {stake_amount}.

STEPS:
1. Visually check the betslip has exactly 1 game
2. If betslip is not empty, use 'Fill BetKing stake amount' with stake={stake_amount}
3. Wait 2 seconds for the potential returns to calculate
4. Use 'Click BetKing place bet button' to place the bet
5. Wait for confirmation and report success or failure

Expected final result:
- is_place_bet: true/false
- error_message: any issues encountered""",
            llm=ChatOpenAI(model="gpt-4o"),
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
            "platform": "BetKing",
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
    
    username = ""     # Replace with actual username/mobile
    password = "$"        # Replace with actual password
    
    balance = await betking_balance_checker(executable_path, user_data_dir, username, password)
    if balance:
        print(f"✅ Balance check result: {balance.model_dump()}")
    else:
        print("❌ Balance check failed")

# Example usage for bet placement
async def main_bet_placement():
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    # Sample betting input for BetKing (from your arbitrage data)
    sample_input = {
        "profit": "0.61%",
        "sport": "Tennis",
        "event_time": "Jun 23, 11:00",
        "bookmaker": "BetKing",
        "team1_bk": "Muller, Alexandre",
        "team2_bk": "Safiullin, Roman",
        "league_bk": "ATP - Mallorca",
        "bet_type_bk": "DNB1",  # Will bet on Team 1 (Muller, Alexandre)
        "odd_bk": "2.42",
        "link_bk": "https://web.betking.com/sports/tennis/atp-mallorca",  # Replace with actual link
        "stake_amount": 150
    }
    
    result = await betking_bet_placer(sample_input, executable_path, user_data_dir)
    if result:
        print(f"✅ Bet placement result: {result['workflow_summary']}")
    else:
        print("❌ Bet placement failed")

if __name__ == "__main__":
    # Choose which function to run
    asyncio.run(main_balance_check())      # For balance checking
    #asyncio.run(main_bet_placement())      # For bet placement
    print("BetKing automation system ready!")
    print("Update the username/password and run the desired function.")