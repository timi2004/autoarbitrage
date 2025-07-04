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

# ==================== 1WIN CONTROLLER ACTIONS ====================

@controller4.action('Login with 1win credentials')
async def login_with_1win_credentials(browser, email: str, password: str) -> ActionResult:
    """Login to 1win with provided credentials"""
    page = await browser.get_current_page()
    
    result = await page.evaluate(f"""
        async () => {{
            try {{
                const email = "{email}";
                const password = "{password}";
                
                // Check if already logged in by looking for balance
                const balanceElement = document.querySelector('.HeaderBalanceInfo_balance_Gw9TU');
                if (balanceElement && balanceElement.textContent.trim() !== '') {{
                    return {{
                        success: true,
                        status: 'already_logged_in',
                        balance: balanceElement.textContent.trim()
                    }};
                }}
                
                // Look for login button to open modal
                const loginButton = document.querySelector('[data-pw="HEADER-AUTH-BUTTON"]') ||
                                  document.querySelector('button:contains("Login")') ||
                                  document.querySelector('.header-button.login');
                
                if (!loginButton) {{
                    return {{
                        success: false,
                        error: 'Login button not found'
                    }};
                }}
                
                // Click login button to open modal
                loginButton.click();
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Look for "Email" tab and click it
                const emailTab = document.querySelector('.LoginFormDividedTabs_active_D8BS7') ||
                               document.querySelector('button:contains("Email")') ||
                               document.querySelector('[data-pw*="EMAIL"]');
                
                if (emailTab) {{
                    emailTab.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }}
                
                // Find email and password inputs in the modal
                const emailInput = document.querySelector('input[type="email"]') ||
                                 document.querySelector('.VFluidLabelInput_input_y1IK9[value*="@"]') ||
                                 document.querySelector('input[placeholder*="Email"]');
                                 
                const passwordInput = document.querySelector('input[type="password"]') ||
                                    document.querySelector('input[type="text"][value*="$"]') ||
                                    document.querySelector('.VFluidLabelInput_input_y1IK9:not([type="email"])');
                                    
                const submitButton = document.querySelector('[data-pw="LOGIN-MODAL-LOGIN-BUTTON"]') ||
                                   document.querySelector('button:contains("Login")') ||
                                   document.querySelector('.modal-button');
                
                if (!emailInput || !passwordInput) {{
                    return {{
                        success: false,
                        error: 'Login form inputs not found in modal'
                    }};
                }}
                
                // Clear and fill email
                emailInput.value = '';
                emailInput.focus();
                emailInput.value = email;
                emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                emailInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                emailInput.blur();
                
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
                    
                    // Check if login was successful
                    const balanceAfterLogin = document.querySelector('.HeaderBalanceInfo_balance_Gw9TU');
                    
                    if (balanceAfterLogin && balanceAfterLogin.textContent.trim() !== '') {{
                        return {{
                            success: true,
                            status: 'login_successful',
                            balance: balanceAfterLogin.textContent.trim()
                        }};
                    }} else {{
                        // Check if modal is still open (login failed)
                        const modalStillOpen = document.querySelector('.LoginModal') ||
                                             document.querySelector('[data-pw="LOGIN-MODAL"]');
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
    """)
    
    return ActionResult(extracted_content=f"1win Login result: {result}")

@controller4.action('Ask human for help with issues')   
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller4.action('Get 1win balance')
async def get_1win_balance(browser) -> ActionResult:
    """Get current balance from 1win account"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for balance elements
                const balanceElement = document.querySelector('.HeaderBalanceInfo_balance_Gw9TU');
                const currencyElement = document.querySelector('.HeaderBalanceInfo_name_u2NJV');
                
                if (!balanceElement) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Balance element not found - user might not be logged in'
                    };
                }
                
                const balanceText = balanceElement.textContent.trim();
                const currency = currencyElement ? currencyElement.textContent.trim() : 'NGN';
                
                // Check if balance is empty or shows login required
                if (!balanceText || balanceText === '' || balanceText === '0.00' && !currency) {
                    return {
                        success: false,
                        is_logged_in: false,
                        error: 'Balance is empty - user might not be logged in'
                    };
                }
                
                const fullBalance = `${currency} ${balanceText}`;
                
                return {
                    success: true,
                    is_logged_in: true,
                    balance: fullBalance,
                    raw_balance: balanceText,
                    currency: currency
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"1win Balance result: {result}")

@controller3.action('Count 1win betslip games')
async def count_1win_betslip_games(browser) -> ActionResult:
    """Count number of games in 1win betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        () => {
            try {
                // Look for betslip items
                const betChoices = document.querySelectorAll('._root_1nvhv_2');
                const competitorElements = document.querySelectorAll('._competitors_1nvhv_20');
                const removeButtons = document.querySelectorAll('._removeSelection_1nvhv_56');
                
                // Count using different methods for verification
                const choicesCount = betChoices.length;
                const competitorsCount = competitorElements.length;
                const removeButtonsCount = removeButtons.length;
                
                // Use the most reliable count
                const finalCount = Math.max(choicesCount, competitorsCount, removeButtonsCount);
                
                // Check betslip visibility
                const betslipVisible = document.querySelector('.Betslip') !== null ||
                                     document.querySelector('[class*="betslip"]') !== null;
                
                return {
                    success: true,
                    bet_count: finalCount,
                    choices_count: choicesCount,
                    competitors_count: competitorsCount,
                    remove_buttons_count: removeButtonsCount,
                    betslip_visible: betslipVisible,
                    message: `${finalCount} games in 1win betslip`
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"1win Betslip count: {result}")

@controller5.action('Fill 1win stake amount')
async def fill_1win_stake_amount(browser, stake: float = 100) -> ActionResult:
    """Fill stake amount in 1win betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (stakeAmount) => {
            try {
                // Look for stake input field
                const stakeInput = document.querySelector('input[data-qa="amount"]') ||
                                 document.querySelector('input[placeholder*="Bet amount"]') ||
                                 document.querySelector('._input_hxkjw_33');
                
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
                const possibleWinElement = document.querySelector('[class*="possible"]') ||
                                         document.querySelector('[class*="win"]') ||
                                         document.querySelector('[class*="return"]');
                const returnsValue = possibleWinElement ? possibleWinElement.textContent.trim() : 'Not calculated';
                
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
    
    return ActionResult(extracted_content=f"1win Stake fill result: {result}")

@controller5.action('Click 1win place bet button')
async def click_1win_place_bet(browser) -> ActionResult:
    """Click the Place Bet button in 1win"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for place bet button
                const placeBetButton = document.querySelector('button._root_1xrr7_2._root_8tevd_2._variantAccent_8tevd_88._sizeL_8tevd_45') ||
                                     document.querySelector('button:contains("Place a bet")') ||
                                     document.querySelector('[class*="place"]');
                
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
                const remainingBets = document.querySelectorAll('._root_1nvhv_2');
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
    
    return ActionResult(extracted_content=f"1win Place bet result: {result}")

# ==================== MAIN AUTOMATION FUNCTIONS ====================

async def onewin_balance_checker(executable_path, user_data_dir, email, password):
    """Check 1win balance"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"1win_balance_{timestamp}.json")
    
    print(f"🚀 Starting 1win balance check...")
    print(f"💾 Results will be saved to: {temp_path}")
    
    try:
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state='/tmp/1win_cookies.json',
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
        
        # Agent 4: Balance Checker
        agent4 = Agent(
            task=f"""You are a 1win balance checker. Follow these exact steps:

STEP 1: Navigate to 1win
- Navigate to https://1win.com
- Wait 3 seconds for page to load

STEP 2: Check login status
Look for these indicators:
- IF YOU SEE: Balance display with currency (NGN) in the HeaderBalanceInfo_balance_Gw9TU class
  → User is LOGGED IN, proceed to STEP 4
- IF YOU SEE: "Login" and "Registration" buttons in top-right
  → User is LOGGED OUT, proceed to STEP 3

STEP 3: Login process (only if logged out)
- Use the login_with_1win_credentials controller action
- Pass email="{email}" and password="{password}" as parameters
- This will:
  * Click "Login" button to open modal
  * Select "Email" tab for email login
  * Fill email and password in the modal form
  * Submit the form

- Ask for human input using the controller action 'Ask human for help with issues' if it encounters captcha or other issues
- Wait 5 seconds for login to process

- Verify login by checking for balance display

STEP 4: Get balance (only if logged in)
- Use the get_1win_balance controller action to retrieve current balance
- Report the balance amount with NGN currency

Expected output format:
- is_logged_in: true/false
- balance: actual amount with currency (e.g., "NGN 0.00")
-currency: "NGN"
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
            print("✅ 1win balance check completed!")
        else:
            print("❌ 1win balance check failed")
        
        # Save results
        combined_results = {
            "timestamp": timestamp,
            "platform": "1win",
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

async def onewin_bet_placer(input_data: dict, executable_path: str, user_data_dir: str):
    """Place bet on 1win"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"1win_bet_{timestamp}.json")
    
    print(f"🚀 Starting 1win bet placement...")
    print(f"💾 Results will be saved to: {temp_path}")
    
    try:
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state='/tmp/1win_cookies.json',
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
        
        # Agent 2: Bet Placement
        agent2 = Agent(
            task=f"""You will place a bet on 1win based on this input data: {input_data}

KEY CONVERSIONS FOR 1WIN:
- DNB1 (Draw No Bet Team 1) → "Winner" for Team 1 (as shown in screenshots)
- DNB2 (Draw No Bet Team 2) → "Winner" for Team 2
- "Winner" is 1win's equivalent of DNB

WORKFLOW: 
1. Go to the provided link: {input_data.get('link_bk', '')}
2. Wait for page to load (3 seconds)
3. Based on bet_type_bk: {input_data.get('bet_type_bk', '')}, click the appropriate odds button:
   - If DNB1 → click "Winner" odds for Team 1 ({input_data.get('team1_bk', '')})
   - If DNB2 → click "Winner" odds for Team 2 ({input_data.get('team2_bk', '')})
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
            task=f"""Verify the 1win betslip status after bet placement.

Your task:
1. Use the count_1win_betslip_games controller action
2. Verify exactly 1 game is in the betslip
3. If betslip is empty or has more than 1 game, return an error
4. Look for the bet details including match name and odds in _root_1nvhv_2 elements
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
            task=f"""You are the final bet placer for 1win. Your stake amount is {stake_amount}.

STEPS:
1. Visually check the betslip has exactly 1 game
2. If betslip is not empty, use 'Fill 1win stake amount' with stake={stake_amount}
3. Wait 2 seconds for the potential returns to calculate
4. Use 'Click 1win place bet button' to place the bet
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
            "platform": "1win",
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
    user_data_dir='C:\\Users\\leg\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    email = "@gmail.com"     # Replace with actual email
    password = ""              # Replace with actual password
    
    balance = await onewin_balance_checker(executable_path, user_data_dir, email, password)
    if balance:
        print(f"✅ Balance check result: {balance.model_dump()}")
    else:
        print("❌ Balance check failed")

# Example usage for bet placement
async def main_bet_placement():
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\leg\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    # Sample betting input for 1win (from your arbitrage data)
    sample_input = {
        "profit": "0.85%",
        "sport": "Table Tennis",
        "event_time": "Jun 23, 9:30",
        "bookmaker": "1win",
        "team1_bk": "Maksym Hubenko",
        "team2_bk": "Ivan Fedoryshyn",
        "league_bk": "Table Tennis. Men. Setka Cup",
        "bet_type_bk": "DNB2",  # Will bet on Team 2 (Ivan Fedoryshyn)
        "odd_bk": "1.29",
        "link_bk": "https://1win.com/en/betting/table-tennis/maksym-hubenko-ivan-fedoryshyn",
        "stake_amount": 100
    }
    
    result = await onewin_bet_placer(sample_input, executable_path, user_data_dir)
    if result:
        print(f"✅ Bet placement result: {result['workflow_summary']}")
    else:
        print("❌ Bet placement failed")

if __name__ == "__main__":
    # Choose which function to run
    asyncio.run(main_balance_check())      # For balance checking
    #asyncio.run(main_bet_placement())      # For bet placement
    print("1win automation system ready!")
    print("Update the email/password and run the desired function.")