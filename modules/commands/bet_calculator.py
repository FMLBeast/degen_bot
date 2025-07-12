"""
Bet calculator commands with topic support
"""
from modules.auth.authorization import check_chat_authorization
from utils.reply_helper import reply_to_message
from utils.user_helper import ensure_user_in_database

def format_number(n):
    """Format number with appropriate suffixes."""
    if abs(n) >= 1e9:
        return f"{n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"{n/1e6:.2f}M"
    if abs(n) >= 1e3:
        return f"{n/1e3:.2f}K"
    return f"{n:.2f}"

def calculate_bets(base_bet, multiplier, increase_percentage, iterations=20):
    """Calculate betting progression"""
    bets = [base_bet]
    net_results = []
    total = 0

    for i in range(1, iterations + 1):
        net_result = bets[-1] * multiplier
        total += net_result
        next_bet = bets[-1] * (1 + increase_percentage / 100)
        
        bets.append(next_bet)
        net_results.append(net_result)

    return bets[:iterations], net_results, total

async def calculate_bet(update, context):
    """Handle bet calculation command"""
    if not await check_chat_authorization(update, context):
        return
    
    # Ensure user exists in database
    ensure_user_in_database(update)
    
    if len(context.args) != 3:
        await reply_to_message(update, context,
            "Usage: `/bet <base_bet> <multiplier> <increase_%>`\n\n"
            "Example: `/bet 10 1.5 10`",
            parse_mode='Markdown'
        )
        return

    try:
        base_bet = float(context.args[0].replace(",", "."))
        multiplier = float(context.args[1].replace(",", "."))
        increase_percentage = float(context.args[2].replace(",", "."))
    except ValueError:
        await reply_to_message(update, context,
            "❌ Please provide valid numbers for all parameters.",
            parse_mode='Markdown'
        )
        return

    bets, net_results, total = calculate_bets(base_bet, multiplier, increase_percentage)

    # Create header and table with monospace formatting
    result_message = (
        "🎲 *Betting Progression Analysis* 🎲\n\n"
        "```\n"
        "┌─────────┬───────────┬───────────┬───────────┐\n"
        "│  Round  │ Bet Size  │  Result   │   Total   │\n"
        "├─────────┼───────────┼───────────┼───────────┤\n"
    )
    
    # Add table rows
    current_total = 0
    for i, (bet, net_result) in enumerate(zip(bets, net_results), start=1):
        current_total += net_result
        result_message += (
            f"│ {str(i):<8}│ {format_number(bet):<10}│ {format_number(net_result):<10}│ "
            f"{format_number(current_total):<10}│\n"
        )

    # Close table
    result_message += (
        "└─────────┴───────────┴───────────┴───────────┘\n"
        "```\n\n"
    )

    # Add summary
    summary = (
        f"📈 *Initial Bet:* `{base_bet}`\n"
        f"📊 *Multiplier:* `{multiplier:.1f}x`\n"
        f"📋 *Increase:* `{increase_percentage:.1f}%`"
    )

    # Send message with proper markdown parsing
    await reply_to_message(update, context,
        result_message + summary,
        parse_mode='Markdown'
    )
