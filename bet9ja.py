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

# ==================== BET9JA CONTROLLER ACTIONS ====================

@controller4.action('Login with Bet9ja credentials')
async def login_with_bet9ja_credentials(browser, username: str, password: str) -> ActionResult:
    """Login to Bet9ja with provided credentials"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (credentials) => {
            const { username, password } = credentials;
            try {
                // Check if already logged in by looking for My Account dropdown
                const myAccountElement = document.querySelector('.myaccount__details, .acc-dd__menu');
                if (myAccountElement) {
                    const balanceElement = document.querySelector('.myaccount__details .txt-cut span[style*="unset"]');
                    if (balanceElement && balanceElement.parentElement.textContent.includes('₦')) {
                        return {
                            success: true,
                            status: 'already_logged_in',
                            balance: balanceElement.parentElement.textContent.trim()
                        };
                    }
                }
                
                // Look for login button to open modal
                const loginButton = document.querySelector('.btn-primary-m.btn-login') ||
                                  document.querySelector('.btn-login') ||
                                  document.querySelector('[title="Login"]');
                
                if (!loginButton) {
                    return {
                        success: false,
                        error: 'Login button not found'
                    };
                }
                
                // Click login button to open modal
                loginButton.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Find username/mobile and password inputs in the modal
                const usernameInput = document.querySelector('#username') ||
                                    document.querySelector('input[placeholder*="Mobile"]') ||
                                    document.querySelector('input[placeholder*="Username"]');
                const passwordInput = document.querySelector('#password') ||
                                    document.querySelector('input[type="password"]');
                const submitButton = document.querySelector('.btn-primary-l') ||
                                   document.querySelector('.form .btn');
                
                if (!usernameInput || !passwordInput) {
                    return {
                        success: false,
                        error: 'Login form inputs not found in modal'
                    };
                }
                
                // Clear and fill username/mobile
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
                    
                    // Check if login was successful by looking for My Account
                    const balanceAfterLogin = document.querySelector('.myaccount__details .txt-cut');
                    
                    if (balanceAfterLogin && balanceAfterLogin.textContent.includes('₦')) {
                        return {
                            success: true,
                            status: 'login_successful',
                            balance: balanceAfterLogin.textContent.trim()
                        };
                    } else {
                        // Check if login form is still visible (login failed)
                        const formStillVisible = document.querySelector('.form') ||
                                               document.querySelector('#username') ||
                                               document.querySelector('#password');
                        if (formStillVisible) {
                            return {
                                success: false,
                                status: 'login_failed',
                                error: 'Login form still visible after attempt'
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
    
    return ActionResult(extracted_content=f"Bet9ja Login result: {result}")

@controller4.action('Ask human for help with issues')
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller4.action('Get Bet9ja balance')
async def get_bet9ja_balance(browser) -> ActionResult:
    """Get current balance from Bet9ja account"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for balance elements in My Account dropdown
                const balanceElement = document.querySelector('.myaccount__details .txt-cut span[style*="unset"]') ||
                                     document.querySelector('.myaccount__details .txt-cut');
                
                const withdrawableText = document.querySelector('.myaccount__heading');
                
                if (!balanceElement) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Balance element not found - user might not be logged in'
                    };
                }
                
                const balanceText = balanceElement.parentElement ? 
                                  balanceElement.parentElement.textContent.trim() : 
                                  balanceElement.textContent.trim();
                
                // Check if balance contains Nigerian Naira symbol
                if (!balanceText.includes('₦')) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Balance does not contain ₦ symbol - user might not be logged in'
                    };
                }
                
                return {
                    success: true,
                    is_logged_in: true,
                    balance: balanceText,
                    has_withdrawable_section: !!withdrawableText
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"Bet9ja Balance result: {result}")

@controller3.action('Count Bet9ja betslip games')
async def count_bet9ja_betslip_games(browser) -> ActionResult:
    """Count number of games in Bet9ja betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        () => {
            try {
                // Look for betslip items using various selectors
                const betslipMatches = document.querySelectorAll('.betslip__match');
                const betslipCheckboxes = document.querySelectorAll('.betslip__cb-input');
                const stakeInputs = document.querySelectorAll('.betslip input[type="number"], .betslip .input[placeholder="stake"]');
                
                // Count using different methods for verification
                const matchesCount = betslipMatches.length;
                const checkboxesCount = betslipCheckboxes.length;
                const stakesCount = stakeInputs.length;
                
                // Use the most reliable count
                const finalCount = Math.max(matchesCount, checkboxesCount, stakesCount);
                
                // Check betslip visibility
                const betslipVisible = document.querySelector('.betslip__body, .betslip') !== null;
                
                // Get match details if any
                const matchDetails = [];
                betslipMatches.forEach(match => {
                    const matchName = match.querySelector('strong')?.textContent || 'Unknown match';
                    const odds = match.querySelector('.betslip__match-odds .txt-primary')?.textContent || 'Unknown odds';
                    matchDetails.push(`${matchName} - ${odds}`);
                });
                
                return {
                    success: true,
                    bet_count: finalCount,
                    matches_count: matchesCount,
                    checkboxes_count: checkboxesCount,
                    stakes_count: stakesCount,
                    betslip_visible: betslipVisible,
                    match_details: matchDetails,
                    message: `${finalCount} games in Bet9ja betslip`
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"Bet9ja Betslip count: {result}")

@controller5.action('Fill Bet9ja stake amount')
async def fill_bet9ja_stake_amount(browser, stake: float) -> ActionResult:
    """Fill stake amount in Bet9ja betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (stakeData) => {
            const { stakeAmount } = stakeData;
            try {
                // Look for stake input field
                const stakeInput = document.querySelector('.betslip input[type="number"]') ||
                                 document.querySelector('.betslip .input[placeholder="stake"]') ||
                                 document.querySelector('input.input[type="number"]');
                
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
                stakeInput.blur();
                
                // Wait for calculation
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                // Check if potential returns were calculated
                const returnsElement = document.querySelector('.betslip__potential-win, .potential-win, .total-return');
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
    """, {"stakeAmount": stake})
    
    return ActionResult(extracted_content=f"Bet9ja Stake fill result: {result}")

@controller5.action('Click Bet9ja place bet button')
async def click_bet9ja_place_bet(browser) -> ActionResult:
    """Click the Place Bet button in Bet9ja"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for place bet button
                const placeBetButton = document.querySelector('#betslip_buttons_placebet') ||
                                     document.querySelector('.btn-green-l span:contains("Place Bet")') ||
                                     document.querySelector('button:contains("Place Bet")') ||
                                     document.querySelector('.btn:contains("Place Bet")');
                
                if (!placeBetButton) {
                    return {
                        success: false,
                        error: 'Place bet button not found'
                    };
                }
                
                const buttonToClick = placeBetButton.closest('.btn') || placeBetButton;
                
                // Check if button is disabled
                if (buttonToClick.disabled || 
                    buttonToClick.classList.contains('disabled') ||
                    buttonToClick.style.display === 'none') {
                    return {
                        success: false,
                        error: 'Place bet button is disabled or hidden'
                    };
                }
                
                // Click the button
                buttonToClick.click();
                
                // Wait for response
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                // Check for success/error messages
                const successMessage = document.querySelector('.success, .confirmation, .alert-success, [class*="success"]');
                const errorMessage = document.querySelector('.error, .alert-danger, .alert-error, [class*="error"]');
                
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
                const remainingBets = document.querySelectorAll('.betslip__match');
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
    
    return ActionResult(extracted_content=f"Bet9ja Place bet result: {result}")

# ==================== MAIN AUTOMATION FUNCTIONS ====================

async def bet9ja_balance_checker(executable_path, user_data_dir, username, password):
    """Check Bet9ja balance"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"bet9ja_balance_{timestamp}.json")
    
    print(f"🚀 Starting Bet9ja balance check...")
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
            task=f"""You are a Bet9ja balance checker. Follow these exact steps:

STEP 1: Navigate to Bet9ja
- Navigate to https://bet9ja.com
- Wait 3 seconds for page to load

STEP 2: Check login status
Look for these indicators:
- IF YOU SEE: "My Account" button with balance display containing "₦" (Nigerian Naira) in top-right
  → User is LOGGED IN, proceed to STEP 4
- IF YOU SEE: "Login" and "Register" buttons in top-right
  → User is LOGGED OUT, proceed to STEP 3

STEP 3: Login process (only if logged out)
- Use the login_with_bet9ja_credentials controller action
- Pass username="{username}" and password="{password}" as parameters
- This will:
  * Click "Login" button to open modal
  * Fill mobile number/username and password
  * Submit the form

- Ask for human input using the controller action 'Ask human for help with issues' if it encounters captcha or other issues
- Wait 5 seconds for login to process
- Verify login by checking for My Account dropdown with balance

STEP 4: Get balance (only if logged in)
- Use the get_bet9ja_balance controller action to retrieve current balance
- Report the balance amount with ₦ currency

Expected output format:
- is_logged_in: true/false
- balance: actual amount with currency (e.g., " 0.00")
- currency : "NGN"
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
            print("✅ Bet9ja balance check completed!")
        else:
            print("❌ Bet9ja balance check failed")
        
        # Save results
        combined_results = {
            "timestamp": timestamp,
            "platform": "Bet9ja",
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

async def bet9ja_bet_placer(input_data: dict, executable_path: str, user_data_dir: str):
    """Place bet on Bet9ja"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"bet9ja_bet_{timestamp}.json")
    
    print(f"🚀 Starting Bet9ja bet placement...")
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
            task=f"""You will place a bet on Bet9ja based on this input data: {input_data}

KEY CONVERSIONS FOR BET9JA:
DNB1 → "1" in the "1-2"  market
DNB2 → "2" in the "1-2"market 


WORKFLOW: 
1. Go to the provided link: {input_data.get('link_bk', '')}
- Do not scroll down
2. Wait for page to load (3 seconds)
3. Based on bet_type_bk: {input_data.get('bet_type_bk', '')}, click the appropriate odds button:
   - If DNB1 → Look for "1-2" market and click "1" (first team: {input_data.get('team1_bk', '')})
   - If DNB2 → Look for ""1-2" market and click "2" (second team: {input_data.get('team2_bk', '')})
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
            task=f"""Verify the Bet9ja betslip status after bet placement.

Your task:
1. Use the count_bet9ja_betslip_games controller action
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
            task=f"""You are the final bet placer for Bet9ja. Your stake amount is the given stake amount.

STEPS:
1. Visually check the betslip has exactly 1 game
2. If betslip is not empty, use 'Fill Bet9ja stake amount' with the given stake amount
3. Wait 2 seconds for the potential returns to calculate
-make sure stakes amount matches given stake amount, if it does not match visually input the stake.(this is very important)
4. Use 'Click Bet9ja place bet button' to place the bet
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
            "platform": "Bet9ja",
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
    
    username = ""    # Your Bet9ja username
    password = ""            # Your Bet9ja password
    
    balance = await bet9ja_balance_checker(executable_path, user_data_dir, username, password)
    if balance:
        print(f"✅ Balance check result: {balance.model_dump()}")
    else:
        print("❌ Balance check failed")

# Example usage for bet placement
async def main_bet_placement():
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    # Sample betting input for Bet9ja (from your arbitrage data)
    sample_input = {
       "profit": "0.48%",
        "sport": "Baseball",
        "event_time": "Jul 04, 10:35",
        "bookmaker": "Bet9ja",
        "team1_bk": "Rakuten Monkeys",
        "team2_bk": "Fubon Guardians",
        "league_bk": "Baseball. Chinese Taipei. CPBL",
        "bet_type_bk": "DNB1",
        "odd_bk": "1.68",
        "link_bk": "https://sports.bet9ja.com/event/618948749",
        "stake_amount": 300
    }
    
    result = await bet9ja_bet_placer(sample_input, executable_path, user_data_dir)
    if result:
        print(f"✅ Bet placement result: {result['workflow_summary']}")
    else:
        print("❌ Bet placement failed")

if __name__ == "__main__":
    # Choose which function to run
    #asyncio.run(main_balance_check())      # For balance checking
    asyncio.run(main_bet_placement())      # For bet placement
    print("Bet9ja automation system ready!")
    print("Update the username/password and run the desired function.")