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
    balance: float = Field(description="User's account balance")
    error_message: str = Field(default="", description="Any error message encountered during balance check")
class placer(BaseModel):
    is_place_bet: bool = Field(default=False, description="Whether the bet has been placed successfully")
    error_message: str = Field(default="", description="Any error message encountered during bet placement")

# Create controllers with different output models
controller = Controller(output_model=BetPlacementResult)
controller3 = Controller(output_model=SiteAnalysis)
controller4 = Controller(output_model=Balance)
controller5 = Controller(output_model=placer)


# Add these controller action functions for Agent 4



@controller4.action('Ask human for help with issues')
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)


@controller.action('Ask human for help with issues')
def ask_human(question: str) -> ActionResult:
    answer = input(f'{question} > ')
    return ActionResult(extracted_content=f'The human responded with: {answer}', include_in_memory=True)

@controller5.action('Fill stake amount')
async def fill_stake_amount(browser, stake: float = 10) -> ActionResult:
    """Just fill the stake amount without placing bet"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (stakeAmount) => {
            const stakeInput = document.querySelector('input[placeholder="min. 10"]');
            
            if (!stakeInput) {
                return 'Stake input not found';
            }
            
            stakeInput.value = stakeAmount.toString();
            stakeInput.dispatchEvent(new Event('input', { bubbles: true }));
            stakeInput.dispatchEvent(new Event('change', { bubbles: true }));
            
            return `Stake set to ${stakeAmount}`;
        }
    """, stake)
    
    return ActionResult(extracted_content=result)

@controller5.action('Accept changes if needed')
async def accept_changes(browser) -> ActionResult:
    """Click Accept Changes button if it's active"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            const acceptButton = document.querySelector('button:has(span[data-cms-key="accept_changes"])');
            
            if (!acceptButton) {
                return 'Accept Changes button not found';
            }
            
            if (acceptButton.disabled) {
                return 'Accept Changes button is disabled - no changes to accept';
            }
            
            acceptButton.click();
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            return 'Changes accepted';
        }
    """)
    
    return ActionResult(extracted_content=result)

@controller5.action('Click place bet button')
async def click_place_bet(browser) -> ActionResult:
    """Click the Place Bet button"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            const placeBetButton = document.querySelector('button:has(span[data-cms-key="place_bet"])');
            
            if (!placeBetButton) {
                return 'Place Bet button not found';
            }
            
            if (placeBetButton.disabled || placeBetButton.classList.contains('is-disabled')) {
                return 'Place Bet button is disabled - cannot place bet';
            }
            
            placeBetButton.click();
            return 'Bet placement initiated';
        }
    """)
    
    return ActionResult(extracted_content=result)

@controller4.action('Show balance if hidden')
async def show_balance(browser) -> ActionResult:
    """Toggle balance visibility using the toggle button"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async () => {
            try {
                const toggleButton = document.querySelector('#j_toggleBalance');
                
                if (!toggleButton) {
                    return {
                        success: false,
                        error: 'Toggle button not found - user might not be logged in'
                    };
                }
                
                // Check if balance is currently hidden (toggle has "on" class when visible)
                const isCurrentlyVisible = toggleButton.classList.contains('on');
                
                // Click the toggle button
                toggleButton.click();
                
                // Wait for the toggle animation
                await new Promise(resolve => setTimeout(resolve, 500));
                
                return {
                    success: true,
                    action: isCurrentlyVisible ? 'toggled_to_hide' : 'toggled_to_show',
                    previous_state: isCurrentlyVisible ? 'visible' : 'hidden',
                    current_state: isCurrentlyVisible ? 'hidden' : 'visible'
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }
    """)
    
    return ActionResult(extracted_content=f"Toggle result: {result}")

@controller4.action('Login with credentials')
async def login_with_credentials(browser, phone: str = "9049914379", password: str = "$Theo3474") -> ActionResult:
    """Login to SportyBet with provided credentials"""
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        async (phone, password) => {
            try {
                // Check if login form exists
                const phoneInput = document.querySelector('input[name="phone"]');
                const passwordInput = document.querySelector('input[name="psd"]');
                const loginButton = document.querySelector('button[name="logIn"]');
                
                if (!phoneInput || !passwordInput || !loginButton) {
                    // Check if already logged in
                    const balanceElement = document.querySelector('#j_balance.m-balance');
                    if (balanceElement && balanceElement.textContent.includes('NGN')) {
                        return {
                            success: true,
                            status: 'already_logged_in',
                            balance: balanceElement.textContent.trim()
                        };
                    }
                    
                    return {
                        success: false,
                        error: 'Login form not found'
                    };
                }
                
                // Clear and fill phone number
                phoneInput.value = '';
                phoneInput.focus();
                phoneInput.value = phone;
                phoneInput.dispatchEvent(new Event('input', { bubbles: true }));
                phoneInput.dispatchEvent(new Event('change', { bubbles: true }));
                phoneInput.blur();
                
                // Small delay between fields
                await new Promise(resolve => setTimeout(resolve, 300));
                
                // Clear and fill password
                passwordInput.value = '';
                passwordInput.focus();
                passwordInput.value = password;
                passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                passwordInput.blur();
                
                // Wait for button to enable
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Check button state and click
                if (loginButton.classList.contains('disabled')) {
                    // Try to enable it
                    loginButton.classList.remove('disabled');
                    loginButton.disabled = false;
                }
                
                // Click login
                loginButton.click();
                
                // Wait for login to process
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                // Check if login was successful by looking for balance
                const balanceAfterLogin = document.querySelector('#j_balance.m-balance');
                const balanceText = balanceAfterLogin ? balanceAfterLogin.textContent.trim() : '';
                
                if (balanceText.includes('NGN')) {
                    return {
                        success: true,
                        status: 'login_successful',
                        balance: balanceText
                    };
                } else {
                    // Check if still on login form
                    const stillHasLoginForm = document.querySelector('input[name="phone"]');
                    if (stillHasLoginForm) {
                        return {
                            success: false,
                            status: 'login_failed',
                            error: 'Still showing login form after attempt'
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
    """, phone, password)
    
    return ActionResult(extracted_content=f"Login result: {result}")

# Add betslip counter function to controller3
@controller3.action('Check how many games are in the betslip')
async def count_betslip_games(browser) -> ActionResult:
    """Count number of games in betslip"""
    
    page = await browser.get_current_page()
    
    result = await page.evaluate("""
        () => {
            const betItems = document.querySelectorAll('.m-betslips .m-item');
            return `${betItems.length} games in betslip`;
        }
    """)
    
    return ActionResult(extracted_content=result)

    
async def balance_checker(executable_path, user_data_dir, email, password):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"latest.json")
    
    print(f"🚀 Starting browser automation test...")
    print(f"💾 Conversation will be saved to: {temp_path}")
    
    # Sample betting input for testing
    sample_input = {
        "profit": "0.8%",       
        "sport": "Basketball",        
        "event_time": "Jun 21, 13:50",       
        "bookmaker": "SportyBet",      
        "team1_bk": "BC Zalgiris Kaunas",        
        "team2_bk": "BC Rytas Vilnius",        
        "league_bk": "Basketball. Lithuania. LKL",       
        "bet_type_bk": "DNB2",      
        "odd_bk": "3.6",         
        "link_bk": "https://sportybet.com/ng/sport/basketball/Lithuania/LKL/BC_Zalgiris_Kaunas_vs_BC_Rytas_Vilnius/sr:match:61339551"     
    }
    
    try:
        # ✅ Configure BrowserSession with your Windows Chrome
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state=None,
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
        
        #agent4: Balance Checker
        agent4 = Agent(
            task=f"""You are a SportyBet balance checker. Follow these exact steps:

STEP 1: Navigate to SportyBet
- Navigate to https://sportybet.com
- Wait 2 seconds for page to load
-click on sports
-wait 4 seconds for page to load

STEP 2: Visually check login status
Look at the top-right section of the page:
- IF YOU SEE: A balance amount (like "NGN" followed by numbers), "Deposit" button, and "My Account" dropdown
  → User is LOGGED IN, proceed to STEP 4
- IF YOU SEE: Input fields for "Mobile Number" and "Password" with a "Login" button
  → User is LOGGED OUT, proceed to STEP 3
- Take a screenshot and describe what you see to confirm

STEP 3: Login process (only if logged out)
- Look for the login form in the top-right area
- Use the login_with_credentials controller action
- Pass phone="{email}" and password="{password}" as parameters
- Wait 5 seconds for login to complete
- Check visually again - you should now see a balance amount instead of login form
- If still seeing login form, report login failure

STEP 4: Get balance (only if logged in)
- Look for the balance display (it shows as "NGN" followed by numbers)
- If you can see the balance amount, extract it
- If balance appears hidden or shows as empty:
  - Use the show_balance controller action to toggle visibility
 -
- Report the final balance amount
-Report the final balance currency

IMPORTANT: 
- Always describe what you see on the page before making decisions
- sometimes a modal might pop up before or after login , observe and close it. 
- The login state is determined by what's visible, not controller checks
- Stop after successfully getting balance or after login failure

Expected output format:
- is_logged_in: true/false
- balance: actual amount (e.g., " 3,029.51")
- Currency: Currency (e.g NGN)
- error_message: any issues encountered""",
            llm=ChatOpenAI(model="gpt-4o"),
            browser_session=browser_session,
           
            controller=controller4,  # This controller has the balance checking functions
        )
        history4 = await agent4.run()
        result4 = history4.final_result()
        balance = None
        
        if result4:
            balance = Balance.model_validate_json(result4)
            print("✅ Sportbet balance check completed!")
        else:
            print("❌ sportybet balance check failed")
        
        # Save results
        combined_results = {
            "timestamp": timestamp,
            "platform": "sportybet",
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
    
async def bet_placer(input_data: dict, executable_path, user_data_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_dir = Path("conversations")
    conv_dir.mkdir(exist_ok=True)
    temp_path = str(conv_dir / f"latest.json")
    
    print(f"🚀 Starting browser automation test...")
    print(f"💾 Conversation will be saved to: {temp_path}")
    
    # Sample betting input for testing
    sample_input = {
        "profit": "0.8%",       
        "sport": "Basketball",        
        "event_time": "Jun 21, 13:50",       
        "bookmaker": "SportyBet",      
        "team1_bk": "BC Zalgiris Kaunas",        
        "team2_bk": "BC Rytas Vilnius",        
        "league_bk": "Basketball. Lithuania. LKL",       
        "bet_type_bk": "DNB2",      
        "odd_bk": "3.6",         
        "link_bk": "https://sportybet.com/ng/sport/basketball/Lithuania/LKL/BC_Zalgiris_Kaunas_vs_BC_Rytas_Vilnius/sr:match:61339551"     
    }
    
    try:
        # ✅ Configure BrowserSession with your Windows Chrome
        browser_session = BrowserSession(
            executable_path=executable_path,
            user_data_dir=user_data_dir,
            headless=False,
            keep_alive=True,
            storage_state='/tmp/cookies.json',
        )
        
        await browser_session.start()
        print("✅ Browser session created successfully")
            #agent4: Balance Checker
        

        
        # ✅ Agent 2: Bet Placement
        print("\n🤖 Running Agent 2: Bet placement...")
        agent2 = Agent(
            task=f"""You will place a bet on Sportybet based on this input data: {input_data}
           
        
          
KEY CONVERSIONS:
- DNB1 (Draw No Bet Team 1) → "Home" selection
- DNB2 (Draw No Bet Team 2) → "Away" selection 

WORKFLOW: 
1. Go to the provided link in link_bk:
1. Go to the provided link: {input_data.get('link_bk')} this will be the only approach you take to find the event 
do not search for the event by name or league
2. Wait for page to load (3 seconds)
3. Based on bet_type_bk: {input_data.get('bet_type_bk', '')}, click the appropriate odds button: 
 ,- If DNB1 → click odds for "Home" (Team 1: {input_data.get('team1_bk', '')})
- If DNB2 → click odds for "Away" (Team 2: {input_data.get('team2_bk', '')})
4. Verify the bet was added to basket (betslip) on the right side
5. Stop after successful selection


Your output format should include:
- The input data you processed
- Any errors encountered if any""",
            llm=ChatOpenAI(model="gpt-4o"),
            browser_session=browser_session,
            controller=controller
        )
        
        history2 = await agent2.run()
        result2 = history2.final_result()
        bet_result = None
        
        if result2:
            # ✅ Parse BetPlacementResult output
            bet_result = BetPlacementResult.model_validate_json(result2)
    
            print("✅ Agent 2 completed successfully!")
           
            if bet_result.error_message:
                print(f"❌ Error: {bet_result.error_message}")
        else:
            print("❌ Agent 2 failed")
            return

        # ✅ Agent 3: Betslip Verification
        print("\n🤖 Running Agent 3: Betslip verification...")
        agent3 = Agent(
            task=f"""Based on the previous agent's results:
            
Previous Agent Results:
- Input Data: {bet_result.input_data}



Your task is to:
1. Analyze the current page you're on
2. use the controller to check how many games are in the betslip
3. count how many games are currently in the betslip
4. Verify if it is one, if it is empty or more tham one return an error


Describe what you see on the current page and confirm the betslip status.""",
            llm=ChatOpenAI(model="gpt-4o"),
            browser_session=browser_session,
            controller=controller3,  # This controller has the betslip counter function
        )
        
        history3 = await agent3.run()
        result3 = history3.final_result()
        site_analysis = None
        
        if result3:
            # ✅ Parse SiteAnalysis output
            site_analysis = SiteAnalysis.model_validate_json(result3)
    
            print("✅ Agent 3 completed successfully!")
            print(f"📊 {site_analysis.title} - {site_analysis.description}")
            print(f"🎰 Betting site: {site_analysis.is_betting_site}")
            print(f"📋 Sections: {', '.join(site_analysis.main_sections)}")
        else:
            print("❌ Agent 3 failed")


        agent5 = Agent(
            task=f"""You are the bet placer for sportybet , your task is to place bet based on the stame amount you were given
            
            the stake amount is 100 . 
            step 1 : Visulally check if the betslip is empty or not
            step 2 : If it is not empty fill the stake amount using the controller action 'Fill stake amount' with stake=100
            step 3 : If the stake amount is filled click the 'Place Bet' button using the controller action 'Click place bet button' or accept changes if needed using the controller action 'Accept changes if needed'
            step 4 : If the bet is placed successfully return a success message, otherwise return an error message""",
            llm=ChatOpenAI(model="gpt-4o"),
            browser_session=browser_session,
            controller=controller5,  # This controller has the betslip counter function
        )
        
        history5 = await agent5.run()
        result5 = history5.final_result()
        placer_result = None
        
        if result5:
            # ✅ Parse SiteAnalysis output
            placer_result = placer.model_validate_json(result5)
    
           
        else:
            print("❌ Agent 5 failed")
            

                
        
        # ✅ Wait for file system to sync
        print("\n⏳ Waiting for conversation file to be written...")
        await asyncio.sleep(3)
        
        # ✅ Save combined results
        try:
            combined_results = {
                "bet_placement_result": bet_result.model_dump() if bet_result else None,
                "betslip_verification_result": site_analysis.model_dump() if site_analysis else None,
                "workflow_summary": {
                    "input_processed": sample_input,
                    
                    "verification_completed": site_analysis is not None,
                    "place_bet_completed": placer_result.is_place_bet if placer_result else False,
                }
            }

            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(combined_results, f, indent=2, ensure_ascii=False)
            print(f"✅ Structured results saved to: {temp_path}")
            print(f"📁 File size: {os.path.getsize(temp_path)} bytes")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
        
    except Exception as browser_error:
        print(f"❌ Browser session error: {browser_error}")
        print("💡 Possible issues:")
        print("   - Chrome path incorrect")
        print("   - Profile directory locked by another Chrome instance")
        print("   - Insufficient permissions")
        return
    
    finally:
        # ✅ Cleanup (always runs)
        try:
            await browser_session.close()
            print("🧹 Browser session closed successfully")
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup warning: {cleanup_error}")




        
if __name__ == "__main__":
    
    executable_path='C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' 
    user_data_dir='C:\\Users\\HP PC\\AppData\\Local\\Google\\Chrome\\User Data\\Default'
    
    username = ""     # Your 888sport username
    password = "$"            # Your 888sport password
    asyncio.run(balance_checker(executable_path, user_data_dir, username, password))