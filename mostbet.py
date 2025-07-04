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

# ==================== MOSTBET CONTROLLER ACTIONS ====================

@controller4.action('Login with MostBet credentials')
async def login_with_mostbet_credentials(browser, email: str, password: str) -> ActionResult:
    """Login to MostBet with provided credentials"""
    page = await browser.get_current_page()
    
    # Pass credentials as a single object argument
    result = await page.evaluate("""
        async (credentials) => {
            const { email, password } = credentials;
            try {
                // Check if already logged in by looking for balance
                const balanceElement = document.querySelector('.auto_user_balance');
                if (balanceElement && balanceElement.textContent.includes('$')) {
                    return {
                        success: true,
                        status: 'already_logged_in',
                        balance: balanceElement.textContent.trim()
                    };
                }
                
                // Look for login button to open modal
                const loginButton = document.querySelector('.auto_login') ||
                                  document.querySelector('button:contains("Log in")') ||
                                  document.querySelector('button:contains("LOG IN")');
                
                if (!loginButton) {
                    return {
                        success: false,
                        error: 'Login button not found'
                    };
                }
                
                // Click login button to open modal
                loginButton.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Find email and password inputs in the modal
                const emailInput = document.querySelector('#uReal') ||
                                 document.querySelector('input[placeholder*="email"]') ||
                                 document.querySelector('input[placeholder*="login"]');
                                 
                const passwordInput = document.querySelector('#pReal') ||
                                    document.querySelector('input[type="password"]');
                                    
                const submitButton = document.querySelector('.LoginForm_submitButton__FvjWH') ||
                                   document.querySelector('button[type="submit"]');
                
                if (!emailInput || !passwordInput) {
                    return {
                        success: false,
                        error: 'Login form inputs not found in modal'
                    };
                }
                
                // Clear and fill email
                emailInput.value = '';
                emailInput.focus();
                emailInput.value = email;
                emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                emailInput.dispatchEvent(new Event('change', { bubbles: true }));
                emailInput.blur();
                
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
                    const balanceAfterLogin = document.querySelector('.auto_user_balance');
                    
                    if (balanceAfterLogin && balanceAfterLogin.textContent.includes('$')) {
                        return {
                            success: true,
                            status: 'login_successful',
                            balance: balanceAfterLogin.textContent.trim()
                        };
                    } else {
                        // Check if login form is still visible (login failed)
                        const loginFormStillOpen = document.querySelector('.LoginForm_container__PPren');
                        if (loginFormStillOpen) {
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
    """, {"email": email, "password": password})
    
    return ActionResult(extracted_content=f"MostBet Login result: {result}")

@controller4.action('Ask human for help with issues')
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller4.action('Get MostBet balance')
async def get_mostbet_balance(browser) -> ActionResult:
    """Get current balance from MostBet account"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for balance elements
                const balanceElement = document.querySelector('.auto_user_balance') ||
                                     document.querySelector('.HeaderButton_button__jxKSC span');
                
                if (!balanceElement) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Balance element not found - user might not be logged in'
                    };
                }
                
                const balanceText = balanceElement.textContent.trim();
                
                // Check if balance contains $ symbol (MostBet uses $ for balance)
                if (!balanceText.includes('$')) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Balance does not contain $ symbol - user might not be logged in'
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
    
    return ActionResult(extracted_content=f"MostBet Balance result: {result}")

@controller3.action('Count MostBet betslip games')
async def count_mostbet_betslip_games(browser) -> ActionResult:
    """Count number of games in MostBet betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        () => {
            try {
                // Look for betslip items
                const betItems = document.querySelectorAll('.Bet_inner__Ykh2X');
                const betDetails = document.querySelectorAll('.auto_bet');
                const stakeInputs = document.querySelectorAll('.auto_amount');
                
                // Count using different methods for verification
                const betItemsCount = betItems.length;
                const detailsCount = betDetails.length;
                const inputsCount = stakeInputs.length;
                
                // Use the most reliable count
                const finalCount = Math.max(betItemsCount, detailsCount, inputsCount);
                
                // Check betslip visibility
                const betslipVisible = document.querySelector('.ExtendedCoupon_createCouponButton__NkbiX') !== null;
                
                return {
                    success: true,
                    bet_count: finalCount,
                    bet_items_count: betItemsCount,
                    details_count: detailsCount,
                    inputs_count: inputsCount,
                    betslip_visible: betslipVisible,
                    message: `${finalCount} games in MostBet betslip`
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"MostBet Betslip count: {result}")

@controller5.action('Fill MostBet stake amount')
async def fill_mostbet_stake_amount(browser, stake: float = 100) -> ActionResult:
    """Fill stake amount in MostBet betslip"""
    page = await browser.get_current_page()
    
    # Fixed: Pass stake as an object
    result = await page.evaluate("""
        async (params) => {
            const { stakeAmount } = params;
            try {
                // Look for stake input field
                const stakeInput = document.querySelector('.auto_amount') ||
                                 document.querySelector('input[inputmode="decimal"]') ||
                                 document.querySelector('input[pattern="\\\\d*"]');
                
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
                const potentialPayout = document.querySelector('.ExtendedCoupon_potentialPayout__qMIBD') ||
                                       document.querySelector('[class*="potential"]');
                const payoutValue = potentialPayout ? potentialPayout.textContent.trim() : 'Not calculated';
                
                return {
                    success: true,
                    message: `Stake set to ${stakeAmount}`,
                    stake_amount: stakeAmount,
                    potential_payout: payoutValue
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """, {"stakeAmount": stake})
    
    return ActionResult(extracted_content=f"MostBet Stake fill result: {result}")


@controller5.action('Click MostBet place bet button')
async def click_mostbet_place_bet(browser) -> ActionResult:
    """Click the Place Bet button in MostBet"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for place bet button
                const placeBetButton = document.querySelector('.auto_accept_bet') ||
                                     document.querySelector('.ExtendedCoupon_createCouponButton__NkbiX') ||
                                     document.querySelector('button:contains("Place a bet")');
                
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
                
                // Check for success/error messages or notifications
                const notification = document.querySelector('.notification, .alert, .toast, [class*="notification"]');
                const successMessage = document.querySelector('.success, .confirmation, [class*="success"]');
                const errorMessage = document.querySelector('.error, .alert-error, [class*="error"]');
                
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
                
                if (notification && notification.offsetParent !== null) {
                    return {
                        success: true,
                        message: `Bet placement notification: ${notification.textContent.trim()}`
                    };
                }
                
                // Check if betslip is cleared (bet was placed)
                const remainingBets = document.querySelectorAll('.Bet_inner__Ykh2X');
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
    
    return ActionResult(extracted_content=f"MostBet Place bet result: {result}")

# ==================== MAIN AUTOMATION FUNCTIONS ====================

async def mostbet_balance_checker(executable_path, user_data_dir, email, password):
    """Check MostBet balance"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("C:\\Users\\HP PC\\OneDrive\\Documents\\arb\\arb\\conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"mostbet_balance_{timestamp}.json")
    
    print(f"🚀 Starting MostBet balance check...")
    print(f"💾 Results will be saved to: {temp_path}")
    
    try:
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state='/tmp/mostbet_cookies.json',
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
        
        # Agent 4: Balance Checker
        agent4 = Agent(
            task=f"""You are a MostBet balance checker. Follow these exact steps:

STEP 1: Navigate to MostBet
- Navigate to https://mostbet.com
- Wait 3 seconds for page to load

STEP 2: Check login status
Look for these indicators:
- IF YOU SEE: Balance display with "$" symbol in top-right corner (.auto_user_balance)
  → User is LOGGED IN, proceed to STEP 4
- IF YOU SEE: "SIGN UP" and "LOG IN" buttons in top-right
  → User is LOGGED OUT, proceed to STEP 3

STEP 3: Login process (only if logged out)
- Use the login_with_mostbet_credentials controller action
- Pass email="{email}" and password="{password}" as parameters
- This will:
  * Click "LOG IN" button to open modal
  * Fill email input (#uReal) and password input (#pReal)
  * Submit the form

- Ask for human input using the controller action 'Ask human for help with issues' if it encounters captcha or other issues
- Wait 5 seconds for login to process

- Verify login by checking for balance display (.auto_user_balance)

STEP 4: Get balance (only if logged in)
- Use the get_mostbet_balance controller action to retrieve current balance
- Report the balance amount with $ currency

Expected output format:
- is_logged_in: true/false
- balance: actual amount with currency (e.g., "$0,00")
- error_message: any issues encountered""",
            llm=ChatOpenAI(model="gpt-4o"),
            browser_session=browser_session,
            sensitive_data={
                "email": email,
                "password": password
            },
            controller=controller4,
        )
        
        history4 = await agent4.run()
        result4 = history4.final_result()
        balance = None
        
        if result4:
            balance = Balance.model_validate_json(result4)
            print("✅ MostBet balance check completed!")
        else:
            print("❌ MostBet balance check failed")
        
        # Save results
        combined_results = {
            "timestamp": timestamp,
            "platform": "MostBet",
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

async def mostbet_bet_placer(input_data: dict, executable_path: str, user_data_dir: str):
    """Place bet on MostBet"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("C:\\Users\\HP PC\\OneDrive\\Documents\\arb\\arb\\conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"mostbet_bet_{timestamp}.json")
    
    print(f"🚀 Starting MostBet bet placement...")
    print(f"💾 Results will be saved to: {temp_path}")
    
    try:
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state='/tmp/mostbet_cookies.json',
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
        
        # Agent 2: Bet Placement
        agent2 = Agent(
            task=f"""You will place a bet on MostBet based on this input data: {input_data}

KEY CONVERSIONS FOR MOSTBET:
- DNB1 (Draw No Bet Team 1) → "Winner W1" for Team 1
- DNB2 (Draw No Bet Team 2) → "Winner W2" for Team 2
- "Winner" is MostBet's equivalent of DNB (Draw No Bet)

WORKFLOW: 
1. Go to the provided link: {input_data.get('link_bk', '')}
2. Wait for page to load (3 seconds)
3. Based on bet_type_bk: {input_data.get('bet_type_bk', '')}, click the appropriate odds button:
   - If DNB1 → Look for "Winner" section and click W1 odds for Team 1 ({input_data.get('team1_bk', '')})
   - If DNB2 → Look for "Winner" section and click W2 odds for Team 2 ({input_data.get('team2_bk', '')})
4. Verify the bet was added to betslip on the right side
5. Stop after successful selection

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
            task=f"""Verify the MostBet betslip status after bet placement.

Your task:
1. Use the count_mostbet_betslip_games controller action
2. Verify exactly 1 game is in the betslip
3. If betslip is empty or has more than 1 game, return an error
4. Look for the bet details including match name and odds in the betslip
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
            task=f"""You are the final bet placer for MostBet. Your stake amount is {stake_amount}.

STEPS:
1. Visually check the betslip has exactly 1 game
2. If betslip is not empty, use 'Fill MostBet stake amount' with stake={stake_amount}
3. Wait 2 seconds for the potential payout to calculate
4. Use 'Click MostBet place bet button' to place the bet
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
            "platform": "MostBet",
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
    executable_path='C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default'

    email = "blackcore053@gmail.com"     # Replace with actual email
    password = "$Oden3474"           # Replace with actual password
    
    balance = await mostbet_balance_checker(executable_path, user_data_dir, email, password)
    if balance:
        print(f"✅ Balance check result: {balance.model_dump()}")
    else:
        print("❌ Balance check failed")

# Example usage for bet placement
async def main_bet_placement():
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    # Sample betting input for MostBet (adapted from your arbitrage data)
    sample_input = {
        "profit": "0.61%",
        "sport": "Tennis",
        "event_time": "Jun 23, 11:00",
        "bookmaker": "MostBet",
        "team1_bk": "Bergs Z",
        "team2_bk": "Fonseca J",
        "league_bk": "ATP Eastbourne. Grass",
        "bet_type_bk": "DNB1",  # Will bet on Team 1 (Bergs Z) - Winner W1
        "odd_bk": "2.41",
        "link_bk": "https://mostbet.com/tennis-match-url", # Replace with actual MostBet match URL
        "stake_amount": 13
    }
    
    result = await mostbet_bet_placer(sample_input, executable_path, user_data_dir)
    if result:
        print(f"✅ Bet placement result: {result['workflow_summary']}")
    else:
        print("❌ Bet placement failed")

if __name__ == "__main__":
    # Choose which function to run
    asyncio.run(main_balance_check())      # For balance checking
    #asyncio.run(main_bet_placement())       # For bet placement
    print("MostBet automation system ready!")
    print("Update the email/password and run the desired function.")