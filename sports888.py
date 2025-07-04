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

# ==================== 888SPORT CONTROLLER ACTIONS ====================

@controller4.action('Login with 888sport credentials')
async def login_with_888sport_credentials(browser, username: str, password: str ) -> ActionResult:
    """Login to 888sport with provided credentials"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (credentials) => {
            const { username, password } = credentials;
            try {
                // Check if already logged in by looking for balance
                const balanceElement = document.querySelector('[data-testid="uc-current-balance-header"]');
                if (balanceElement && balanceElement.textContent.includes('US$')) {
                    return {
                        success: true,
                        status: 'already_logged_in',
                        balance: balanceElement.textContent.trim()
                    };
                }
                
                // Look for login button to open modal
                const loginButton = document.querySelector('[data-testid="topMenuaCloginButton"]') ||
                                  document.querySelector('button:contains("LOG IN")') ||
                                  document.querySelector('.login-btn');
                
                if (!loginButton) {
                    return {
                        success: false,
                        error: 'Login button not found'
                    };
                }
                
                // Click login button to open modal
                loginButton.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Find username and password inputs in the modal
                const usernameInput = document.querySelector('#rlLoginUsername') ||
                                    document.querySelector('input[placeholder*="Username"]') ||
                                    document.querySelector('input[type="text"]');
                                 
                const passwordInput = document.querySelector('#rlLoginPassword') ||
                                    document.querySelector('input[type="password"]');
                                    
                const submitButton = document.querySelector('#rlLoginSubmit') ||
                                   document.querySelector('button:contains("Login")');
                
                if (!usernameInput || !passwordInput) {
                    return {
                        success: false,
                        error: 'Login form inputs not found in modal'
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
                
                // Click submit button
                if (submitButton) {
                    submitButton.click();
                    
                    // Wait for login to process
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    
                    // Check if login was successful
                    const balanceAfterLogin = document.querySelector('[data-testid="uc-current-balance-header"]');
                    
                    if (balanceAfterLogin && balanceAfterLogin.textContent.includes('US$')) {
                        return {
                            success: true,
                            status: 'login_successful',
                            balance: balanceAfterLogin.textContent.trim()
                        };
                    } else {
                        // Check if modal is still open (login failed)
                        const modalStillOpen = document.querySelector('#rlLoginFormWrapper');
                        if (modalStillOpen && modalStillOpen.style.display !== 'none') {
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
    """, {"username": username, "password": password})
    
    return ActionResult(extracted_content=f"888sport Login result: {result}")

@controller4.action('Ask human for help with issues')   
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller4.action('Get 888sport balance')
async def get_888sport_balance(browser) -> ActionResult:
    """Get current balance from 888sport account"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for balance elements
                const balanceElement = document.querySelector('[data-testid="uc-current-balance-header"]');
                
                if (!balanceElement) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Balance element not found - user might not be logged in'
                    };
                }
                
                const balanceText = balanceElement.textContent.trim();
                
                // Check if balance contains US$ symbol
                if (!balanceText.includes('US$')) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Balance does not contain US$ symbol - user might not be logged in'
                    };
                }
                
                return {
                    success: true,
                    is_logged_in: true,
                    balance: balanceText
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"888sport Balance result: {result}")

@controller3.action('Count 888sport betslip games')
async def count_888sport_betslip_games(browser) -> ActionResult:
    """Count number of games in 888sport betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        () => {
            try {
                // Look for betslip items using 888sport specific selectors
                const betSelections = document.querySelectorAll('[data-test-id="betslip;selection-body"]');
                const betslipItems = document.querySelectorAll('.fullslip__selection-body');
                const stakeFields = document.querySelectorAll('[data-test-id="betslip;stake-field"]');
                
                // Count using different methods for verification
                const selectionsCount = betSelections.length;
                const itemsCount = betslipItems.length;
                const stakesCount = stakeFields.length;
                
                // Use the most reliable count
                const finalCount = Math.max(selectionsCount, itemsCount, stakesCount);
                
                // Check betslip visibility
                const betslipVisible = document.querySelector('.fullslip__selection-body') !== null;
                
                return {
                    success: true,
                    bet_count: finalCount,
                    selections_count: selectionsCount,
                    items_count: itemsCount,
                    stakes_count: stakesCount,
                    betslip_visible: betslipVisible,
                    message: `${finalCount} games in 888sport betslip`
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"888sport Betslip count: {result}")

@controller5.action('Fill 888sport stake amount')
async def fill_888sport_stake_amount(browser, stake: float = 100) -> ActionResult:
    """Fill stake amount in 888sport betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (stakeData) => {
            const stakeAmount = stakeData.stake;
            try {
                // Look for stake input field using 888sport specific selectors
                const stakeInput = document.querySelector('[data-test-id="betslip;stake-view"]') ||
                                 document.querySelector('.fullslip__stake-value') ||
                                 document.querySelector('input[placeholder*="0.00"]');
                
                if (!stakeInput) {
                    return {
                        success: false,
                        error: 'Stake input field not found'
                    };
                }
                
                // Remove readonly attribute if present
                stakeInput.removeAttribute('readonly');
                
                // Clear and set stake amount
                stakeInput.value = '';
                stakeInput.focus();
                stakeInput.value = stakeAmount.toString();
                stakeInput.dispatchEvent(new Event('input', { bubbles: true }));
                stakeInput.dispatchEvent(new Event('change', { bubbles: true }));
                stakeInput.blur();
                
                // Wait for calculation
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                // Check if potential returns were calculated
                const returnsElement = document.querySelector('[data-test-id="betslip;returns"]') ||
                                     document.querySelector('.fullslip__payout-price');
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
    """, {"stake": stake})
    
    return ActionResult(extracted_content=f"888sport Stake fill result: {result}")

@controller5.action('Click 888sport place bet button')
async def click_888sport_place_bet(browser) -> ActionResult:
    """Click the Place Bet button in 888sport"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for place bet button using 888sport specific selectors
                const placeBetButton = document.querySelector('[data-test-id="betslip;place-bet"]') ||
                                     document.querySelector('.fullslip__cta--place-bet') ||
                                     document.querySelector('[data-spectate-product="new-betslip;deposit"]');
                
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
                const errorMessage = document.querySelector('.error, .alert, [class*="error"]');
                
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
                
                // Check if betslip is cleared (bet was placed)
                const remainingBets = document.querySelectorAll('[data-test-id="betslip;selection-body"]');
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
    
    return ActionResult(extracted_content=f"888sport Place bet result: {result}")

# ==================== MAIN AUTOMATION FUNCTIONS ====================

async def sport888_balance_checker(executable_path, user_data_dir, username, password):
    """Check 888sport balance"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"888sport_balance_{timestamp}.json")
    
    print(f"🚀 Starting 888sport balance check...")
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
            task=f"""You are a 888sport balance checker. Follow these exact steps:

STEP 1: Navigate to 888sport
- Navigate to https://www.888sport.com
- Wait 3 seconds for page to load

STEP 2: Check login status
Look for these indicators:
- IF YOU SEE: Balance display with "US$" symbol in top-right (data-testid="uc-current-balance-header")
  → User is LOGGED IN, proceed to STEP 4
- IF YOU SEE: "LOG IN" and "JOIN NOW" buttons in top-right
  → User is LOGGED OUT, proceed to STEP 3

STEP 3: Login process (only if logged out)
- Use the login_with_888sport_credentials controller action
- Pass username="{username}" and password="{password}" as parameters
- This will:
  * Click "LOG IN" button to open modal
  * Fill username and password fields
  * Submit the form

- Ask for human input using the controller action 'Ask human for help with issues' if it encounters captcha or other issues
- Wait 5 seconds for login to process

- Verify login by checking for balance display

STEP 4: Get balance (only if logged in)
- Use the get_888sport_balance controller action to retrieve current balance
- Report the balance amount with US$ currency

Expected output format:
- is_logged_in: true/false
- balance: actual amount with currency (e.g., "US$0.00")
- currency: "USD"
- error_message: any issues encountered""",
            llm=ChatAnthropic(model="claude-3-5-sonnet-20241022"),
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
            print("✅ 888sport balance check completed!")
        else:
            print("❌ 888sport balance check failed")
        
        # Save results
        combined_results = {
            "timestamp": timestamp,
            "platform": "888sport",
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

async def sport888_bet_placer(input_data: dict, executable_path: str, user_data_dir: str):
    """Place bet on 888sport"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"888sport_bet_{timestamp}.json")
    
    print(f"🚀 Starting 888sport bet placement...")
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
            task=f"""You will place a bet on 888sport based on this input data: {input_data}

KEY CONVERSIONS FOR 888SPORT:
- DNB1 (Draw No Bet Team 1) → "To Win Match" for Team 1
- DNB2 (Draw No Bet Team 2) → "To Win Match" for Team 2
- "To Win Match" is 888sport's equivalent of DNB

WORKFLOW: 
1. Go to the provided link: {input_data.get('link_bk', '')}
2. Wait for page to load (3 seconds)
3. Based on bet_type_bk: {input_data.get('bet_type_bk', '')}, click the appropriate odds button:
   - If DNB1 → click odds for Team 1 ({input_data.get('team1_bk', '')})
   - If DNB2 → click odds for Team 2 ({input_data.get('team2_bk', '')})
4. Verify the bet was added to betslip on the right side
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
            task=f"""Verify the 888sport betslip status after bet placement.

Your task:
1. Use the count_888sport_betslip_games controller action
2. Verify exactly 1 game is in the betslip
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
        stake_amount = input_data.get('stake_amount', 100)
        agent5 = Agent(
            task=f"""You are the final bet placer for 888sport. Your stake amount is {stake_amount}.

STEPS:
1. Visually check the betslip has exactly 1 game
2. If betslip is not empty, use 'Fill 888sport stake amount' with stake={stake_amount}
3. Wait 2 seconds for the potential returns to calculate
4. Use 'Click 888sport place bet button' to place the bet
5. Wait for confirmation and report success or failure

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
            "platform": "888sport",
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
    
    username = ""     # Your 888sport username
    password = ""            # Your 888sport password
    
    balance = await sport888_balance_checker(executable_path, user_data_dir, username, password)
    if balance:
        print(f"✅ Balance check result: {balance.model_dump()}")
    else:
        print("❌ Balance check failed")

# Example usage for bet placement
async def main_bet_placement():
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    # Sample betting input for 888sport (from your arbitrage data)
    sample_input = {
        "profit": "0.41%",
        "sport": "Tennis",
        "event_time":"Jun 23, 14:30",
        "bookmaker": "888sport",
        "team1_bk":  "Victoria Azarenka",
        "team2_bk":  "Laura Siegemund",
        "league_bk":"Tennis. WTA Bad Homburg",
        "bet_type_bk": "DNB1",  # Will bet on Team 1 (Janmagnus Johnson)
        "odd_bk":  "1.333",
        "link_bk": "https://888sport.com/en/tennis/germany/wta-bad-homburg/victoria-azarenka-vs-laura-siegemund-e-5979447",
        "stake_amount": 88
    }
    
    result = await sport888_bet_placer(sample_input, executable_path, user_data_dir)
    if result:
        print(f"✅ Bet placement result: {result['workflow_summary']}")
    else:
        print("❌ Bet placement failed")

if __name__ == "__main__":
    # Choose which function to run
    #asyncio.run(main_balance_check())      # For balance checking
    asyncio.run(main_bet_placement())      # For bet placement
    print("888sport automation system ready!")
    print("Update the username/password and run the desired function.")