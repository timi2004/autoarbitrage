from playwright.sync_api import sync_playwright
import json
import time
import logging
import traceback
import os
from datetime import datetime
import sys
import os

# Add the agent directory to the path to import config_manager

from config_manager import ConfigManager


# Bookmaker ID assignments from breaking-bet.com
# Format: bookmaker_name = id_number

# A
#bet188 = 83          # 188bet
#xbet_1 = 21          # 1XBet  
#win_1 = 79           # 1win
#sport_888 = 82       # 888sport

# B
#baltbet = 53         # BaltBet
#bet365 = 39          # Bet365
#bet9ja = 33          # Bet9ja
#betking = 49         # BetKing
#betwgb = 36          # BetWGB
#betano = 85          # Betano
#betboom = 77         # Betboom
#betcity = 6          # Betcity
#betcity_live = 84    # Betcity (Live)
#betclic = 22         # Betclic
#betfair_ex = 31      # BetfairEx
#betfair_sb = 10      # BetfairSB
#betsafe = 23         # Betsafe
#betway = 48          # Betway
#bwin = 3             # Bwin
#betpawa = 44         # betPawa

# C
#cashpoint = 74       # Cashpoint
#codere = 62          # Codere

# D
#dafabet = 56         # Dafabet

# E
#everygame = 16       # Everygame

# F
#favbet = 14          # Favbet
#fonbet = 25          # Fonbet

# G
#ggbet = 57           # GGbet

# I
#interwetten = 15     # Interwetten

# K
#konfambet = 87       # Konfambet

# L
#ladbrokes = 41       # Ladbrokes
#leon = 8             # Leon
#ligastavok = 55      # LigaStavok
#lottomatica = 68     # Lottomatica

# M
#msport = 80          # MSport
#marathonbet = 5      # Marathonbet
#matchbook = 40       # Matchbook
#melbet = 76          # Melbet
#mostbet = 52         # Mostbet

# N
#nairabet = 38        # NairaBet

# O
#olimp = 54           # Olimp

# P
#pinnacle = 7         # Pinnacle
#pinnacle_esports = 73 # Pinnacle E-sports

# S
#sbobet = 9           # Sbobet
#sisal = 67           # Sisal
#smarkets = 30        # Smarkets
#snai = 65            # Snai
#sportybet = 43       # SportyBet

# T
#tempobet = 71        # Tempobet
#tennisi = 51         # Tennisi

# U
#unibet = 18          # Unibet

# V
#vbet = 19            # Vbet

# W
#winline = 28         # Winline

# Z
#zenit = 4            # Zenit
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_arbitrage_opportunities():
    logger.info("Starting Playwright for arbitrage scraping")
    
    with sync_playwright() as p:
        browser_type = p.chromium
        
        # Launch browser
        browser = browser_type.launch(
            headless=False,
            slow_mo=100,
        )
        
        # Create context
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        
        # Create page
        page = context.new_page()
        
        try:
            # Set timeout
            page.set_default_timeout(60000)
            
            # Navigate to the website
            logger.info("Navigating to breaking-bet.com...")
            page.goto('https://breaking-bet.com/en/arbs/prematch', wait_until='domcontentloaded')
            logger.info("Page DOM content loaded")
            
            # Take screenshot and wait
            page.screenshot(path="initial_load.png")
            logger.info("✅ Page initially loaded, screenshot saved")
            
            # Wait for page to stabilize
            logger.info("Waiting for page to stabilize...")
            time.sleep(15)
            page.screenshot(path="after_wait.png")
            
            # Handle cookie consent if present
            try:
                cookie_button = page.query_selector('button:has-text("Accept"), button:has-text("Cookie"), .cookie-button')
                if cookie_button:
                    logger.info("Accepting cookies...")
                    cookie_button.click()
                    time.sleep(2)
            except Exception as e:
                logger.info(f"No cookie banner found or error: {e}")
            
            # Scroll down
            logger.info("Scrolling down to view content...")
            page.mouse.wheel(0, 300)
            time.sleep(2)
            page.screenshot(path="after_scroll.png")
            
            # Click filter icon
            logger.info("Looking for filter icon...")
            filter_icon = page.query_selector('th.setting span.hand.glyphicon.glyphicon-cog')
            if filter_icon:
                logger.info("✅ Found filter icon with direct selector")
                filter_icon.click()
                time.sleep(2)
                page.screenshot(path="filter_clicked.png")
            else:
                logger.warning("⚠️ Filter icon not found, trying JavaScript...")
                clicked = page.evaluate("""
                    () => {
                        const filterIcon = document.querySelector('th.setting span.hand.glyphicon.glyphicon-cog');
                        if (filterIcon) {
                            filterIcon.click();
                            return true;
                        }
                        return false;
                    }
                """)
                if clicked:
                    logger.info("✅ Filter clicked via JavaScript")
                    time.sleep(2)
                else:
                    logger.error("❌ Could not find filter icon")
                    return []
            
            # Wait for modal
            logger.info("Waiting for filter modal...")
            try:
                modal = page.wait_for_selector('#main_filter', state='visible', timeout=5000)
                logger.info("✅ Filter modal is visible")
                page.screenshot(path="modal_open.png")
            except Exception as e:
                logger.error(f"❌ Filter modal not found: {e}")
                return []
            
            # Uncheck Handicaps, Ind. totals, and Additional markets
            logger.info("Unchecking specific markets (Handicaps, Ind. totals, totals, Additional)...")
            markets_result = page.evaluate("""
                () => {
                    try {
                        // Markets to uncheck: Handicaps (2), Ind. totals (4), totals (3) Additional (6)
                        const marketsToUncheck = ["2", "4", "6", "3"];
                        
                        for (const value of marketsToUncheck) {
                            const checkbox = document.querySelector(`div.checkbox input[type="checkbox"][value="${value}"]`);
                            if (checkbox && checkbox.checked) {
                                // Click the label to uncheck
                                checkbox.closest('label').click();
                                console.log(`Unchecked market with value ${value}`);
                            }
                        }
                        
                        // Return status of all markets for verification
                        const marketStatus = {};
                        document.querySelectorAll('div.checkbox input[type="checkbox"]').forEach(cb => {
                            const label = cb.closest('label').textContent.trim();
                            marketStatus[label] = cb.checked;
                        });
                        
                        return { 
                            success: true, 
                            message: "Specific markets unchecked",
                            marketStatus 
                        };
                    } catch (e) {
                        return { success: false, error: e.toString() };
                    }
                }
            """)
            logger.info(f"Market filter result: {json.dumps(markets_result, indent=2)}")
            page.screenshot(path="after_market_selection.png")
            
            # Deselect specific sports (Football, e-Sports, Futsal)
            logger.info("Deselecting Football, e-Sports, and Futsal from sports filter...")
            sports_result = page.evaluate("""
                () => {
                    try {
                        // Sports to deselect: Football (1), e-Sports (10), Futsal (14)
                        const sportsToDeselect = ["1", "10", "14"];
                        const results = [];
                        
                        for (const sportValue of sportsToDeselect) {
                            const checkbox = document.querySelector(`div.checkboxes.bookmakers_checkboxes input[type="checkbox"][value="${sportValue}"]`);
                            
                            if (!checkbox) {
                                results.push({ sport: sportValue, success: false, error: "Checkbox not found" });
                                continue;
                            }
                            
                            // Get sport name from label text
                            const label = checkbox.closest('label');
                            const sportName = label ? label.textContent.trim() : `Sport-${sportValue}`;
                            
                            // Check if sport is currently selected (checked)
                            if (checkbox.checked) {
                                // Click the label to uncheck it
                                if (label) {
                                    label.click();
                                    
                                    // Verify it was unchecked
                                    results.push({
                                        sport: sportName,
                                        value: sportValue,
                                        success: true,
                                        message: "Successfully unchecked",
                                        wasChecked: true,
                                        nowChecked: checkbox.checked,
                                        labelHasSelected: label.classList.contains('selected')
                                    });
                                } else {
                                    results.push({ sport: sportName, value: sportValue, success: false, error: "Label not found" });
                                }
                            } else {
                                results.push({
                                    sport: sportName,
                                    value: sportValue,
                                    success: true,
                                    message: "Was already unchecked",
                                    wasChecked: false,
                                    nowChecked: false
                                });
                            }
                        }
                        
                        return {
                            success: true,
                            message: "Sports deselection completed",
                            results: results
                        };
                    } catch (e) {
                        return { success: false, error: e.toString() };
                    }
                }
            """)
            logger.info(f"Sports deselection result: {json.dumps(sports_result, indent=2)}")
            page.screenshot(path="after_sports_deselection.png")
            time.sleep(2)
            
            # Set time filter to 1 day
            logger.info("Setting time filter to 1 day...")
            time_filter_result = page.evaluate("""
                () => {
                    try {
                        // Find the time filter dropdown
                        const timeFilter = document.querySelector('select[name="filter[settings][age]"]');
                        if (!timeFilter) return { success: false, error: "Time filter dropdown not found" };
                        
                        // Set the value to "1d" (1 day)
                        timeFilter.value = "1d";
                        
                        // Trigger change event to update the UI
                        const event = new Event('change', { bubbles: true });
                        timeFilter.dispatchEvent(event);
                        
                        return { 
                            success: true, 
                            message: "Time filter set to 1 day", 
                            selectedValue: timeFilter.value 
                        };
                    } catch (e) {
                        return { success: false, error: e.toString() };
                    }
                }
            """)
            logger.info(f"Time filter result: {json.dumps(time_filter_result, indent=2)}")
            
            # Click "Select all" TWICE to turn everything off
            logger.info("Clicking 'Select all' TWICE to ensure all bookmakers are disabled...")
            
            # First click on Select all
            select_all = page.query_selector('span.hand.select_all')
            if select_all:
                logger.info("First click on 'Select all'...")
                select_all.click()
                time.sleep(2)
                
                # Second click on Select all
                logger.info("Second click on 'Select all'...")
                select_all.click()
                time.sleep(2)
                
                logger.info("✅ Clicked 'Select all' twice")
                page.screenshot(path="after_select_all_clicks.png")
            else:
                logger.error("❌ 'Select all' element not found")
                # Try JavaScript as fallback
                page.evaluate("""
                    () => {
                        const selectAll = document.querySelector('span.hand.select_all');
                        if (selectAll) {
                            // First click
                            selectAll.click();
                            // Wait a bit
                            setTimeout(() => {
                                // Second click
                                selectAll.click();
                            }, 1000);
                            return true;
                        }
                        return false;
                    }
                """)
                logger.info("Attempted JavaScript clicks on 'Select all'")
                time.sleep(3)  # Wait for JavaScript timeout to complete
            
            # Now select our target bookmakers
            config = ConfigManager()
            target_bookmakers = config.get_target_bookmakers_for_scraper()
            target_bookmakers = [str(bm_id) for bm_id in target_bookmakers]
            
            if not target_bookmakers:
                
                logger.warning("⚠️ No bookmakers are enabled in config! Using default bookmakers.")
                target_bookmakers = ["33", "49"]
                logger.info(f"🔄 Using fallback bookmakers: {target_bookmakers}")
            else:
                logger.info(f"✅ Using configured bookmakers: {target_bookmakers}")  
            #target_bookmakers = ["43", "38", "33", "82", "49", "79", "5", "4", "19"]
            
            logger.info(f"Selecting bookmakers with values: {target_bookmakers}")
            
            selection_result = page.evaluate("""
                                             
                (targetValues) => {
                    const result = {
                        success: [],
                        failed: []
                    };
                    
                    // Function to find checkbox by value
                    function findCheckbox(value) {
                        return document.querySelector(`.bookmakers_checkboxes input[type="checkbox"][value="${value}"]`);
                    }
                    
                    // Process each target value
                    for (const value of targetValues) {
                        const checkbox = findCheckbox(value);
                        
                        if (checkbox && checkbox.parentElement) {
                            try {
                                // Scroll the parent container to make sure checkbox is visible
                                const container = document.querySelector('.bookmakers_checkboxes');
                                const label = checkbox.closest('label');
                                
                                if (container && label) {
                                    // Get position
                                    const rect = label.getBoundingClientRect();
                                    const containerRect = container.getBoundingClientRect();
                                    
                                    // Scroll into view if needed
                                    if (rect.top < containerRect.top || rect.bottom > containerRect.bottom) {
                                        label.scrollIntoView({ behavior: 'auto', block: 'nearest' });
                                    }
                                    
                                    // Click on the label to trigger the checkbox
                                    label.click();
                                    
                                    // Verify if clicked (checkbox checked and label has "selected" class)
                                    if (checkbox.checked && label.classList.contains('selected')) {
                                        result.success.push(value);
                                    } else {
                                        result.failed.push({value, reason: "Click didn't set proper state"});
                                    }
                                } else {
                                    result.failed.push({value, reason: "Container or label not found"});
                                }
                            } catch (e) {
                                result.failed.push({value, reason: e.toString()});
                            }
                        } else {
                            result.failed.push({value, reason: "Checkbox not found"});
                        }
                    }
                    
                    return result;
                }
            """, target_bookmakers)
            
            logger.info(f"Selection results: {json.dumps(selection_result, indent=2)}")
            page.screenshot(path="after_selection.png")
            
            # Toggle off "3 outcomes" option
            logger.info("Toggling off '3 outcomes' option...")
            
            # Try a direct click on the label for 3 outcomes
            clicked = page.evaluate("""
                () => {
                    try {
                        // Find the label containing "3 outcomes" text
                        const labels = Array.from(document.querySelectorAll('.checkbox label'));
                        const threeOutcomesLabel = labels.find(label => 
                            label.textContent.trim() === '3 outcomes');
                            
                        if (threeOutcomesLabel) {
                            // Click the label directly (this should toggle the checkbox)
                            threeOutcomesLabel.click();
                            console.log("Clicked on 3 outcomes label");
                            
                            // Verify if it worked
                            const checkbox = threeOutcomesLabel.querySelector('input');
                            return {
                                success: true,
                                clicked: true,
                                checkboxChecked: checkbox ? checkbox.checked : null,
                                labelSelected: threeOutcomesLabel.classList.contains('selected')
                            };
                        }
                        return { success: false, error: "3 outcomes label not found" };
                    } catch (e) {
                        return { success: false, error: e.toString() };
                    }
                }
            """)
            logger.info(f"Direct click on 3 outcomes label result: {json.dumps(clicked, indent=2)}")
            
            # Add a longer delay to allow the UI to update
            logger.info("Waiting 5 seconds for UI to update after toggling 3 outcomes...")
            time.sleep(5)
            page.screenshot(path="after_toggle_3outcomes.png")
            
            # Add a 10-second wait period before closing modal for verification
            logger.info("Waiting 10 seconds for verification before closing the modal...")
            time.sleep(10)
            page.screenshot(path="before_closing_modal.png")
            
            # Close the modal
            logger.info("Closing the modal...")
            try:
                close_button = page.query_selector('button.close[data-dismiss="modal"]')
                if close_button:
                    close_button.click()
                    logger.info("✅ Clicked close button")
                else:
                    logger.error("❌ Close button not found")
                    # Try JavaScript close as fallback
                    page.evaluate("""
                        () => {
                            const closeBtn = document.querySelector('button.close[data-dismiss="modal"]');
                            if (closeBtn) closeBtn.click();
                        }
                    """)
                    logger.info("Attempted JavaScript close")
            except Exception as e:
                logger.error(f"Error closing modal: {e}")
                # Try another JavaScript approach
                page.evaluate("""
                    () => {
                        // Try multiple approaches to close the modal
                        const closeBtn = document.querySelector('button.close[data-dismiss="modal"]');
                        if (closeBtn) {
                            closeBtn.click();
                            return;
                        }
                        
                        // Try finding the modal and hiding it directly
                        const modal = document.getElementById('main_filter');
                        if (modal) {
                            modal.classList.remove('in');
                            modal.style.display = 'none';
                            
                            // Remove modal backdrop if present
                            const backdrop = document.querySelector('.modal-backdrop');
                            if (backdrop) backdrop.remove();
                        }
                    }
                """)
                logger.info("Attempted alternative JavaScript modal close")
            
            # Wait for modal to close and filter to apply
            logger.info("Waiting for filter to apply (30 seconds)...")
            time.sleep(15)
            page.screenshot(path="after_filter.png")
            
            # Check if opportunities are present with improved detection
            logger.info("Checking for arbitrage opportunities with multiple selectors...")
            page.screenshot(path="before_detection.png")

            # Wait longer to ensure everything is loaded
            logger.info("Waiting longer for page to fully load and render (45 seconds)...")
            page.wait_for_timeout(15000)
            page.mouse.wheel(0, 300)
            time.sleep(15)
            page.mouse.wheel(0, -300)
            time.sleep(15)
            logger.info("Extended wait completed, page should be fully loaded")

            # Take a screenshot to verify the state before extraction
            page.screenshot(path="fully_loaded_before_extraction.png")
            logger.info("Taking screenshot of page before extraction")

            # Use a simpler, more robust approach to extract opportunities
            logger.info("Extracting opportunities with schema-compliant approach...")
            main_opportunities = page.evaluate("""
                () => {
                    // Helper function to safely extract text
                    function safeText(element) {
                        return element ? element.textContent.trim() : '';
                    }
                    
                    try {
                        const opportunities = [];
                        
                        // Add this diagnostic code to the evaluate function
                        const iframeContent = Array.from(document.querySelectorAll('iframe')).map(f => {
                            try {
                                return {
                                    src: f.src,
                                    hasContent: f.contentDocument ? true : false,
                                    accessDenied: f.contentDocument ? false : true
                                };
                            } catch(e) {
                                return { src: f.src, error: e.toString(), accessDenied: true };
                            }
                        });

                        // Get all element counts to see what's available
                        const counts = {
                            tables: document.querySelectorAll('table').length,
                            lootWrap: document.querySelectorAll('.loot_wrap').length,
                            profitCells: document.querySelectorAll('td.profit').length,
                            bookmakerCells: document.querySelectorAll('td.bookmaker_td').length,
                            oddRows: document.querySelectorAll('tr.odd_row').length,
                            iframes: iframeContent,
                            anyLoot: document.body.innerHTML.includes('loot_wrap'),
                            anyProfit: document.body.innerHTML.includes('td class="profit"'),
                            bodyLength: document.body.innerHTML.length
                        };

                        console.log("Element availability:", counts);
                        
                        // Look for profit cells as our anchor points
                        const profitCells = document.querySelectorAll('td.profit');
                        console.log(`Found ${profitCells.length} profit cells`);
                        
                        for (const profitCell of profitCells) {
                            try {
                                // Get the parent row
                                const row = profitCell.closest('tr');
                                if (!row) continue;
                                
                                // Extract the profit percentage
                                const percentElement = profitCell.querySelector('div.percent span');
                                const profit = safeText(percentElement).replace('%', '').trim();
                                
                                // Get sport
                                const sport = safeText(document.querySelector('.sport_filter_selected')) || 'Unknown';
                                
                                // Get event time
                                const timeElement = row.querySelector('td.time');
                                const eventTime = safeText(timeElement);
                                
                                // Get bet types
                                const betTypeElements = row.querySelectorAll('td.bet_type');
                                const betType1 = betTypeElements.length >= 1 ? safeText(betTypeElements[0]) : '';
                                const betType2 = betTypeElements.length >= 2 ? safeText(betTypeElements[1]) : '';
                                
                                // Get odds specific (1 period, etc)
                                const oddSpecificElement = row.querySelector('td.odds_types span.odds_groups');
                                const oddSpecific = oddSpecificElement ? safeText(oddSpecificElement) : '';
                                
                                // Get bookmakers
                                const bookmaker1Element = row.querySelector('td:nth-child(3)');
                                const bookmaker2Element = row.querySelector('td:nth-child(5)');
                                const bookmaker1 = safeText(bookmaker1Element);
                                const bookmaker2 = safeText(bookmaker2Element);
                                
                                // Get odds
                                const odd1Element = row.querySelector('td:nth-child(4)');
                                const odd2Element = row.querySelector('td:nth-child(6)');
                                const odd1 = safeText(odd1Element);
                                const odd2 = safeText(odd2Element);
                                
                                // Get matchup
                                const matchElement = row.querySelector('td.match');
                                const matchup = safeText(matchElement);
                                
                                // Get links
                                let link1 = '', link2 = '';
                                const links = row.querySelectorAll('a');
                                if (links.length >= 1) link1 = links[0].href;
                                if (links.length >= 2) link2 = links[1].href;
                                
                                // Create opportunity object with the standard schema
                                const opportunity = {
                                    profit: parseFloat(profit) || 0,
                                    sport,
                                    event_time: eventTime,
                                    matchup,
                                    bookmaker1,
                                    bookmaker2,
                                    odd_bk1: odd1,
                                    odd_bk2: odd2,
                                    bet_type_bk1: betType1,
                                    bet_type_bk2: betType2,
                                    link_bk1: link1,
                                    link_bk2: link2,
                                    odd_specific: oddSpecific,
                                    detailed_page: false
                                };
                                
                                // Validate the opportunity has the minimum required fields
                                if (opportunity.bookmaker1 && opportunity.bookmaker2 && 
                                    opportunity.odd_bk1 && opportunity.odd_bk2 && 
                                    parseFloat(opportunity.profit) > 0) {
                                    opportunities.push(opportunity);
                                } else {
                                    console.log("Skipping incomplete opportunity:", opportunity);
                                }
                            } catch (e) {
                                console.error("Error extracting row:", e);
                            }
                        }
                        
                        return opportunities;
                    } catch (e) {
                        console.error("Fatal extraction error:", e);
                        return [{fatal_error: e.toString()}];
                    }
                }
            """)

            # Log what we found
            logger.info(f"Extraction complete. Found {len(main_opportunities)} opportunities")
            if len(main_opportunities) > 0:
                logger.info("First opportunity sample:")
                logger.info(json.dumps(main_opportunities[0], indent=2))
            else:
                logger.error("No opportunities extracted despite being visible")
                # Take screenshot for debugging
                page.screenshot(path="empty_extraction.png")
            
            # Now look for "show all" links and extract detailed opportunities
            logger.info("Looking for 'show all' links...")
            show_all_links = page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('.lifetime_tr a.link_to_event').forEach(link => {
                        links.push({
                            url: link.getAttribute('href'),
                            text: link.textContent.trim(),
                            arbId: link.closest('.loot_wrap')?.id || 'unknown'
                        });
                    });
                    return links;
                }
            """)
            
            logger.info(f"Found {len(show_all_links)} 'show all' links")
            
            # Process each "show all" link
            detailed_opportunities = []
            for i, link_data in enumerate(show_all_links):
                try:
                    logger.info(f"Processing 'show all' link {i+1}/{len(show_all_links)}: {link_data['text']}")
                    
                    # Navigate to the detailed page
                    detailed_url = "https://breaking-bet.com" + link_data['url']
                    logger.info(f"Navigating to: {detailed_url}")
                    
                    # Navigate with a longer timeout
                    page.goto(detailed_url, timeout=60000)
                    
                    # Add a fixed delay to ensure the page has time to fully render
                    logger.info("Waiting 5 seconds for page to fully render...")
                    time.sleep(5)
                    
                    # Wait for the skeletons to disappear and real content to load
                    logger.info("Waiting for real content to load (non-skeleton elements)...")
                    try:
                        # First wait for any loot_wrap to appear
                        page.wait_for_selector('.loot_wrap', timeout=10000)
                        
                        # Then wait for non-skeleton elements to appear
                        page.wait_for_selector('.loot_wrap:not(.skeleton)', timeout=20000)
                        
                        # Also wait for bookmaker elements which should be in the real content
                        page.wait_for_selector('td.bookmaker_td', timeout=10000)
                    except Exception as wait_error:
                        logger.warning(f"Wait for real content timed out: {str(wait_error)}")
                        # Continue anyway but with longer delay
                        logger.info("Waiting additional 10 seconds instead...")
                        time.sleep(10)
                    
                    # Take a screenshot to verify the page loaded correctly
                    page.screenshot(path=f"detailed_page_{i}.png")
                    
                    # First check if there are any elements visible
                    visible_elements = page.evaluate("""
                        () => {
                            const items = document.querySelectorAll('.loot_wrap');
                            return items.length;
                        }
                    """)
                    
                    logger.info(f"Found {visible_elements} visible elements on detailed page")
                    
                    if visible_elements == 0:
                        # If no elements are found, wait longer and try again
                        logger.info("No elements found. Waiting additional 5 seconds...")
                        time.sleep(5)
                        page.screenshot(path=f"detailed_page_{i}_retry.png")
                    
                    # Wait for content to load with a longer timeout
                    try:
                        page.wait_for_selector('.loot_wrap', timeout=60000)
                    except Exception as wait_error:
                        logger.warning(f"Wait for selector timed out: {str(wait_error)}")
                        # Continue anyway, we might still be able to extract some data
                    
                    # Extract detailed opportunities from this page with improved selector and full schema
                    logger.info("Extracting detailed opportunities...")
                    detailed_page_opportunities = page.evaluate("""
                        () => {
                            try {
                                const opportunities = [];
                                
                                // Use selector that explicitly excludes skeleton elements
                                let arbItems = document.querySelectorAll('.loot_wrap:not(.skeleton)');
                                
                                if (arbItems.length === 0) {
                                    // Try different selector combinations
                                    arbItems = document.querySelectorAll('.table.forkstable:not(.skeleton)');
                                    console.log("Using alternative selector, found: " + arbItems.length);
                                    
                                    if (arbItems.length === 0) {
                                        // Last resort, just try any tables
                                        arbItems = document.querySelectorAll('table.forkstable');
                                        console.log("Using last resort selector, found: " + arbItems.length);
                                    }
                                }
                                
                                console.log(`Found ${arbItems.length} real detailed opportunities (non-skeleton)`);
                                
                                // Get URL for reference
                                const pageUrl = window.location.href;
                                
                                arbItems.forEach((item, index) => {
                                    try {
                                        // Extract profit percentage
                                        const profitElement = item.querySelector('td.profit div.percent span');
                                        const profit = profitElement ? profitElement.textContent.trim() : 'Unknown';
                                        
                                        // Extract sport
                                        const sportElement = item.querySelector('td.sport div.percent span');
                                        const sport = sportElement ? sportElement.textContent.trim() : 'Unknown';
                                        
                                        // Extract time
                                        const timeElement = item.querySelector('td.sport div.lifetime span');
                                        const eventTime = timeElement ? timeElement.textContent.trim() : 'Unknown';
                                        
                                        // Extract odd specific using the correct selector
                                        // FIXED: Getting odd_specific at the item level, not row level
                                        const oddSpecificElement = item.querySelector('td.sport span.odds_groups');
                                        const itemOddSpecific = oddSpecificElement ? oddSpecificElement.textContent.trim() : '';
                                        console.log("Found odd specific:", itemOddSpecific);
                                        
                                        // Extract bookmaker rows
                                        const rows = item.querySelectorAll('tr.odd_row');
                                        console.log(`Found ${rows.length} bookmaker rows`);
                                        
                                        // Initialize arrays for bookmaker data
                                        const bookmakers = [];
                                        const teams = [];
                                        const leagues = [];
                                        const betTypes = [];
                                        const odds = [];
                                        const links = [];
                                        
                                        // Process each bookmaker row
                                        rows.forEach((row, rowIndex) => {
                                            // Extract bookmaker name
                                            const bookmakerElement = row.querySelector('td.bookmaker_td');
                                            const bookmaker = bookmakerElement ? bookmakerElement.textContent.trim() : `Unknown-${rowIndex}`;
                                            bookmakers.push(bookmaker);
                                            
                                            // Extract teams
                                            let team1 = 'Unknown';
                                            let team2 = 'Unknown';
                                            const teamsElement = row.querySelector('div.teams a span');
                                            if (teamsElement) {
                                                const teamText = teamsElement.textContent.trim();
                                                // Try different delimiters
                                                let teamParts;
                                                if (teamText.includes(' - ')) {
                                                    teamParts = teamText.split(' - ');
                                                } else if (teamText.includes(' vs ')) {
                                                    teamParts = teamText.split(' vs ');
                                                } else if (teamText.includes('–')) {
                                                    teamParts = teamText.split('–');
                                                } else if (teamText.includes('-')) {
                                                    teamParts = teamText.split('-');
                                                }
                                                
                                                if (teamParts && teamParts.length === 2) {
                                                    team1 = teamParts[0].trim();
                                                    team2 = teamParts[1].trim();
                                                } else if (teamText) {
                                                    team1 = teamText;
                                                }
                                            }
                                            teams.push({ team1, team2 });
                                            
                                            // Extract league
                                            const leagueElement = row.querySelector('p.liga');
                                            const league = leagueElement ? leagueElement.textContent.trim() : 'Unknown';
                                            leagues.push(league);
                                            
                                            // Extract bet type
                                            const betTypeElement = row.querySelector('td.odds_types abbr span');
                                            const betType = betTypeElement ? betTypeElement.textContent.trim() : 'Unknown';
                                            betTypes.push(betType);
                                            
                                            // Extract odds - try multiple methods
                                            let odd = 'Unknown';
                                            // Method 1: value.values
                                            const valueValuesCell = row.querySelector('td.value.values div');
                                            if (valueValuesCell) {
                                                const valueText = valueValuesCell.textContent;
                                                const oddMatch = valueText.match(/[0-9.]+/);
                                                if (oddMatch) {
                                                    odd = oddMatch[0];
                                                }
                                            } else {
                                                // Method 2: Input fields
                                                const oddElement = row.querySelector('input[id^="coef_input_"]');
                                                if (oddElement && oddElement.value) {
                                                    odd = oddElement.value;
                                                }
                                            }
                                            odds.push(odd);
                                            
                                            // Extract bookmaker links
                                            let link = 'Unknown';
                                            const linkElement = row.querySelector('div.teams a');
                                            if (linkElement) {
                                                const relativeLink = linkElement.getAttribute('href');
                                                if (relativeLink) {
                                                    if (relativeLink.startsWith('/en/go?url=')) {
                                                        try {
                                                            const urlParam = relativeLink.substring('/en/go?url='.length);
                                                            link = decodeURIComponent(urlParam);
                                                        } catch (e) {
                                                            link = 'https://breaking-bet.com' + relativeLink;
                                                        }
                                                    } else {
                                                        link = 'https://breaking-bet.com' + relativeLink;
                                                    }
                                                }
                                            }
                                            links.push(link);
                                        });
                                        
                                        // Create opportunity object with correct schema
                                        opportunities.push({
                                            profit,
                                            sport,
                                            event_time: eventTime,
                                            odd_specific: itemOddSpecific || '',  // FIXED: Use the item level odd_specific
                                            
                                            // First bookmaker details
                                            bookmaker1: bookmakers[0] || 'Unknown',
                                            team1_bk1: teams[0]?.team1 || 'Unknown',
                                            team2_bk1: teams[0]?.team2 || 'Unknown',
                                            league_bk1: leagues[0] || 'Unknown',
                                            bet_type_bk1: betTypes[0] || 'Unknown',
                                            odd_bk1: odds[0] || 'Unknown',
                                            link_bk1: links[0] || 'Unknown',
                                            
                                            // Second bookmaker details
                                            bookmaker2: bookmakers[1] || 'Unknown',
                                            team1_bk2: teams[1]?.team1 || 'Unknown',
                                            team2_bk2: teams[1]?.team2 || 'Unknown', 
                                            league_bk2: leagues[1] || 'Unknown',
                                            bet_type_bk2: betTypes[1] || 'Unknown',
                                            odd_bk2: odds[1] || 'Unknown',
                                            link_bk2: links[1] || 'Unknown',
                                            
                                            // Original raw data arrays for reference
                                            bookmakers,
                                            teams,
                                            leagues,
                                            bet_types: betTypes,
                                            odds,
                                            links,
                                            
                                            // Additional metadata for detailed pages
                                            detailed_page: true,
                                            detailed_page_url: pageUrl,
                                            matchup: teams[0]?.team1 + " vs " + teams[0]?.team2
                                        });
                                    } catch (e) {
                                        console.error(`Error extracting detailed item ${index}:`, e);
                                        opportunities.push({
                                            error: e.toString(),
                                            index: index,
                                            detailed_page: true,
                                            detailed_page_url: pageUrl
                                        });
                                    }
                                });
                                
                                return opportunities;
                            } catch (e) {
                                console.error("Extraction error:", e);
                                return [{error: e.toString(), detailed_page_error: true}];
                            }
                        }
                    """)
                    
                    logger.info(f"Extracted {len(detailed_page_opportunities)} detailed opportunities")
                    
                    # FIX: Directly add the opportunities to our collection without filtering
                    # Instead of using detailed_page_opportunities_to_add which is being filtered
                    if len(detailed_page_opportunities) > 0:
                        # Add all opportunities directly
                        detailed_opportunities.extend(detailed_page_opportunities)
                        logger.info(f"Added {len(detailed_page_opportunities)} opportunities to our collection")
                    else:
                        logger.warning(f"No opportunities extracted from detailed page {i+1}")
                    
                    # Take a screenshot for debugging
                    page.screenshot(path=f"detailed_page_{i}_after_extraction.png")
                    
                    # Save raw HTML for debugging
                    html_content = page.content()
                    with open(f"detailed_page_{i}.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                    
                    # If we got some data, process it further
                    if isinstance(detailed_page_opportunities, list) and detailed_page_opportunities and 'error' in detailed_page_opportunities[0]:
                        logger.error(f"Error in detailed page extraction: {detailed_page_opportunities[0]['error']}")
                        
                        # Take extra screenshot to help debug
                        page.screenshot(path=f"detailed_page_error_{i}.png")
                        
                        # Get the current HTML for debugging
                        error_html = page.content()
                        with open(f"detailed_page_error_{i}.html", "w", encoding="utf-8") as f:
                            f.write(error_html)
                        
                        # Try to continue with next link
                        continue
                    else:
                        logger.warning(f"No opportunities extracted from detailed page {i+1}")
                    
                    # Go back to the main page
                    logger.info("Returning to main page...")
                    page.go_back()
                    
                    # Wait for the main page to load again with longer timeout
                    logger.info("Waiting 3 seconds after going back...")
                    time.sleep(3)
                    page.wait_for_selector('.loot_wrap', timeout=60000)
                    
                except Exception as e:
                    logger.error(f"Error processing 'show all' link: {str(e)}")
                    # Take a screenshot of the error
                    page.screenshot(path=f"error_show_all_{i}.png")
                    # Try to go back to the main page
                    try:
                        page.go_back()
                        time.sleep(3)  # Wait after going back
                        page.wait_for_selector('.loot_wrap', timeout=60000)
                    except:
                        # If we can't go back, try going to the main URL again
                        logger.warning("Failed to go back, navigating to main page directly")
                        page.goto("https://breaking-bet.com/en/arbs/prematch")
                        time.sleep(5)  # Longer wait for main page
                        page.wait_for_selector('.loot_wrap', timeout=60000)
            
            # Process all collected opportunities
            all_opportunities = main_opportunities + detailed_opportunities
            
            # FIX: Skip filtering and just report the count
            logger.info(f"Total opportunities found: {len(all_opportunities)}")
            
            # FIX: Always save opportunities, even if there's only a few
            if len(all_opportunities) > 0:
                # Create timestamp for filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Create directory if it doesn't exist
                os.makedirs("opportunities", exist_ok=True)
                
                # Save to JSON file
                output_file =  r"arb_opportunities.json"
                with open(output_file, 'w') as f:
                    json.dump(all_opportunities, f, indent=2)
                
                # Also save a copy to fixed location for easy access
                with open("arb_opportunities.json", 'w') as f:
                    json.dump(all_opportunities, f, indent=2)
                    
                logger.info(f"✅ Saved {len(all_opportunities)} arbitrage opportunities to {output_file}")
                return all_opportunities
            else:
                logger.warning("⚠️ No opportunities found to save")
                
            
                empty_opportunities = []
    
                output_file = r"arb_opportunities.json"
                with open(output_file, 'w') as f:
                 json.dump(empty_opportunities, f, indent=2)
    
                with open("arb_opportunities.json", 'w') as f:
                  json.dump(empty_opportunities, f, indent=2)
    
                logger.info("🧹 Cleared opportunities file (set to empty array)")
                return []
            
            
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            logger.error(traceback.format_exc())
            page.screenshot(path="error.png")
            return []
            
        finally:
            browser.close()
            logger.info("Browser closed")

if __name__ == "__main__":
    logger.info("=== Starting Arbitrage Scraper ===")
    try:
        opportunities = scrape_arbitrage_opportunities()
        logger.info(f"Scraping complete. Found {len(opportunities)} opportunities")
        
        if opportunities:
            logger.info("Sample opportunity:")
            logger.info(json.dumps(opportunities[0], indent=2))
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())