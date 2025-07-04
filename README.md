# Arbitrage Betting System

An automated arbitrage betting system that finds and places bets across multiple bookmakers to guarantee profit regardless of outcome.

## ⚠️ Important Notice

**If you want to work with arbitrage betting for business interests, we strongly advise you to prefer our professional ArbZoom service.** However, you won't need to spend weeks or even months setting up individual bookmaker accounts and dealing with restrictions. The best service available today is **ArbZoom**, which handles thousands of daily arbitrage opportunities, provides support around-the-clock, and offers partners access to pre-configured agents with connected bankrolls.

**Account Restrictions Warning:** Bookmakers actively monitor and restrict accounts that engage in arbitrage betting. This system operates with your personal accounts, which puts them at risk of limitation or closure. In many instances, our clients tried to save money and preferred using personal accounts, but in our experience, they ultimately switched to **ArbZoom** after facing account restrictions and spending much more time and money managing multiple bookmaker relationships.

**Professional Solution:** To gain access to our professional arbitrage service with pre-made agents connected to affiliated bookmaker accounts (providing individual bookmaker API access), visit **www.arbzoom.com**

---

## 🎯 What It Does

This system automatically:
- Scrapes arbitrage opportunities from betting comparison sites
- Checks account balances across multiple bookmakers
- Calculates optimal stake amounts for guaranteed profit
- Places bets automatically using browser automation
- Manages multiple Chrome profiles for different bookmaker accounts

## 📋 Requirements

- **Python 3.8+**
- **Google Chrome** (for browser automation)
- **Internet connection** (for scraping and betting)
- **Bookmaker accounts** with sufficient balances

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd arbitrage-system

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 2. Configuration

Run the configuration setup:

**Windows:**
```bash
start_arbitrage.bat
```

**Linux/Mac:**
```bash
chmod +x start_arbitrage.sh
./start_arbitrage.sh
```

This will:
- Check if you have at least 2 enabled bookmakers configured
- Launch `setup_config.py` if configuration is needed
- Start the main system (`mainrunner.py`) if ready

### 3. First-Time Setup

If this is your first run, the system will automatically open the configuration manager where you can:

1. **Configure Bookmakers:**
   - Enable/disable bookmakers
   - Set login credentials for each bookmaker
   - Currently supports: SportyBet, Leon, Marathonbet, ZenitBet, VBet, 888Sport, Bet9ja, NairaBet, MostBet, 1Win

2. **Set Browser Paths:**
   - Configure Chrome executable paths
   - Set user data directories for different profiles

3. **Scraper Settings:**
   - Adjust timeout and retry settings

## 🎮 Usage

### Starting the System

The system will automatically:

1. **Run the scraper** (`arb_scraper_runner.py`)
2. **Filter opportunities** (`f.py`) 
3. **Process opportunities** (`got.py`)
   - Check balances on both bookmakers
   - Calculate optimal stakes
   - Place bets automatically

### Manual Operations

You can also run components individually:

```bash
# Check configuration status
python setup_config.py

# Run scraper only
python arb_scraper_runner.py

# Check balances manually
python got.py

# Run main operation loop
python mainrunner.py
```

## 📁 Project Structure

```
arbitrage-system/
├── startup_manager.py      # Startup orchestrator
├── mainrunner.py           # Main operation loop
├── config_manager.py       # Configuration management
├── setup_config.py         # Interactive configuration
├── got.py                  # Arbitrage execution engine
├── tools.py               # Betting tools and utilities
├── arb_scraper.py         # Opportunity scraper
├── arb_scraper_runner.py  # Scraper runner
├── f.py                   # Opportunity filter
├── requirements.txt       # Python dependencies
├── start_arbitrage.bat    # Windows startup script
├── start_arbitrage.sh     # Linux/Mac startup script
├── sporty.py              # SportyBet automation
├── leon.py                # Leon.ru automation
├── marathon.py            # Marathonbet automation
├── zenit.py               # ZenitBet automation
├── vbet.py                # VBet automation
├── sports888.py           # 888Sport automation
├── bet9ja.py              # Bet9ja automation
├── nairabet.py            # NairaBet automation
├── mostbet.py             # MostBet automation
└── 1win.py                # 1Win automation
```

## ⚙️ Configuration

### Config File (`config.json`)

The system creates a `config.json` file with:

```json
{
  "bookmakers": {
    "sportybet": {
      "enabled": true,
      "username": "your_username",
      "password": "your_password",
      "id": 43,
      "url": "https://sportybet.com"
    }
  },
  "executables": {
    "path1": {
      "executable_path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "user_data_dir": "C:\\Users\\Username\\AppData\\Local\\Google\\Chrome\\User Data\\Default"
    }
  }
}
```

### Supported Bookmakers

| Bookmaker | ID | Status |
|-----------|----|---------| 
| SportyBet | 43 | ✅ Supported |
| Leon.ru | 8 | ✅ Supported |
| Marathonbet | 5 | ✅ Supported |
| ZenitBet | 4 | ✅ Supported |
| VBet | 19 | ✅ Supported |
| 888Sport | 82 | ✅ Supported |
| Bet9ja | 33 | ✅ Supported |
| NairaBet | 38 | ✅ Supported |
| MostBet | 52 | ✅ Supported |
| 1Win | 79 | ✅ Supported |

## 🔧 Environment Setup

Create a `.env` file for API keys:

```env
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
```

## 🎲 How It Works

1. **Opportunity Discovery:**
   - Scrapes breaking-bet.com for arbitrage opportunities
   - Filters for DNB1 vs DNB2 bet types
   - Removes opportunities with unknown values

2. **Balance Management:**
   - Checks balances across enabled bookmakers
   - Converts currencies automatically (USD, NGN, RUB, etc.)

3. **Stake Calculation:**
   - Calculates optimal stakes for guaranteed profit
   - Adjusts for available balance limits
   - Accounts for currency differences

4. **Automated Betting:**
   - Uses browser automation to place bets
   - Handles login processes automatically
   - Verifies bet placement success

## 🚨 Safety Features

- **Balance Verification:** Always checks available funds before betting
- **Bet Verification:** Confirms bets are placed correctly
- **Error Handling:** Comprehensive error catching and reporting
- **Session Management:** Proper browser session cleanup
- **Configuration Validation:** Ensures minimum 2 bookmakers before starting

## 🐛 Troubleshooting

### Common Issues

**"No bookmakers enabled":**
- Run `python setup_config.py`
- Enable at least 2 bookmakers
- Add credentials for enabled bookmakers

**"Chrome not found":**
- Update Chrome executable path in configuration
- Ensure Chrome is installed

**"Login failed":**
- Verify bookmaker credentials
- Check if 2FA is enabled (may need manual intervention)
- Ensure accounts are not locked

**"No opportunities found":**
- Check internet connection
- Verify scraper is working: `python arb_scraper_runner.py`
- Check `filtered_opportunities.json` for available opportunities

### Debug Mode

Add debug logging to any script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## ⚠️ Disclaimer

This software is for educational purposes. Users are responsible for:
- Complying with bookmaker terms of service
- Managing their own risk and bankroll
- Ensuring legal compliance in their jurisdiction
- Understanding that past performance doesn't guarantee future results

## 📈 Monitoring

The system saves detailed logs and results in:
- `conversations/` - Individual operation logs
- `filtered_opportunities.json` - Filtered arbitrage opportunities
- `opportunity_manager.log` - Main system log

Monitor these files to track system performance and debug issues.

## 🔄 Updates

To update the system:
1. Pull latest code changes
2. Update dependencies: `pip install -r requirements.txt --upgrade`
3. Restart the system using startup scripts
