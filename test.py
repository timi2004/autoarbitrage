import requests
from currency_converter import CurrencyConverter

def currency_converter(amount: float, from_currency: str, to_currency: str) -> float:
    """
    Hybrid currency converter using currency_converter library with API fallback
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., 'USD', 'EUR')  
        to_currency: Target currency code (e.g., 'NGN', 'GBP')
    
    Returns:
        Converted amount as float
        
    Priority:
    1. currency_converter library (fast, offline)
    2. exchangerate-api.com (fallback for unsupported currencies like NGN, RUB)
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # Method 1: Try currency_converter library first
    def try_currency_converter_library():
        try:
            c = CurrencyConverter()
            result = c.convert(amount, from_currency, to_currency)
            return round(result, 2)
        except Exception as e:
            raise Exception(f"currency_converter library failed: {e}")
    
    # Method 2: API fallback using exchangerate-api.com
    def try_api_fallback():
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if to_currency not in data['rates']:
                raise Exception(f"Currency {to_currency} not supported by API")
            
            rate = data['rates'][to_currency]
            result = amount * rate
            return round(result, 2)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
        except Exception as e:
            raise Exception(f"API conversion failed: {e}")
    
    # Currencies that typically need API fallback
    api_required_currencies = {'NGN', 'RUB', 'TRY', 'IRR', 'PKR', 'BDT', 'LKR', 'VES', 'MMK'}
    
    # If either currency requires API, skip library and go straight to API
    if from_currency in api_required_currencies or to_currency in api_required_currencies:
        try:
            print(f"🌐 Using API for {from_currency}→{to_currency} (special currency)")
            return try_api_fallback()
        except Exception as e:
            raise Exception(f"API failed for special currency conversion: {e}")
    
    # For standard currencies, try library first, then API fallback
    try:
        print(f"📚 Using currency_converter library for {from_currency}→{to_currency}")
        return try_currency_converter_library()
        
    except Exception as library_error:
        print(f"❌ Library failed: {library_error}")
        print(f"🌐 Falling back to API for {from_currency}→{to_currency}")
        
        try:
            return try_api_fallback()
        except Exception as api_error:
            raise Exception(f"Both methods failed. Library: {library_error}, API: {api_error}")

if __name__ == "__main__":
    try:
        # Test conversions
        result1 = currency_converter(100, 'USD', 'NGN')
        print(f"100 USD = {result1} NGN")
        
        result2 = currency_converter(1000, 'NGN', 'USD')
        print(f"1000 NGN = {result2} USD")
        
        result3 = currency_converter(50, 'EUR', 'GBP')
        print(f"50 EUR = {result3} GBP")
        result3 = currency_converter(50, 'EUR', 'GBP')
        print(f"50 EUR = {result3} GBP")
        
    except Exception as e:
        print(f"Error: {e}")