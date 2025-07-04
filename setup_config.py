#!/usr/bin/env python3
"""
Interactive configuration setup for the arbitrage system
"""

from config_manager import ConfigManager
import getpass

def main_menu(config):
    """Display main menu and handle user choices"""
    while True:
        print("\n" + "="*50)
        print("🔧 ARBITRAGE SYSTEM CONFIG MANAGER")
        print("="*50)
        print("1. View current status")
        print("2. Manage bookmakers")
        print("3. Set browser/executable paths")
        print("4. Set scraper settings")
        print("5. Save and exit")
        print("6. Exit without saving")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            config.print_status()
        elif choice == "2":
            manage_bookmakers(config)
        elif choice == "3":
            set_browser_paths(config)
        elif choice == "4":
            set_scraper_settings(config)
        elif choice == "5":
            config.save_config()
            print("✅ Configuration saved! Exiting...")
            break
        elif choice == "6":
            print("❌ Exiting without saving...")
            break
        else:
            print("❌ Invalid choice. Please try again.")

def manage_bookmakers(config):
    """Manage bookmaker settings"""
    while True:
        print("\n" + "="*40)
        print("📚 BOOKMAKER MANAGEMENT")
        print("="*40)
        
        bookmakers = config.get_all_bookmakers()
        
        print("\nCurrent bookmakers:")
        for i, (name, data) in enumerate(bookmakers.items(), 1):
            status = "✅ Enabled" if data.get("enabled") else "🔴 Disabled"
            username = data.get("username", "")
            cred_status = "✅ Configured" if username else "⚠️ No credentials"
            print(f"{i:2d}. {name:<12} - {status:<12} - {cred_status}")
        
        print(f"\n{len(bookmakers)+1:2d}. Return to main menu")
        
        choice = input(f"\nSelect bookmaker to configure (1-{len(bookmakers)+1}): ").strip()
        
        try:
            choice_num = int(choice)
            if choice_num == len(bookmakers) + 1:
                break
            elif 1 <= choice_num <= len(bookmakers):
                bookmaker_name = list(bookmakers.keys())[choice_num - 1]
                configure_bookmaker(config, bookmaker_name)
            else:
                print("❌ Invalid choice.")
        except ValueError:
            print("❌ Please enter a valid number.")

def configure_bookmaker(config, bookmaker_name):
    """Configure a specific bookmaker"""
    bookmaker_data = config.get_all_bookmakers()[bookmaker_name]
    
    while True:
        print(f"\n" + "="*40)
        print(f"⚙️ CONFIGURING: {bookmaker_name.upper()}")
        print("="*40)
        
        enabled = bookmaker_data.get("enabled", False)
        username = bookmaker_data.get("username", "")
        
        print(f"Current status: {'✅ Enabled' if enabled else '🔴 Disabled'}")
        print(f"Username: {username if username else '⚠️ Not set'}")
        print(f"ID: {bookmaker_data.get('id', 'N/A')}")
        print(f"URL: {bookmaker_data.get('url', 'N/A')}")
        
        print("\nOptions:")
        print("1. Enable/Disable")
        print("2. Set credentials")
        print("3. Back to bookmaker list")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            if enabled:
                config.disable_bookmaker(bookmaker_name)
            else:
                config.enable_bookmaker(bookmaker_name)
            bookmaker_data = config.get_all_bookmakers()[bookmaker_name]  # Refresh data
            
        elif choice == "2":
            print(f"\nSetting credentials for {bookmaker_name}:")
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            
            if username and password:
                config.set_bookmaker_credentials(bookmaker_name, username, password)
                print("✅ Credentials set successfully!")
            else:
                print("❌ Both username and password are required.")
                
        elif choice == "3":
            break
        else:
            print("❌ Invalid choice.")

def set_browser_paths(config):
    """Set browser/executable paths"""
    while True:
        print("\n" + "="*40)
        print("🖥️ BROWSER/EXECUTABLE PATHS")
        print("="*40)
        
        executables = config.get_all_executable_configs()
        
        print("\nCurrent configurations:")
        for i, (name, data) in enumerate(executables.items(), 1):
            print(f"{i}. {name}:")
            print(f"   Executable: {data.get('executable_path', 'Not set')}")
            print(f"   User Dir: {data.get('user_data_dir', 'Not set')}")
        
        print(f"{len(executables)+1}. Add new configuration")
        print(f"{len(executables)+2}. Return to main menu")
        
        choice = input(f"\nSelect option (1-{len(executables)+2}): ").strip()
        
        try:
            choice_num = int(choice)
            if choice_num == len(executables) + 2:
                break
            elif choice_num == len(executables) + 1:
                add_executable_config(config)
            elif 1 <= choice_num <= len(executables):
                config_name = list(executables.keys())[choice_num - 1]
                edit_executable_config(config, config_name)
            else:
                print("❌ Invalid choice.")
        except ValueError:
            print("❌ Please enter a valid number.")

def add_executable_config(config):
    """Add a new executable configuration"""
    print("\n➕ Adding new executable configuration:")
    name = input("Configuration name (e.g., 'path3'): ").strip()
    
    if name in config.get_all_executable_configs():
        print(f"❌ Configuration '{name}' already exists!")
        return
    
    executable_path = input("Executable path: ").strip()
    user_data_dir = input("User data directory: ").strip()
    
    if name and executable_path:
        config.set_executable_config(name, executable_path, user_data_dir)
        print(f"✅ Added configuration '{name}'!")
    else:
        print("❌ Name and executable path are required.")

def edit_executable_config(config, config_name):
    """Edit an existing executable configuration"""
    current = config.get_executable_config(config_name)
    
    print(f"\n✏️ Editing configuration: {config_name}")
    print(f"Current executable: {current.get('executable_path', 'Not set')}")
    print(f"Current user dir: {current.get('user_data_dir', 'Not set')}")
    
    executable_path = input("New executable path (press Enter to keep current): ").strip()
    user_data_dir = input("New user data directory (press Enter to keep current): ").strip()
    
    if not executable_path:
        executable_path = current.get('executable_path', '')
    if not user_data_dir:
        user_data_dir = current.get('user_data_dir', '')
    
    config.set_executable_config(config_name, executable_path, user_data_dir)
    print(f"✅ Updated configuration '{config_name}'!")

def set_scraper_settings(config):
    """Set scraper settings"""
    print("\n" + "="*40)
    print("⚙️ SCRAPER SETTINGS")
    print("="*40)
    
    current_settings = config.get_scraper_settings()
    
    print("\nCurrent settings:")
    for key, value in current_settings.items():
        print(f"  {key}: {value}")
    
    print("\nEnter new values (press Enter to keep current):")
    
    settings_to_update = {
        "max_opportunities": "Maximum opportunities to fetch",
        "timeout_seconds": "Timeout in seconds", 
        "retry_attempts": "Number of retry attempts",
        "delay_between_requests": "Delay between requests (seconds)"
    }
    
    for key, description in settings_to_update.items():
        current_value = current_settings.get(key, "")
        new_value = input(f"{description} [{current_value}]: ").strip()
        
        if new_value:
            try:
                # Try to convert to int/float if it's a number
                if '.' in new_value:
                    new_value = float(new_value)
                else:
                    new_value = int(new_value)
                config.set_scraper_setting(key, new_value)
                print(f"✅ Updated {key}")
            except ValueError:
                print(f"❌ Invalid value for {key}")

if __name__ == "__main__":
    print("🚀 Starting Arbitrage System Configuration...")
    
    config = ConfigManager()
    main_menu(config)
    
    print("👋 Configuration complete!")