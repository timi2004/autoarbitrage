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

# ==================== NAIRABET CONTROLLER ACTIONS ====================

@controller4.action('Login with NairaBet credentials')
async def login_with_nairabet_credentials(browser, username: str, password: str) -> ActionResult:
    """Login to NairaBet with provided credentials"""
    page = await browser.get_current_page()
    
    # Embed credentials in the JavaScript to avoid parameter passing issues
    script = f"""
        async () => {{
            try {{
                const username = "{username.replace('"', '\\"')}";
                const password = "{password.replace('"', '\\"')}";
                
                // Check if already logged in by looking for Account button
                const accountButton = document.querySelector('button .header-button__label');
                if (accountButton && accountButton.textContent.includes('Account')) {{
                    return {{
                        success: true,
                        status: 'already_logged_in',
                        message: 'User is already logged in'
                    }};
                }}
                
                // Look for login button in header
                const loginButtons = document.querySelectorAll('button .header-button__label');
                let loginButton = null;
                for (let btn of loginButtons) {{
                    if (btn.textContent.includes('Login')) {{
                        loginButton = btn;
                        break;
                    }}
                }}
                
                if (!loginButton) {{
                    return {{
                        success: false,
                        error: 'Login button not found in header'
                    }};
                }}
                
                // Click login button to open modal
                loginButton.closest('button').click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Look for login form inputs in the modal
                const usernameInput = document.querySelector('input[name="login"]') ||
                                    document.querySelector('input[maxlength="100"]');
                                    
                const passwordInput = document.querySelector('input[name="password"]') ||
                                    document.querySelector('input[type="password"]');
                                    
                // Look for submit button in different ways
                const submitButtons = document.querySelectorAll('button');
                let submitButton = null;
                for (let btn of submitButtons) {{
                    const innerText = btn.querySelector('.form-button__inner');
                    if (innerText && innerText.textContent.includes('Login Securely')) {{
                        submitButton = btn;
                        break;
                    }}
                }}
                
                if (!submitButton) {{
                    submitButton = document.querySelector('.form-button--primary');
                }}
                
                if (!usernameInput || !passwordInput) {{
                    return {{
                        success: false,
                        error: 'Login form inputs not found in modal'
                    }};
                }}
                
                // Clear and fill username/email
                usernameInput.value = '';
                usernameInput.focus();
                usernameInput.value = username;
                usernameInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                usernameInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                usernameInput.blur();
                
                // Wait between fields
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Clear and fill password
                passwordInput.value = '';
                passwordInput.focus();
                passwordInput.value = password;
                passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                passwordInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                passwordInput.blur();
                
                // Wait for validation
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Click submit button
                if (submitButton) {{
                    submitButton.click();
                    
                    // Wait for login to process
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    
                    // Check if login was successful by looking for Account button
                    const accountButtons = document.querySelectorAll('button .header-button__label');
                    let accountAfterLogin = null;
                    for (let btn of accountButtons) {{
                        if (btn.textContent.includes('Account')) {{
                            accountAfterLogin = btn;
                            break;
                        }}
                    }}
                    
                    if (accountAfterLogin) {{
                        return {{
                            success: true,
                            status: 'login_successful',
                            message: 'Login successful - Account button visible'
                        }};
                    }} else {{
                        // Check if login modal is still open (login failed)
                        const modalStillOpen = document.querySelector('[data-skeleton="login"]');
                        if (modalStillOpen) {{
                            return {{
                                success: false,
                                status: 'login_failed',
                                error: 'Login modal still open after attempt'
                            }};
                        }}
                    }}
                }}
                
                return {{
                    success: false,
                    status: 'unknown',
                    error: 'Could not determine login status'
                }};
                
            }} catch (error) {{
                return {{
                    success: false,
                    error: error.message
                }};
            }}
        }}
    """
    
    result = await page.evaluate(script)
    
    return ActionResult(extracted_content=f"NairaBet Login result: {result}")

@controller4.action('Ask human for help with issues')   
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller4.action('Get NairaBet balance')
async def get_nairabet_balance(browser) -> ActionResult:
    """Get current balance from NairaBet account"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // First check if Account button is present (indicates logged in)
                const accountButtons = document.querySelectorAll('button .header-button__label');
                let accountButton = null;
                for (let btn of accountButtons) {
                    if (btn.textContent.includes('Account')) {
                        accountButton = btn;
                        break;
                    }
                }
                
                if (!accountButton) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Account button not found - user might not be logged in'
                    };
                }
                
                // Click Account button to open balance menu
                accountButton.closest('button').click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Look for balance elements in the user menu
                const totalBalanceElement = document.querySelector('.money-details__value') ||
                                          document.querySelector('[class*="balance"]');
                
                if (!totalBalanceElement) {
                    return {
                        success: false,
                        is_logged_in: true,
                        error: 'Balance element not found in account menu'
                    };
                }
                
                const balanceText = totalBalanceElement.textContent.trim();
                
                // Check if balance contains Nigerian Naira
                if (!balanceText.includes('NGN')) {
                    return {
                        success: false,
                        is_logged_in: true,
                        error: 'Balance does not contain NGN currency'
                    };
                }
                
                return {
                    success: true,
                    is_logged_in: true,
                    balance: balanceText,
                    message: 'Balance retrieved successfully'
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"NairaBet Balance result: {result}")

@controller3.action('Count NairaBet betslip games')
async def count_nairabet_betslip_games(browser) -> ActionResult:
    """Count number of games in NairaBet betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        () => {
            try {
                // Look for betslip content
                const betslipContent = document.querySelector('.betslip-content');
                if (!betslipContent) {
                    return {
                        success: true,
                        bet_count: 0,
                        betslip_visible: false,
                        message: 'Betslip not visible or empty'
                    };
                }
                
                // Look for betslip selections
                const betslipSelections = document.querySelectorAll('.betslip-selection');
                const betOutcomes = document.querySelectorAll('.betslip-selection__outcome-name');
                const stakeInputs = document.querySelectorAll('.form-stake input');
                
                // Count using different methods for verification
                const selectionsCount = betslipSelections.length;
                const outcomesCount = betOutcomes.length;
                const stakesCount = stakeInputs.length;
                
                // Use the most reliable count
                const finalCount = Math.max(selectionsCount, outcomesCount, stakesCount);
                
                return {
                    success: true,
                    bet_count: finalCount,
                    selections_count: selectionsCount,
                    outcomes_count: outcomesCount,
                    stakes_count: stakesCount,
                    betslip_visible: true,
                    message: `${finalCount} games in NairaBet betslip`
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"NairaBet Betslip count: {result}")

@controller5.action('Fill NairaBet stake amount')
async def fill_nairabet_stake_amount(browser, stake: float = 100) -> ActionResult:
    """Fill stake amount in NairaBet betslip"""
    page = await browser.get_current_page()
    
    # Embed stake amount in the JavaScript
    script = f"""
        async () => {{
            try {{
                const stakeAmount = {stake};
                
                // Look for stake input field
                const stakeInput = document.querySelector('.form-stake input') ||
                                 document.querySelector('.betslip-stake input') ||
                                 document.querySelector('input[placeholder="0.00"]');
                
                if (!stakeInput) {{
                    return {{
                        success: false,
                        error: 'Stake input field not found'
                    }};
                }}
                
                // Clear and set stake amount
                stakeInput.value = '';
                stakeInput.focus();
                stakeInput.value = stakeAmount.toString();
                stakeInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                stakeInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                stakeInput.blur();
                
                // Wait for calculation
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                // Check if potential winnings were calculated
                const winningsElement = document.querySelector('.betslip-selection__outcome-value') ||
                                      document.querySelector('[class*="possible"]') ||
                                      document.querySelector('[class*="winnings"]');
                const winningsValue = winningsElement ? winningsElement.textContent.trim() : 'Not calculated';
                
                return {{
                    success: true,
                    message: `Stake set to ${{stakeAmount}} NGN`,
                    stake_amount: stakeAmount,
                    potential_winnings: winningsValue
                }};
                
            }} catch (error) {{
                return {{
                    success: false,
                    error: error.message
                }};
            }}
        }}
    """
    
    result = await page.evaluate(script)
    
    return ActionResult(extracted_content=f"NairaBet Stake fill result: {result}")

@controller5.action('Click NairaBet place bet button')
async def click_nairabet_place_bet(browser) -> ActionResult:
    """Click the Place Bet button in NairaBet"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for place bet button
                const placeBetButton = document.querySelector('.betslip-bet-button') ||
                                     document.querySelector('button:has(.form-button__inner:contains("Place Bet"))') ||
                                     document.querySelector('[class*="place"][class*="bet"]');
                
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
                const remainingBets = document.querySelectorAll('.betslip-selection');
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
    
    return ActionResult(extracted_content=f"NairaBet Place bet result: {result}")

# ==================== MAIN AUTOMATION FUNCTIONS ====================

async def nairabet_balance_checker(executable_path, user_data_dir, username, password):
    """Check NairaBet balance"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"nairabet_balance_{timestamp}.json")
    
    print(f"🚀 Starting NairaBet balance check...")
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
            task=f"""You are a NairaBet balance checker. Follow these exact steps:

STEP 1: Navigate to NairaBet
- Navigate to https://www.nairabet.com
- Wait 3 seconds for page to load

STEP 2: Check login status
Look for these indicators:
- IF YOU SEE: "Account" button in top-right header
  → User is LOGGED IN, proceed to STEP 4
- IF YOU SEE: "Login" and "Join" buttons in top-right header
  → User is LOGGED OUT, proceed to STEP 3

STEP 3: Login process (only if logged out)
- Use the login_with_nairabet_credentials controller action
- Pass username="{username}" and password="{password}" as parameters
- This will:
  * Click "Login" button to open modal
  * Fill username/email and password in the form
  * Submit the form

- Ask for human input using the controller action 'Ask human for help with issues' if it encounters captcha or other issues
- Wait 5 seconds for login to process
- Verify login by checking for "Account" button

STEP 4: Get balance (only if logged in)
- Use the get_nairabet_balance controller action to retrieve current balance
- This will click the Account button and read the Total Balance from the menu
- Report the balance amount with NGN currency

Expected output format:
- is_logged_in: true/false
- balance: actual amount with currency (e.g., "69449.60 ")
- currency: "NGN"
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
            print("✅ NairaBet balance check completed!")
        else:
            print("❌ NairaBet balance check failed")
        
        # Save results
        combined_results = {
            "timestamp": timestamp,
            "platform": "NairaBet",
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

async def nairabet_bet_placer(input_data: dict, executable_path: str, user_data_dir: str):
    """Place bet on NairaBet"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"nairabet_bet_{timestamp}.json")
    
    print(f"🚀 Starting NairaBet bet placement...")
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
            task=f"""You will place a bet on NairaBet based on this input data: {input_data}

KEY CONVERSIONS FOR NAIRABET:
- DNB1 (Draw No Bet Team 1) → "Match Winner" for Team 1
- DNB2 (Draw No Bet Team 2) → "Match Winner" for Team 2
- "Match Winner" is NairaBet's equivalent of DNB

WORKFLOW: 
1. Go to the provided link: {input_data.get('link_bk', '')}
2. Wait for page to load (3 seconds)
3. Based on bet_type_bk: {input_data.get('bet_type_bk', '')}, click the appropriate odds button:
   - If DNB1 → click odds for Team 1 ({input_data.get('team1_bk', '')}) under "Match Winner"
   - If DNB2 → click odds for Team 2 ({input_data.get('team2_bk', '')}) under "Match Winner"
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
            task=f"""Verify the NairaBet betslip status after bet placement.

Your task:
1. Use the count_nairabet_betslip_games controller action
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
            task=f"""You are the final bet placer for NairaBet. Your stake amount is {stake_amount}.

STEPS:
1. Visually check the betslip has exactly 1 game
2. If betslip is not empty, use 'Fill NairaBet stake amount' with the given stake amount
3. Wait 2 seconds for the potential winnings to calculate
4. Use 'Click NairaBet place bet button' to place the bet
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
            "platform": "NairaBet",
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
    
    username = ""        # Replace with actual username/email
    password = ""        # Replace with actual password
    
    balance = await nairabet_balance_checker(executable_path, user_data_dir, username, password)
    if balance:
        print(f"✅ Balance check result: {balance.model_dump()}")
    else:
        print("❌ Balance check failed")

# Example usage for bet placement
async def main_bet_placement():
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    # Sample betting input for NairaBet (from your arbitrage data)
    sample_input = {
        
        "profit": "0.48%",
        "sport": "Baseball",
        "event_time": "Jul 04, 10:35",
        "bookmaker1": "NairaBet",
        "team1_bk1": "Rakuten Monkeys",
        "team2_bk1": "Fubon Guardians",
        "league_bk1": "Baseball. China. Chinese Professional Baseball League",
        "bet_type_bk1": "DNB2",
        "odd_bk1": "2.5",
        "link_bk1": "https://nairabet.com/event/14758410",
        "stake_amount": 100
    }
    
    result = await nairabet_bet_placer(sample_input, executable_path, user_data_dir)
    if result:
        print(f"✅ Bet placement result: {result['workflow_summary']}")
    else:
        print("❌ Bet placement failed")

if __name__ == "__main__":
    # Choose which function to run
    #asyncio.run(main_balance_check())      # For balance checking
    asyncio.run(main_bet_placement())      # For bet placement
    print("NairaBet automation system ready!")
    print("Update the username/password and run the desired function.")