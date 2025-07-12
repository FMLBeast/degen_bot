"""
Crypto conversion commands
"""
import requests
import time
from modules.auth.authorization import check_chat_authorization
from modules.auth.rate_limiting import require_rate_limit
from utils.reply_helper import reply_to_message
from utils.user_helper import ensure_user_in_database
from config.logging_config import logger

# Global variables for caching
fiat_rates = None
crypto_rates = {}
last_fiat_fetch = 0
last_crypto_fetch = {}
FIAT_REFRESH_INTERVAL = 3600  # 1 hour in seconds
CRYPTO_REFRESH_INTERVAL = 300  # 5 minutes in seconds

def fetch_crypto_price(symbol, rapidapi_key):
    """Fetch crypto price from API"""
    if symbol == 'USDT':
        return 1.00
        
    current_time = time.time()
    if symbol in crypto_rates and (current_time - last_crypto_fetch.get(symbol, 0)) < CRYPTO_REFRESH_INTERVAL:
        return crypto_rates[symbol]
        
    url = "https://binance43.p.rapidapi.com/ticker/24hr"
    querystring = {"symbol": f"{symbol}USDT"}
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "binance43.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200 and 'lastPrice' in response.json():
            price = float(response.json()['lastPrice'])
            crypto_rates[symbol] = price
            last_crypto_fetch[symbol] = current_time
            return price
    except Exception as e:
        logger.error(f"Error fetching crypto price: {e}")
    return None

def fetch_fiat_rates():
    """Fetch fiat exchange rates"""
    global fiat_rates, last_fiat_fetch
    current_time = time.time()
    
    if fiat_rates is None or (current_time - last_fiat_fetch) > FIAT_REFRESH_INTERVAL:
        try:
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url)
            response.raise_for_status()
            fiat_rates = response.json()['rates']
            last_fiat_fetch = current_time
        except Exception as e:
            logger.error(f"Error fetching fiat rates: {e}")
            return {}
    
    return fiat_rates

def format_number(number):
    """Format number with appropriate decimal places"""
    if abs(number) < 0.01:
        return f"{number:.8f}"
    elif abs(number) < 1:
        return f"{number:.4f}"
    else:
        return f"{number:,.2f}"

async def convert_crypto(update, context):
    """Handle crypto conversion command"""
    if not await check_chat_authorization(update, context):
        return
    
    # Ensure user exists in database
    ensure_user_in_database(update)
    
    if not await require_rate_limit(update.effective_user.id, 'convert', update, context):
        return
    
    if len(context.args) not in [2, 3]:
        await reply_to_message(update, context,
            "Usage:\n"
            "• `/convert <amount> <from_symbol>` (converts to USD)\n"
            "• `/convert <amount> <from_symbol> <to_symbol>`\n\n"
            "Examples:\n"
            "• `/convert 100 BTC`\n"
            "• `/convert 1.5 ETH BTC`"
        )
        return

    try:
        amount = float(context.args[0])
        symbol_from = context.args[1].upper()
        symbol_to = context.args[2].upper() if len(context.args) == 3 else 'USD'

        # Get API key from environment
        rapidapi_key = context.bot_data.get('rapidapi_key')
        if not rapidapi_key:
            await reply_to_message(update, context, "❌ Crypto API not configured.")
            return

        fiat_rates = fetch_fiat_rates()
        usd_value = None
        
        # Convert from currency to USD
        if symbol_from in fiat_rates:
            usd_value = amount / fiat_rates[symbol_from]
        else:
            price_from = fetch_crypto_price(symbol_from, rapidapi_key)
            if price_from is None:
                await reply_to_message(update, context, f"❌ Unable to fetch price for {symbol_from}")
                return
            usd_value = amount * price_from

        # Convert USD to target currency
        if symbol_to == 'USD':
            final_value = usd_value
        elif symbol_to in fiat_rates:
            final_value = usd_value * fiat_rates[symbol_to]
        else:
            price_to = fetch_crypto_price(symbol_to, rapidapi_key)
            if price_to is None:
                await reply_to_message(update, context, f"❌ Unable to fetch price for {symbol_to}")
                return
            final_value = usd_value / price_to

        response = (
            f"💱 **Currency Conversion**\n\n"
            f"**From:** {format_number(amount)} {symbol_from}\n"
            f"**To:** {format_number(final_value)} {symbol_to}"
        )

        if symbol_from != 'USD' and symbol_to != 'USD':
            response += f"\n**USD Value:** ${format_number(usd_value)}"
        
        await reply_to_message(update, context, response, parse_mode='Markdown')
        
    except ValueError:
        await reply_to_message(update, context, "❌ Please provide a valid amount.")
    except Exception as e:
        logger.error(f"Crypto conversion error: {e}")
        await reply_to_message(update, context, f"❌ Error: {str(e)}")
