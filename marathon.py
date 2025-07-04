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

# ==================== MARATHONBET CONTROLLER ACTIONS ====================

@controller4.action('Login with Marathonbet credentials')
async def login_with_marathonbet_credentials(browser, email: str, password: str ) -> ActionResult:
    """Login to Marathonbet with provided credentials"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (email, password) => {
            try {
                // Check if already logged in by looking for balance
                const balanceElement = document.querySelector('[data-test="headerLoggedBalanceValue"]');
                if (balanceElement && balanceElement.textContent.includes('₦')) {
                    return {
                        success: true,
                        status: 'already_logged_in',
                        balance: balanceElement.textContent.trim()
                    };
                }
                
                // Look for login button to open modal
                const loginButton = document.querySelector('[data-test="headerAuthLogin"]') ||
                                  document.querySelector('button:contains("Log In")') ||
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
                
                // Look for "Other login" tab and click it (for email login)
                const otherLoginTab = document.querySelector('[data-test="authDialogLoginByAnotherLoginTab"]') ||
                                    document.querySelector('button:contains("Other login")');
                
                if (otherLoginTab) {
                    otherLoginTab.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
                
                // Find email and password inputs in the modal
                const emailInput = document.querySelector('[data-test="authDialogLogin"]') ||
                                 document.querySelector('input[placeholder*="Email"]') ||
                                 document.querySelector('input[type="text"]');
                                 
                const passwordInput = document.querySelector('[data-test="authDialogPassword"]') ||
                                    document.querySelector('input[type="password"]');
                                    
                const submitButton = document.querySelector('[data-test="authDialogSubmit"]') ||
                                   document.querySelector('button:contains("Log In")');
                
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
                    const balanceAfterLogin = document.querySelector('[data-test="headerLoggedBalanceValue"]');
                    
                    if (balanceAfterLogin && balanceAfterLogin.textContent.includes('₦')) {
                        return {
                            success: true,
                            status: 'login_successful',
                            balance: balanceAfterLogin.textContent.trim()
                        };
                    } else {
                        // Check if modal is still open (login failed)
                        const modalStillOpen = document.querySelector('[data-test="authDialog"]');
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
    """, email, password)
    
    return ActionResult(extracted_content=f"Marathonbet Login result: {result}")

@controller4.action('Ask human for help with issues')   # pass allowed_domains= or page_filter= to limit actions to certain pages
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)


@controller3.action('Count Marathonbet betslip games')
async def count_marathonbet_betslip_games(browser) -> ActionResult:
    """Count number of games in Marathonbet betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        () => {
            try {
                // Look for betslip items
                const betChoices = document.querySelectorAll('.betslip-content__choice');
                const betSlipItems = document.querySelectorAll('[data-stake]');
                const stakeInputs = document.querySelectorAll('input[id*="stake_"]');
                
                // Count using different methods for verification
                const choicesCount = betChoices.length;
                const stakesCount = betSlipItems.length;
                const inputsCount = stakeInputs.length;
                
                // Use the most reliable count
                const finalCount = Math.max(choicesCount, stakesCount, inputsCount);
                
                // Check betslip visibility
                const betslipVisible = document.querySelector('.betslip-content') !== null;
                
                return {
                    success: true,
                    bet_count: finalCount,
                    choices_count: choicesCount,
                    stakes_count: stakesCount,
                    inputs_count: inputsCount,
                    betslip_visible: betslipVisible,
                    message: `${finalCount} games in Marathonbet betslip`
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"Marathonbet Betslip count: {result}")

@controller5.action('Fill Marathonbet stake amount')
async def fill_marathonbet_stake_amount(browser, stake: float = 100) -> ActionResult:
    """Fill stake amount in Marathonbet betslip"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (stakeAmount) => {
            try {
                // Look for stake input field
                const stakeInput = document.querySelector('input[id*="stake_"]') ||
                                 document.querySelector('input[placeholder*="Stake"]') ||
                                 document.querySelector('.betslip-content__choice__stake input');
                
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
                const returnsElement = document.querySelector('.betslip-content__choice__returns');
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
    
    return ActionResult(extracted_content=f"Marathonbet Stake fill result: {result}")

@controller5.action('Click Marathonbet place bet button')
async def click_marathonbet_place_bet(browser) -> ActionResult:
    """Click the Place Bet button in Marathonbet"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                // Look for place bet button
                const placeBetButton = document.querySelector('button.betslip-controls__placebet') ||
                                     document.querySelector('button:contains("Place Bet")') ||
                                     document.querySelector('[class*="placebet"]');
                
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
                const remainingBets = document.querySelectorAll('.betslip-content__choice');
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
    
    return ActionResult(extracted_content=f"Marathonbet Place bet result: {result}")

# ==================== MAIN AUTOMATION FUNCTIONS ====================

async def marathonbet_balance_checker(executable_path, user_data_dir, email, password):
    """Check Marathonbet balance"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"marathonbet_balance_{timestamp}.json")
    
    print(f"🚀 Starting Marathonbet balance check...")
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
            task=f"""You are a Marathonbet balance checker. Follow these exact steps:

STEP 1: Navigate to Marathonbet
- Navigate to https://marathonbet.com
- Wait 3 seconds for page to load

STEP 2: Check login status
Look for these indicators:
- IF YOU SEE: Balance display with any currency symbol such as "₦" (Nigerian Naira) symbol in top-right
  → User is LOGGED IN, proceed to STEP 4
- IF YOU SEE: "Log In" and "Join Now" buttons in top-right
  → User is LOGGED OUT, proceed to STEP 3

STEP 3: Login process (only if logged out)
- Use the login_with_marathonbet_credentials controller action
- Pass email="{email}" and password="{password}" as parameters
- This will:
  * Click "Log In" button to open modal
  * Select "Other login" tab for email login
  * Fill email and password
  * Submit the form

- ask for human input using the controller action 'Ask human for help with issues' if it encounters captcha or other issues
- Wait 5 seconds for login to process

- Verify login by checking for balance display
-

STEP 4: Get balance (only if logged in)
- Visually check for the balance in the top right to retrieve current balance
- Report the balance amount with  currency

Expected output format:
- is_logged_in: true/false
- balance: actual amount with currency (e.g., "0.00")
- currency : "USD"
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
            print("✅ Marathonbet balance check completed!")
        else:
            print("❌ Marathonbet balance check failed")
        
        # Save results
        combined_results = {
            "timestamp": timestamp,
            "platform": "Marathonbet",
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

async def marathonbet_bet_placer(input_data: dict, executable_path: str, user_data_dir: str):
    """Place bet on Marathonbet"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"marathonbet_bet_{timestamp}.json")
    
    print(f"🚀 Starting Marathonbet bet placement...")
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
            task=f"""You will place a bet on Marathonbet based on this input data: {input_data}

KEY CONVERSIONS FOR MARATHONBET:
- DNB1 (Draw No Bet Team 1) → "To Win Match or Match winner" for Team 1
- DNB2 (Draw No Bet Team 2) → "To Win Match or Match winner" for Team 2
- "To Win Match" or Match winner is Marathonbet's equivalent of DNB

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
            task=f"""Verify the Marathonbet betslip status after bet placement.

Your task:
1. Use the count_marathonbet_betslip_games controller action
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
            task=f"""You are the final bet placer for Marathonbet. Your stake amount is {stake_amount}.

STEPS:
1. Visually check the betslip has exactly 1 game
2. If betslip is not empty, use 'Fill Marathonbet stake amount' with stake={stake_amount}
3. Wait 2 seconds for the potential returns to calculate
4. Use 'Click Marathonbet place bet button' to place the bet
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
            "platform": "Marathonbet",
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
    
    email = "@gmail.com"     # Replace with actual email
    password = ""           # Replace with actual password
    
    balance = await marathonbet_balance_checker(executable_path, user_data_dir, email, password)
    if balance:
        print(f"✅ Balance check result: {balance.model_dump()}")
    else:
        print("❌ Balance check failed")

# Example usage for bet placement
async def main_bet_placement():
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    # Sample betting input for Marathonbet (from your arbitrage data)
    sample_input = {
    "profit": "0.61%",
    "sport": "Ice Hockey",
    "event_time": "Jun 22, 10:20",
    "bookmaker": "Marathonbet",
    "team1_bk": "Traktor 3x3",
    "team2_bk": "Ak Bars 3x3",
    "league_bk": "Ice Hockey. 3x3. KHL",
    "bet_type_bk": "DNB1",  # Will bet on Team 1 (Traktor 3x3)
    "odd_bk": "6.1",
    "link_bk": "https://marathonbet.com/en/betting/Ice-Hockey/Traktor-3x3+vs+Ak-Bars-3x3+-+23297419",
    "stake_amount": 100
}
    
    result = await marathonbet_bet_placer(sample_input, executable_path, user_data_dir)
    if result:
        print(f"✅ Bet placement result: {result['workflow_summary']}")
    else:
        print("❌ Bet placement failed")

if __name__ == "__main__":
    # Choose which function to run
    #asyncio.run(main_balance_check())      # For balance checking
    asyncio.run(main_bet_placement())      # For bet placement
    print("Marathonbet automation system ready!")
    print("Update the email/password and run the desired function.")