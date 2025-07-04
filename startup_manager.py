#!/usr/bin/env python3
"""
Startup Manager for Arbitrage System
Checks config and launches appropriate script
"""

import sys
import os
import subprocess
from config_manager import ConfigManager

def check_config_status():
    """Check if config has enough enabled bookmakers"""
    try:
        config = ConfigManager()
        enabled_bookmakers = config.get_enabled_bookmakers()
        
        print("="*50)
        print("🔍 ARBITRAGE SYSTEM STARTUP CHECK")
        print("="*50)
        
        # Check how many bookmakers are enabled
        enabled_count = len(enabled_bookmakers)
        
        print(f"📊 Found {enabled_count} enabled bookmakers:")
        for name, data in enabled_bookmakers.items():
            username = data.get("username", "")
            cred_status = "✅ Configured" if username else "⚠️ No credentials"
            print(f"  • {name} (ID: {data.get('id', 'N/A')}) - {cred_status}")
        
        print()
        
        # Check if we have enough bookmakers
        if enabled_count < 2:
            print("❌ INSUFFICIENT BOOKMAKERS")
            print("   Need at least 2 enabled bookmakers for arbitrage betting.")
            print("   Starting configuration setup...")
            print()
            return False
        else:
            print("✅ CONFIGURATION READY")
            print("   Sufficient bookmakers enabled. Starting main system...")
            print()
            return True
            
    except Exception as e:
        print(f"❌ ERROR checking config: {e}")
        print("   Starting configuration setup to fix the issue...")
        print()
        return False

def run_setup_config():
    """Run the setup_config.py script"""
    try:
        print("🔧 Starting Configuration Setup...")
        print("-" * 30)
        
        # Run setup_config.py
        result = subprocess.run([sys.executable, "setup_config.py"], check=True)
        
        print("-" * 30)
        print("✅ Configuration setup completed!")
        print()
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Configuration setup failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ setup_config.py not found in current directory")
        return False
    except Exception as e:
        print(f"❌ Error running setup_config.py: {e}")
        return False

def run_mainrunner():
    """Run the mainrunner.py script"""
    try:
        print("🚀 Starting Arbitrage Main Runner...")
        print("-" * 40)
        
        # Run mainrunner.py
        result = subprocess.run([sys.executable, "mainrunner.py"], check=True)
        
        print("-" * 40)
        print("✅ Main runner completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Main runner failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ mainrunner.py not found in current directory")
        return False
    except KeyboardInterrupt:
        print("\n⚠️ Main runner interrupted by user")
        return True  # This is normal
    except Exception as e:
        print(f"❌ Error running mainrunner.py: {e}")
        return False

def main():
    """Main startup logic"""
    print("🎯 ARBITRAGE SYSTEM LAUNCHER")
    print("=" * 50)
    
    # Check if we're in the right directory
    required_files = ["config_manager.py", "mainrunner.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("   Please run this script from the agent directory")
        sys.exit(1)
    
    # Check config status
    config_ready = check_config_status()
    
    if not config_ready:
        # Need to run setup
        if not run_setup_config():
            print("❌ Setup failed. Please check the configuration manually.")
            sys.exit(1)
        
        # After setup, check config again
        print("🔄 Rechecking configuration...")
        config_ready = check_config_status()
        
        if not config_ready:
            print("❌ Configuration still not ready after setup.")
            print("   Please run setup_config.py manually and enable at least 2 bookmakers.")
            sys.exit(1)
    
    # Config is ready, run main runner
    if not run_mainrunner():
        print("❌ Main runner failed.")
        sys.exit(1)
    
    print("🎉 Startup sequence completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Startup interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)