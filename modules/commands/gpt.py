"""
GPT commands with topic support
"""
import openai
from modules.auth.authorization import check_chat_authorization
from modules.auth.rate_limiting import require_rate_limit
from utils.reply_helper import reply_to_message
from utils.user_helper import ensure_user_in_database
from config.logging_config import logger

async def ask_gpt(update, context):
    """Handle ask GPT command for open questions"""
    if not await check_chat_authorization(update, context):
        return
    
    # Ensure user exists in database
    ensure_user_in_database(update)
    
    if not await require_rate_limit(update.effective_user.id, 'ask_gpt', update, context):
        return
    
    if not context.args:
        await reply_to_message(update, context,
            "🤖 **Ask GPT anything!**\n\n"
            "Usage: `/ask <your question>`\n\n"
            "Examples:\n"
            "• `/ask What is the meaning of life?`\n"
            "• `/ask How do I cook pasta?`\n"
            "• `/ask Explain quantum physics simply`\n"
            "• `/ask Write a haiku about cats`",
            parse_mode='Markdown'
        )
        return

    # Join all arguments to form the complete question
    question = ' '.join(context.args)
    username = update.effective_user.first_name or update.effective_user.username or "Someone"
    
    # Show thinking message
    await reply_to_message(update, context, f"🤖 Thinking about your question...")
    
    try:
        openai_key = context.bot_data.get('openai_key')
        if not openai_key:
            await reply_to_message(update, context, "❌ AI assistant not configured.")
            return
        
        # Send question to OpenAI
        client = openai.AsyncOpenAI(api_key=openai_key)
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful, friendly assistant. Provide clear, concise, and helpful answers. Keep responses under 500 words when possible. Use a conversational tone."
                },
                {
                    "role": "user", 
                    "content": question
                }
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        gpt_answer = response.choices[0].message.content
        
        # Format the response nicely
        response_message = (
            f"🤖 **GPT Response** 🤖\n\n"
            f"❓ **Question from {username}:**\n"
            f"*{question}*\n\n"
            f"💭 **Answer:**\n"
            f"{gpt_answer}"
        )
        
        # Split message if it's too long (Telegram limit is 4096 characters)
        if len(response_message) > 4000:
            # Send question first
            question_msg = (
                f"🤖 **GPT Response** 🤖\n\n"
                f"❓ **Question from {username}:**\n"
                f"*{question}*\n\n"
                f"💭 **Answer:**"
            )
            await reply_to_message(update, context, question_msg, parse_mode='Markdown')
            
            # Send answer in chunks
            chunks = [gpt_answer[i:i+4000] for i in range(0, len(gpt_answer), 4000)]
            for chunk in chunks:
                await reply_to_message(update, context, chunk)
        else:
            await reply_to_message(update, context, response_message, parse_mode='Markdown')
        
        # Log the question for analytics
        logger.info(f"GPT Question from {username} ({update.effective_user.id}): {question[:100]}...")
        
    except Exception as e:
        logger.error(f"GPT API error: {e}")
        await reply_to_message(update, context,
            f"❌ Sorry {username}, I couldn't process your question right now. "
            f"Please try again later.\n\n"
            f"Error: AI service temporarily unavailable"
        )
