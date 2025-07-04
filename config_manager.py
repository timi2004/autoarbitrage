import json
import os
from typing import Dict, List, Optional

class ConfigManager:
    """
    Manages configuration settings for the arbitrage system
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            if not os.path.exists(self.config_path):
                print(f"⚠️ Config file {self.config_path} not found. Creating default config...")
                self.create_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"✅ Config loaded from {self.config_path}")
            return config
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in config file: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {}
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Config saved to {self.config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    
    
    # Executable methods
    def get_executable_config(self, path_name: str) -> Optional[Dict]:
        """Get executable configuration by path name"""
        return self.config.get("executables", {}).get(path_name)
    
    def get_all_executable_configs(self) -> Dict:
        """Get all executable configurations"""
        return self.config.get("executables", {})
    
    def set_executable_config(self, path_name: str, executable_path: str, user_data_dir: str):
        """Set executable configuration"""
        if "executables" not in self.config:
            self.config["executables"] = {}
        
        self.config["executables"][path_name] = {
            "executable_path": executable_path,
            "user_data_dir": user_data_dir
        }
    
    # Bookmaker methods
    def get_enabled_bookmakers(self) -> Dict[str, Dict]:
        """Get only enabled bookmakers"""
        bookmakers = self.config.get("bookmakers", {})
        return {name: data for name, data in bookmakers.items() if data.get("enabled", False)}
    
    def get_all_bookmakers(self) -> Dict[str, Dict]:
        """Get all bookmakers (enabled and disabled)"""
        return self.config.get("bookmakers", {})
    
    def get_bookmaker_credentials(self, bookmaker_name: str) -> Optional[Dict]:
        """Get credentials for a specific bookmaker"""
        bookmaker = self.config.get("bookmakers", {}).get(bookmaker_name)
        if bookmaker:
            return {
                "username": bookmaker.get("username", ""),
                "password": bookmaker.get("password", ""),
                "url": bookmaker.get("url", "")
            }
        return None
    
    def set_bookmaker_credentials(self, bookmaker_name: str, username: str, password: str):
        """Set credentials for a bookmaker"""
        if "bookmakers" not in self.config:
            self.config["bookmakers"] = {}
        
        if bookmaker_name in self.config["bookmakers"]:
            self.config["bookmakers"][bookmaker_name]["username"] = username
            self.config["bookmakers"][bookmaker_name]["password"] = password
        else:
            print(f"⚠️ Bookmaker {bookmaker_name} not found in config")
    
    def enable_bookmaker(self, bookmaker_name: str):
        """Enable a bookmaker"""
        if bookmaker_name in self.config.get("bookmakers", {}):
            self.config["bookmakers"][bookmaker_name]["enabled"] = True
            print(f"✅ Enabled bookmaker: {bookmaker_name}")
        else:
            print(f"⚠️ Bookmaker {bookmaker_name} not found")
    
    def disable_bookmaker(self, bookmaker_name: str):
        """Disable a bookmaker"""
        if bookmaker_name in self.config.get("bookmakers", {}):
            self.config["bookmakers"][bookmaker_name]["enabled"] = False
            print(f"🔴 Disabled bookmaker: {bookmaker_name}")
        else:
            print(f"⚠️ Bookmaker {bookmaker_name} not found")
    
    def get_target_bookmakers_for_scraper(self) -> List[int]:
        """
        Get list of bookmaker IDs for enabled bookmakers
        This is what should be used in arb_scraper.py as target_bookmakers
        """
        enabled_bookmakers = self.get_enabled_bookmakers()
        target_ids = [data["id"] for data in enabled_bookmakers.values() if "id" in data]
        
        print(f"🎯 Target bookmaker IDs for scraper: {target_ids}")
        print(f"📋 Enabled bookmakers: {list(enabled_bookmakers.keys())}")
        
        return target_ids
    
    # Scraper settings methods
    def get_scraper_settings(self) -> Dict:
        """Get scraper settings"""
        return self.config.get("scraper_settings", {})
    
    def set_scraper_setting(self, key: str, value):
        """Set a scraper setting"""
        if "scraper_settings" not in self.config:
            self.config["scraper_settings"] = {}
        
        self.config["scraper_settings"][key] = value
    
    # Utility methods
    def print_status(self):
        """Print current configuration status"""
        print("\n" + "="*50)
        print("📋 CONFIGURATION STATUS")
        print("="*50)
        
        # Executables
        print("\n🖥️ EXECUTABLES:")
        for name, config in self.get_all_executable_configs().items():
            print(f"  {name}:")
            print(f"    Path: {config.get('executable_path', 'Not set')}")
            print(f"    User Dir: {config.get('user_data_dir', 'Not set')}")
        
        # Bookmakers
        print("\n📚 BOOKMAKERS:")
        enabled = self.get_enabled_bookmakers()
        disabled = {k: v for k, v in self.get_all_bookmakers().items() if not v.get("enabled", False)}
        
        print(f"  ✅ Enabled ({len(enabled)}):")
        for name, data in enabled.items():
            username = data.get("username", "")
            status = "✅ Configured" if username else "⚠️ No credentials"
            print(f"    {name} (ID: {data.get('id', 'N/A')}) - {status}")
        
        print(f"  🔴 Disabled ({len(disabled)}):")
        for name, data in disabled.items():
            print(f"    {name} (ID: {data.get('id', 'N/A')})")
        
        # Target bookmakers for scraper
        target_ids = self.get_target_bookmakers_for_scraper()
        print(f"\n🎯 SCRAPER TARGET IDs: {target_ids}")
        
        print("="*50 + "\n")


# Example usage and testing
def main():
    """Example usage of ConfigManager"""
    config = ConfigManager()
    
    # Print current status
    config.print_status()
    
    # Example: Enable/disable bookmakers
    # config.enable_bookmaker("1win")
    # config.disable_bookmaker("nairabet")
    
    # Example: Set credentials
    # config.set_bookmaker_credentials("bet9ja", "your_username", "your_password")
    
    # Example: Get target bookmakers for scraper
    target_bookmakers = config.get_target_bookmakers_for_scraper()
    print(f"Use this in arb_scraper.py: target_bookmakers = {target_bookmakers}")
    
    # Save any changes
    # config.save_config()


if __name__ == "__main__":
    main()