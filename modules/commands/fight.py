"""
Turn-Based AI-Powered Fight Arena with Damage System
"""
import asyncio
import random
import time
import openai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.auth.authorization import check_chat_authorization
from modules.database.models import get_user_data, update_user_degencoins, log_transaction, get_user_by_username
from utils.reply_helper import reply_to_message
from utils.user_helper import ensure_user_in_database
from config.logging_config import logger

# Global storage for active fights
ACTIVE_FIGHTS = {}

# Weird weapons and scenarios for AI to use
WEIRD_WEAPONS = [
    "inflatable rubber chicken", "disco ball on a stick", "banana launcher", 
    "rainbow-colored nunchucks", "enchanted spatula", "laser pointer of doom",
    "flying taco", "rubber boot bazooka", "magical cheese grater", "cosmic umbrella",
    "telepathic fish", "bouncing pickle", "antigravity spoon", "flaming yo-yo",
    "ninja rubber duck", "hypnotic pizza slice", "phantom spaghetti whip",
    "holographic battle axe", "singing chainsaw", "frozen waffle launcher", "quantum fork",
    "explosive rubber band", "cybernetic toothbrush", "sentient calculator", "plasma tennis racket",
    "magnetic fishing rod", "radioactive chopsticks", "dimensional scissors", "sonic screwdriver",
    "crystalline boomerang", "electric bagpipe", "molten cheese cannon", "spectral wrench",
    "gravity hammer", "phase shift dagger", "neural whip", "bio-luminescent staff",
    "steam-powered crossbow", "ethereal lasso", "nano-enhanced crowbar", "psionic tuning fork",
    "thermal lance", "void katana", "energy slingshot", "mechanic gauntlets",
    "cursed compass", "solar-powered mace", "temporal brass knuckles", "ionic spear",
    "levitating club", "metamorphic shield", "synthetic bow", "arcane multitool",
    "cryogenic hammer", "photonic blade", "kinetic whip", "atomic yo-yo",
    "digital throwing stars", "gravitational saber", "molecular saw", "plasma net",
    "psychic crowbar", "electromagnetic staff", "quantum entangled rope", "fusion-powered mallet",
    "holographic shield", "bio-mechanical claw", "nano-fiber garrote", "particle beam rifle",
    "spectral chain", "dimensional anchor", "ionic disruptor", "thermal blade",
    "magnetic grappling hook", "neural interface sword", "crystallized lightning bolt", "sonic boom staff"
]

FIGHT_SCENARIOS = [
    "on a floating island made of marshmallows",
    "inside a giant hamster wheel",
    "while riding invisible motorcycles", 
    "in a zero-gravity bubble tea shop",
    "on top of a flying whale",
    "inside a disco-themed volcano",
    "while juggling live chickens",
    "in a rain of colorful jellybeans",
    "on a battlefield of trampolines",
    "inside a magical washing machine",
    "while being chased by dancing penguins",
    "in a library run by ninja librarians"
]

ENVIRONMENTAL_HAZARDS = [
    ("A rogue marshmallow bounces by", 8, 15),
    ("Invisible motorcycle crashes through", 12, 20),
    ("Gravity suddenly reverses", 5, 12),
    ("Giant hamster starts spinning the wheel", 10, 18),
    ("The whale decides to dive", 15, 25),
    ("Lava bubble pops nearby", 8, 16),
    ("Chicken pecks someone's ankles", 3, 8),
    ("Jellybean avalanche cascades down", 6, 14),
    ("Trampoline launches someone into ceiling", 10, 20),
    ("Washing machine enters spin cycle", 12, 22),
    ("Dancing penguin trips someone", 4, 10),
    ("Ninja librarian throws a shuriken book", 9, 17),
    ("Disco ball falls from ceiling", 7, 15),
    ("Portal opens under someone's feet", 5, 35),
    ("Cosmic umbrella opens at wrong time", 8, 18)
]

class Fighter:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.hp = 100
        self.max_hp = 100
        self.weapon = random.choice(WEIRD_WEAPONS)
        self.is_alive = True
        
    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)
        if self.hp <= 0:
            self.is_alive = False
            self.hp = 0

class TurnBasedFight:
    def __init__(self, chat_id, initiator_id, initiator_name, bet_amount, opponent_id=None, opponent_name=None):
        self.chat_id = chat_id
        self.bet_amount = bet_amount
        self.fighters = []
        self.current_turn = 0
        self.turn_number = 1
        self.status = "waiting"  # waiting, fighting, finished
        self.message_id = None
        self.battle_message_id = None  # Track the main battle message for updates
        self.created_at = time.time()
        self.scenario = random.choice(FIGHT_SCENARIOS)
        self.entrance_fee = max(10, bet_amount // 10) if not opponent_id else bet_amount
        self.total_pot = bet_amount
        self.fight_log = []
        self.pre_generated_events = []  # Store all fight events
        self.current_event = 0
        
        # Add fighters
        self.fighters.append(Fighter(initiator_id, initiator_name))
        if opponent_id:
            self.fighters.append(Fighter(opponent_id, opponent_name))
            self.status = "ready"
    
    def add_fighter(self, user_id, username):
        if len(self.fighters) >= 8:  # Max 8 fighters for royale
            return False
        for fighter in self.fighters:
            if fighter.user_id == user_id:
                return False
        
        self.fighters.append(Fighter(user_id, username))
        self.total_pot += self.entrance_fee
        return True
    
    def get_alive_fighters(self):
        return [f for f in self.fighters if f.is_alive]
    
    def get_current_fighter(self):
        alive_fighters = self.get_alive_fighters()
        if not alive_fighters:
            return None
        return alive_fighters[self.current_turn % len(alive_fighters)]
    
    def next_turn(self):
        alive_fighters = self.get_alive_fighters()
        if len(alive_fighters) <= 1:
            return False
        
        self.current_turn = (self.current_turn + 1) % len(alive_fighters)
        if self.current_turn == 0:
            self.turn_number += 1
        return True
    
    def get_winner(self):
        alive_fighters = self.get_alive_fighters()
        return alive_fighters[0] if len(alive_fighters) == 1 else None

async def fight_arena(update, context):
    """Enhanced turn-based fight arena command"""
    if not await check_chat_authorization(update, context):
        return
    
    ensure_user_in_database(update)
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.first_name or update.effective_user.username or f"User {user_id}"
    
    # Check if there's already an active fight in this chat
    if chat_id in ACTIVE_FIGHTS:
        fight = ACTIVE_FIGHTS[chat_id]
        if fight.status in ["waiting", "fighting"]:
            await show_fight_status(update, context, fight)
            return
    
    if not context.args:
        await reply_to_message(update, context,
            "⚔️ **TURN-BASED FIGHT ARENA** ⚔️\n\n"
            "**1v1 Combat:**\n"
            "• `/fight <opponent> <bet_amount>` - Challenge someone\n"
            "• Turn-based combat with damage points\n\n"
            "**Battle Royale:**\n"
            "• `/fight royale <entrance_fee>` - Multi-fighter mayhem\n"
            "• Last fighter standing wins all!\n\n"
            "**Features:**\n"
            "• 🎯 Turn-based tactical combat\n"
            "• 💥 Damage point system (100 HP each)\n"
            "• 🤖 AI-generated weird weapons & scenarios\n"
            "• 💰 Winner takes all degencoins\n\n"
            "**Examples:**\n"
            "• `/fight @HashrateB 50`\n"
            "• `/fight royale 25`",
            parse_mode='Markdown'
        )
        return
    
    if context.args[0].lower() == "royale":
        await start_battle_royale(update, context)
    elif context.args[0].lower() == "join":
        await join_battle_royale(update, context)
    else:
        await start_single_fight(update, context)

async def start_battle_royale(update, context):
    """Start a turn-based battle royale"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.first_name or update.effective_user.username or f"User {user_id}"
    
    if len(context.args) < 2:
        await reply_to_message(update, context, "❌ Usage: `/fight royale <entrance_fee>`")
        return
    
    try:
        entrance_fee = int(context.args[1])
        if entrance_fee < 10:
            await reply_to_message(update, context, "❌ Minimum entrance fee is 10 degencoins.")
            return
        if entrance_fee > 1000:
            await reply_to_message(update, context, "❌ Maximum entrance fee is 1000 degencoins.")
            return
    except ValueError:
        await reply_to_message(update, context, "❌ Please provide a valid entrance fee amount.")
        return
    
    # Check user balance
    user_data = get_user_data(user_id)
    if not user_data or user_data['degencoins'] < entrance_fee:
        await reply_to_message(update, context, f"❌ You need {entrance_fee} degencoins to start this battle royale.")
        return
    
    # Deduct entrance fee
    update_user_degencoins(user_id, user_data['degencoins'] - entrance_fee)
    
    # Create battle royale
    fight = TurnBasedFight(chat_id, user_id, username, entrance_fee)
    ACTIVE_FIGHTS[chat_id] = fight
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Join Battle", callback_data=f"fight_join_{user_id}")],
        [InlineKeyboardButton("🏁 Start Fight", callback_data=f"fight_start_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"fight_cancel_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = await reply_to_message(update, context,
        f"⚔️ **BATTLE ROYALE ARENA** ⚔️\n\n"
        f"🎭 **Scenario:** Fighting {fight.scenario}\n"
        f"🎯 **Initiator:** {username}\n"
        f"🔫 **Weapon:** {fight.fighters[0].weapon}\n"
        f"💰 **Entrance Fee:** {entrance_fee} degencoins\n"
        f"🏆 **Current Pot:** {fight.total_pot} degencoins\n"
        f"👥 **Fighters:** {len(fight.fighters)}/8\n\n"
        f"💡 Others click 'Join Battle' to enter!\n"
        f"⏰ **Auto-start in 60 seconds**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    fight.message_id = message.message_id
    
    # Auto-start after 60 seconds
    await asyncio.sleep(60)
    if chat_id in ACTIVE_FIGHTS and ACTIVE_FIGHTS[chat_id].status == "waiting":
        await start_turn_based_battle(update, context, ACTIVE_FIGHTS[chat_id])

async def start_single_fight(update, context):
    """Start a turn-based 1v1 fight"""
    if len(context.args) < 2:
        await reply_to_message(update, context, "❌ Usage: `/fight <opponent> <bet_amount>`")
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.first_name or update.effective_user.username or f"User {user_id}"
    opponent_mention = context.args[0]
    
    try:
        bet_amount = int(context.args[1])
        if bet_amount < 10:
            await reply_to_message(update, context, "❌ Minimum bet is 10 degencoins.")
            return
        if bet_amount > 1000:
            await reply_to_message(update, context, "❌ Maximum bet is 1000 degencoins.")
            return
    except ValueError:
        await reply_to_message(update, context, "❌ Please provide a valid bet amount.")
        return
    
    # Check user balance
    user_data = get_user_data(user_id)
    if not user_data or user_data['degencoins'] < bet_amount:
        await reply_to_message(update, context, f"❌ You need {bet_amount} degencoins to place this bet.")
        return
    
    # Find opponent
    opponent_username = opponent_mention.replace('@', '')
    opponent_data = get_user_by_username(opponent_username)
    
    if not opponent_data:
        await reply_to_message(update, context, f"❌ User {opponent_mention} not found. They need to interact with the bot first.")
        return
    
    if opponent_data['user_id'] == user_id:
        await reply_to_message(update, context, "❌ You can't fight yourself! Try `/fight royale` instead.")
        return
    
    # Check opponent balance
    if opponent_data['degencoins'] < bet_amount:
        await reply_to_message(update, context, f"❌ {opponent_mention} doesn't have enough degencoins for this bet.")
        return
    
    # Deduct bets from both players
    update_user_degencoins(user_id, user_data['degencoins'] - bet_amount)
    update_user_degencoins(opponent_data['user_id'], opponent_data['degencoins'] - bet_amount)
    
    # Create and start turn-based fight
    opponent_name = opponent_data.get('first_name') or opponent_data.get('username') or f"User {opponent_data['user_id']}"
    chat_id = update.effective_chat.id
    
    fight = TurnBasedFight(chat_id, user_id, username, bet_amount * 2, opponent_data['user_id'], opponent_name)
    ACTIVE_FIGHTS[chat_id] = fight
    
    await start_turn_based_battle(update, context, fight)

async def start_turn_based_battle(update, context, fight):
    """Start the turn-based combat system"""
    if len(fight.fighters) < 2:
        # Refund if not enough fighters
        for fighter in fight.fighters:
            user_data = get_user_data(fighter.user_id)
            refund = fight.entrance_fee if len(fight.fighters) > 2 else fight.bet_amount // 2
            update_user_degencoins(fighter.user_id, user_data['degencoins'] + refund)
        
        await reply_to_message(update, context,
            "❌ **Battle Cancelled**\n\n"
            "Not enough participants. All fees refunded.",
            parse_mode='Markdown'
        )
        del ACTIVE_FIGHTS[fight.chat_id]
        return
    
    fight.status = "fighting"
    
    # Pre-generate entire fight sequence (silently)
    await pre_generate_fight(update, context, fight)
    
    # Show opening and play with realistic delays
    await show_fight_opening(update, context, fight)
    
    # Play the pre-generated fight with engaging timing
    await play_fight_sequence(update, context, fight)

async def generate_fight_opening(update, context, fight):
    """Generate AI opening scene for the fight"""
    openai_key = context.bot_data.get('openai_key')
    if not openai_key:
        await reply_to_message(update, context, "❌ AI fight system not configured.")
        return
    
    try:
        client = openai.AsyncOpenAI(api_key=openai_key)
        
        fighter_intros = []
        for fighter in fight.fighters:
            fighter_intros.append(f"{fighter.name} wielding {fighter.weapon}")
        
        prompt = f"""Create a SHORT (max 2 sentences) epic opening scene for a turn-based battle {fight.scenario}.
        
        Fighters: {', '.join(fighter_intros)}
        
        Make it funny, absurd, and gruesome like an anime tournament announcement. End with "THE BATTLE BEGINS!"
        
        Example: "The fighters assemble {fight.scenario}, weapons gleaming ominously in the twisted light! THE BATTLE BEGINS!"
        """
        
        response = await client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.9,
            max_tokens=200
        )
        
        opening_scene = response.choices[0].message.content.strip()
        
        # Create HP display
        hp_display = "\n".join([f"🔥 **{f.name}:** {f.hp}/100 HP" for f in fight.fighters])
        
        await reply_to_message(update, context,
            f"⚔️ **BATTLE COMMENCES** ⚔️\n\n"
            f"{opening_scene}\n\n"
            f"**Fighter Status:**\n{hp_display}\n\n"
            f"🎯 **Turn 1 starting...**",
            parse_mode='Markdown'
        )
        
        # Wait a moment for dramatic effect
        await asyncio.sleep(3)
        
    except Exception as e:
        logger.error(f"AI opening scene error: {e}")

async def process_turn(update, context, fight):
    """Process a single turn of combat"""
    if fight.status != "fighting":
        return
    
    alive_fighters = fight.get_alive_fighters()
    if len(alive_fighters) <= 1:
        await end_battle(update, context, fight)
        return
    
    current_fighter = fight.get_current_fighter()
    if not current_fighter:
        await end_battle(update, context, fight)
        return
    
    # Check for environmental hazards (15% chance with 3+ fighters)
    if len(alive_fighters) >= 3 and random.random() < 0.15:
        await generate_environmental_hazard(update, context, fight)
        
        # Check if battle should end after hazard
        if len(fight.get_alive_fighters()) <= 1:
            await end_battle(update, context, fight)
            return
    
    # Generate AI turn action
    await generate_turn_action(update, context, fight, current_fighter)
    
    # Check if battle should end
    if len(fight.get_alive_fighters()) <= 1:
        await end_battle(update, context, fight)
        return
    
    # Move to next turn
    fight.next_turn()
    
    # Continue battle after short delay
    await asyncio.sleep(4)
    await process_turn(update, context, fight)

async def generate_turn_action(update, context, fight, attacker):
    """Generate AI turn action with damage calculation"""
    openai_key = context.bot_data.get('openai_key')
    if not openai_key:
        return
    
    try:
        client = openai.AsyncOpenAI(api_key=openai_key)
        
        # Select random target
        possible_targets = [f for f in fight.get_alive_fighters() if f.user_id != attacker.user_id]
        if not possible_targets:
            return
        
        target = random.choice(possible_targets)
        
        # Calculate damage (15-35 points, with crits)
        base_damage = random.randint(15, 35)
        is_crit = random.random() < 0.15  # 15% crit chance
        damage = int(base_damage * 1.8) if is_crit else base_damage
        
        # Generate attack description
        prompt = f"""Create a SHORT (max 2 sentences) attack description for a turn-based fight.
        
        Attacker: {attacker.name} using {attacker.weapon}
        Target: {target.name}
        Damage: {damage} points
        Critical Hit: {is_crit}
        Setting: {fight.scenario}
        
        Make it absurdly funny and gruesome. {"CRITICAL HIT!" if is_crit else "Regular attack"}
        
        Example: "John swings his inflatable rubber chicken, bonking Mike's skull for 25 damage! Mike's eyes roll back as he staggers."
        """
        
        response = await client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.95,
            max_tokens=150
        )
        
        action_text = response.choices[0].message.content.strip()
        
        # Apply damage
        target.take_damage(damage)
        
        # Create status display
        hp_display = "\n".join([
            f"{'💀' if not f.is_alive else '🔥'} **{f.name}:** {f.hp}/100 HP {'(DEFEATED!)' if not f.is_alive else ''}"
            for f in fight.fighters
        ])
        
        crit_text = "\n💥 **CRITICAL HIT!**" if is_crit else ""
        defeat_text = f"\n\n⚰️ **{target.name} has been defeated!**" if not target.is_alive else ""
        
        await reply_to_message(update, context,
            f"🎯 **Turn {fight.turn_number}** - {attacker.name}'s Attack\n\n"
            f"{action_text}{crit_text}\n\n"
            f"📊 **Damage Dealt:** {damage} points{defeat_text}\n\n"
            f"**Current Status:**\n{hp_display}",
            parse_mode='Markdown'
        )
        
        fight.fight_log.append(f"Turn {fight.turn_number}: {attacker.name} → {target.name} ({damage} dmg)")
        
    except Exception as e:
        logger.error(f"AI turn action error: {e}")

async def pre_generate_fight(update, context, fight):
    """Pre-generate entire fight sequence to save AI costs"""
    openai_key = context.bot_data.get('openai_key')
    if not openai_key:
        # Fallback to predefined messages if no AI
        fight.pre_generated_events = generate_fallback_fight(fight)
        return
    
    try:
        client = openai.AsyncOpenAI(api_key=openai_key)
        
        # Create fighter simulation with copies
        sim_fighters = []
        for f in fight.fighters:
            sim_fighter = Fighter(f.user_id, f.name)
            sim_fighter.weapon = f.weapon
            sim_fighters.append(sim_fighter)
        
        events = []
        turn = 1
        current_turn = 0
        
        # Generate opening scene
        fighter_intros = [f"{f.name} with {f.weapon}" for f in sim_fighters]
        opening_prompt = f"""Create a SHORT (1 sentence) battle opening for fighters {fight.scenario}.
        
        Fighters: {', '.join(fighter_intros)}
        
        Keep it brief and action-focused. End with "Battle begins!"
        """
        
        response = await client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': opening_prompt}],
            temperature=0.9,
            max_tokens=200
        )
        
        events.append({
            'type': 'opening',
            'text': response.choices[0].message.content.strip()
        })
        
        # Simulate the entire fight
        while len([f for f in sim_fighters if f.is_alive]) > 1:
            alive_fighters = [f for f in sim_fighters if f.is_alive]
            
            # Environmental hazard check (15% chance with 3+ fighters)
            if len(alive_fighters) >= 3 and random.random() < 0.15:
                hazard_text, min_dmg, max_dmg = random.choice(ENVIRONMENTAL_HAZARDS)
                num_affected = min(random.randint(1, 3), len(alive_fighters))
                affected_fighters = random.sample(alive_fighters, num_affected)
                
                casualties = []
                damage_reports = []
                
                for fighter in affected_fighters:
                    damage = random.randint(min_dmg, max_dmg)
                    fighter.take_damage(damage)
                    
                    if not fighter.is_alive:
                        casualties.append(f"💀 {fighter.name} dies horribly!")
                    else:
                        damage_reports.append(f"💥 {fighter.name} (-{damage} HP)")
                
                events.append({
                    'type': 'hazard',
                    'text': hazard_text,
                    'damage_reports': damage_reports,
                    'casualties': casualties,
                    'hp_states': [(f.name, f.hp, f.is_alive) for f in sim_fighters]
                })
                
                # Check if fight should end
                if len([f for f in sim_fighters if f.is_alive]) <= 1:
                    break
            
            # Regular attack turn
            attacker = alive_fighters[current_turn % len(alive_fighters)]
            possible_targets = [f for f in alive_fighters if f.user_id != attacker.user_id]
            
            if possible_targets:
                target = random.choice(possible_targets)
                
                # Calculate damage
                base_damage = random.randint(15, 35)
                is_crit = random.random() < 0.15
                damage = int(base_damage * 1.8) if is_crit else base_damage
                
                # Generate attack description
                attack_prompt = f"""Create a SHORT (1 sentence) attack for turn-based combat.
                
                {attacker.name} attacks {target.name} with {attacker.weapon} for {damage} damage.
                {"Critical hit!" if is_crit else "Normal attack"}
                
                Be concise and action-focused.
                """
                
                response = await client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{'role': 'user', 'content': attack_prompt}],
                    temperature=0.95,
                    max_tokens=150
                )
                
                # Apply damage
                target.take_damage(damage)
                
                events.append({
                    'type': 'attack',
                    'attacker': attacker.name,
                    'target': target.name,
                    'damage': damage,
                    'is_crit': is_crit,
                    'text': response.choices[0].message.content.strip(),
                    'target_defeated': not target.is_alive,
                    'hp_states': [(f.name, f.hp, f.is_alive) for f in sim_fighters],
                    'turn': turn
                })
            
            current_turn = (current_turn + 1) % len(alive_fighters)
            if current_turn == 0:
                turn += 1
        
        # Generate victory scene
        winner = next((f for f in sim_fighters if f.is_alive), None)
        if winner:
            defeated_fighters = [f.name for f in sim_fighters if not f.is_alive]
            
            victory_prompt = f"""Create a SHORT (1 sentence) victory message.
            
            {winner.name} wins with {winner.weapon}, defeating {len(defeated_fighters)} fighters.
            Prize: {fight.total_pot} degencoins
            
            Be brief and celebratory.
            """
            
            response = await client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': victory_prompt}],
                temperature=0.9,
                max_tokens=180
            )
            
            events.append({
                'type': 'victory',
                'winner': winner.name,
                'winner_id': winner.user_id,
                'text': response.choices[0].message.content.strip()
            })
        
        fight.pre_generated_events = events
        
    except Exception as e:
        logger.error(f"Fight pre-generation error: {e}")
        fight.pre_generated_events = generate_fallback_fight(fight)

def generate_fallback_fight(fight):
    """Generate basic fight without AI if needed"""
    events = []
    
    # Simple opening
    events.append({
        'type': 'opening',
        'text': f"The fighters assemble {fight.scenario}, weapons ready! THE BATTLE BEGINS!"
    })
    
    # Basic combat simulation
    sim_fighters = []
    for f in fight.fighters:
        sim_fighter = Fighter(f.user_id, f.name)
        sim_fighter.weapon = f.weapon
        sim_fighters.append(sim_fighter)
    
    turn = 1
    current_turn = 0
    
    while len([f for f in sim_fighters if f.is_alive]) > 1:
        alive_fighters = [f for f in sim_fighters if f.is_alive]
        attacker = alive_fighters[current_turn % len(alive_fighters)]
        possible_targets = [f for f in alive_fighters if f.user_id != attacker.user_id]
        
        if possible_targets:
            target = random.choice(possible_targets)
            damage = random.randint(15, 35)
            is_crit = random.random() < 0.15
            if is_crit:
                damage = int(damage * 1.8)
            
            target.take_damage(damage)
            
            attack_texts = [
                f"{attacker.name} hits {target.name} with {attacker.weapon} ({damage} dmg)",
                f"{attacker.name} strikes {target.name} using {attacker.weapon} ({damage} dmg)",
                f"{target.name} takes {damage} damage from {attacker.name}'s {attacker.weapon}"
            ]
            
            events.append({
                'type': 'attack',
                'attacker': attacker.name,
                'target': target.name,
                'damage': damage,
                'is_crit': is_crit,
                'text': random.choice(attack_texts),
                'target_defeated': not target.is_alive,
                'hp_states': [(f.name, f.hp, f.is_alive) for f in sim_fighters],
                'turn': turn
            })
        
        current_turn = (current_turn + 1) % len(alive_fighters)
        if current_turn == 0:
            turn += 1
    
    # Victory
    winner = next((f for f in sim_fighters if f.is_alive), None)
    if winner:
        events.append({
            'type': 'victory',
            'winner': winner.name,
            'winner_id': winner.user_id,
            'text': f"{winner.name} wins with {winner.weapon}!"
        })
    
    return events

async def show_fight_opening(update, context, fight):
    """Show the opening scene and track message for updates"""
    opening_event = fight.pre_generated_events[0] if fight.pre_generated_events else None
    if not opening_event:
        return
    
    hp_display = "\n".join([f"🔥 {f.name}: {f.hp}/100 HP" for f in fight.fighters])
    
    message = await reply_to_message(update, context,
        f"⚔️ **BATTLE** - **STARTING** ⚔️\n\n"
        f"**OPENING:**\n_{opening_event['text']}_\n\n"
        f"**FIGHTER STATUS:**\n{hp_display}\n\n"
        f"_**Turn 1** starting..._",
        parse_mode='Markdown'
    )
    
    fight.battle_message_id = message.message_id
    fight.current_event = 1

async def play_fight_sequence(update, context, fight):
    """Play the pre-generated fight by updating the same message"""
    await asyncio.sleep(3)  # Opening pause
    
    battle_log = []
    current_hp = {f.name: f.hp for f in fight.fighters}
    
    while fight.current_event < len(fight.pre_generated_events):
        event = fight.pre_generated_events[fight.current_event]
        
        if event['type'] == 'hazard':
            damage_text = " | ".join(event['damage_reports']) if event['damage_reports'] else "**Everyone dodges**"
            battle_log.append(f"⚠️ **HAZARD:** {event['text']} - {damage_text}")
            
            # Update HP from event
            for name, hp, alive in event['hp_states']:
                current_hp[name] = hp
            
        elif event['type'] == 'attack':
            crit_marker = " 💥**CRITICAL HIT**" if event['is_crit'] else ""
            defeat_marker = " 💀**KNOCKOUT**" if event['target_defeated'] else ""
            battle_log.append(f"⚔️ **TURN {event['turn']}:** {event['text']}{crit_marker}{defeat_marker}")
            
            # Update HP from event
            for name, hp, alive in event['hp_states']:
                current_hp[name] = hp
            
        elif event['type'] == 'victory':
            await end_pre_generated_battle(update, context, fight, event, battle_log)
            return
        
        # Update the main battle message
        await update_battle_message(update, context, fight, battle_log, current_hp)
        
        fight.current_event += 1
        await asyncio.sleep(4)  # Slower, more engaging timing

async def update_battle_message(update, context, fight, battle_log, current_hp):
    """Update the main battle message with current state"""
    if not fight.battle_message_id:
        return
    
    hp_display = "\n".join([
        f"{'💀' if current_hp[f.name] <= 0 else '🔥'} **{f.name}:** `{current_hp[f.name]}/100 HP`"
        for f in fight.fighters
    ])
    
    # Keep only last 6 log entries to avoid message length issues
    recent_log = battle_log[-6:] if len(battle_log) > 6 else battle_log
    log_text = "\n".join(recent_log) if recent_log else "_Battle starting..._"
    
    # Get current turn number from latest event
    current_turn = "**STARTING**"
    if battle_log:
        for entry in reversed(recent_log):
            if "TURN" in entry:
                turn_match = entry.split("TURN ")[1].split(":")[0] if "TURN " in entry else None
                if turn_match:
                    current_turn = f"**TURN {turn_match}**"
                    break
    
    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=fight.battle_message_id,
            text=f"⚔️ **BATTLE** - {current_turn} ⚔️\n\n"
                 f"**RECENT ACTIONS:**\n{log_text}\n\n"
                 f"**FIGHTER STATUS:**\n{hp_display}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.warning(f"Failed to update battle message: {e}")

async def end_pre_generated_battle(update, context, fight, victory_event, battle_log):
    """End the battle using pre-generated victory"""
    winner_id = victory_event['winner_id']
    winner_name = victory_event['winner']
    
    # Award prize to winner
    winner_data = get_user_data(winner_id)
    old_balance = winner_data['degencoins']
    new_balance = old_balance + fight.total_pot
    update_user_degencoins(winner_id, new_balance)
    
    # Log transaction
    log_transaction(
        fight.fighters[0].user_id,
        winner_id,
        fight.total_pot,
        'battle_victory',
        f"Victory in {len(fight.fighters)}-fighter battle"
    )
    
    # Final update to battle message
    if fight.battle_message_id:
        try:
            # Get final turn count
            final_turn = "**UNKNOWN**"
            if battle_log:
                for entry in reversed(battle_log):
                    if "TURN" in entry:
                        turn_match = entry.split("TURN ")[1].split(":")[0] if "TURN " in entry else None
                        if turn_match:
                            final_turn = f"**TURN {turn_match}**"
                            break
            
            # Keep recent actions for final display
            recent_log = battle_log[-4:] if len(battle_log) > 4 else battle_log
            log_text = "\n".join(recent_log) if recent_log else "_No actions recorded_"
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=fight.battle_message_id,
                text=f"🏆 **BATTLE COMPLETE** - {final_turn} 🏆\n\n"
                     f"**FINAL ACTIONS:**\n{log_text}\n\n"
                     f"**VICTORY:**\n_{victory_event['text']}_\n\n"
                     f"👑 **CHAMPION:** **{winner_name}**\n"
                     f"💰 **PRIZE WON:** `{fight.total_pot}` **degencoins**\n"
                     f"💳 **BALANCE:** `{old_balance:,}` → `{new_balance:,}` **coins**",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Failed to update final battle message: {e}")
    
    del ACTIVE_FIGHTS[fight.chat_id]

async def end_battle(update, context, fight):
    """End the battle and award prizes"""
    winner = fight.get_winner()
    fight.status = "finished"
    
    if not winner:
        # Shouldn't happen, but handle gracefully
        await reply_to_message(update, context, "⚔️ **Battle ended in a draw!** All fighters defeated simultaneously.")
        del ACTIVE_FIGHTS[fight.chat_id]
        return
    
    # Award prize to winner
    winner_data = get_user_data(winner.user_id)
    old_balance = winner_data['degencoins']
    new_balance = old_balance + fight.total_pot
    update_user_degencoins(winner.user_id, new_balance)
    
    # Log transaction
    log_transaction(
        fight.fighters[0].user_id,  # From initiator
        winner.user_id,
        fight.total_pot,
        'battle_victory',
        f"Victory in {len(fight.fighters)}-fighter battle"
    )
    
    # Generate victory scene
    openai_key = context.bot_data.get('openai_key')
    victory_scene = f"{winner.name} stands victorious with their {winner.weapon}!"
    
    if openai_key:
        try:
            client = openai.AsyncOpenAI(api_key=openai_key)
            
            defeated_fighters = [f.name for f in fight.fighters if not f.is_alive]
            
            prompt = f"""Create a SHORT (max 2 sentences) epic victory scene.
            
            Winner: {winner.name} with {winner.weapon}
            Defeated: {', '.join(defeated_fighters)}
            Setting: {fight.scenario}
            Prize: {fight.total_pot} degencoins
            
            Make it funny, over-the-top, gruesome and celebratory!
            
            Example: "{winner.name} stands triumphant as {winner.weapon} drips with victory! The defeated lie scattered like broken dolls across the battlefield!"
            """
            
            response = await client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.9,
                max_tokens=180
            )
            
            victory_scene = response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"AI victory scene error: {e}")
    
    # Final results message
    await reply_to_message(update, context,
        f"🏆 **BATTLE COMPLETE** 🏆\n\n"
        f"{victory_scene}\n\n"
        f"👑 **CHAMPION:** {winner.name}\n"
        f"💰 **Prize Won:** {fight.total_pot} degencoins\n"
        f"👥 **Defeated:** {len(fight.fighters) - 1} fighters\n"
        f"🎯 **Turns Survived:** {fight.turn_number}\n\n"
        f"💳 **Transaction:**\n"
        f"   Previous Balance: {old_balance:,} coins\n"
        f"   Prize Amount: +{fight.total_pot:,} coins\n"
        f"   **New Balance: {new_balance:,} coins**\n\n"
        f"🎊 Legendary victory for {winner.name}!",
        parse_mode='Markdown'
    )
    
    del ACTIVE_FIGHTS[fight.chat_id]

async def show_fight_status(update, context, fight):
    """Show current fight status"""
    if fight.status == "fighting":
        # Show current battle status
        alive_fighters = fight.get_alive_fighters()
        current_fighter = fight.get_current_fighter()
        
        hp_display = "\n".join([
            f"{'💀' if not f.is_alive else '🔥'} **{f.name}:** {f.hp}/100 HP"
            for f in fight.fighters
        ])
        
        await reply_to_message(update, context,
            f"⚔️ **ONGOING BATTLE** ⚔️\n\n"
            f"🎭 **Scenario:** {fight.scenario}\n"
            f"🎯 **Turn {fight.turn_number}** - {current_fighter.name if current_fighter else 'Unknown'}'s turn\n"
            f"💰 **Prize Pool:** {fight.total_pot} degencoins\n\n"
            f"**Fighter Status:**\n{hp_display}\n\n"
            f"⚡ Battle in progress...",
            parse_mode='Markdown'
        )
    else:
        # Show waiting room
        fighter_list = "\n".join([f"• {f.name} - {f.weapon}" for f in fight.fighters])
        
        keyboard = [
            [InlineKeyboardButton("⚔️ Join Battle", callback_data=f"fight_join_{fight.fighters[0].user_id}")],
            [InlineKeyboardButton("🏁 Start Fight", callback_data=f"fight_start_{fight.fighters[0].user_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"fight_cancel_{fight.fighters[0].user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await reply_to_message(update, context,
            f"⚔️ **BATTLE ROYALE LOBBY** ⚔️\n\n"
            f"🎭 **Scenario:** {fight.scenario}\n"
            f"💰 **Entrance Fee:** {fight.entrance_fee} degencoins\n"
            f"🏆 **Current Pot:** {fight.total_pot} degencoins\n"
            f"👥 **Fighters ({len(fight.fighters)}/8):**\n{fighter_list}\n\n"
            f"💡 Click 'Join Battle' to enter!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Callback handlers remain the same but updated for new fight structure
async def handle_fight_callback(update, context):
    """Handle fight-related button callbacks"""
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Callback query answer failed (likely timeout): {e}")
        # Continue processing anyway
    
    data = query.data
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.first_name or update.effective_user.username or f"User {user_id}"
    
    if chat_id not in ACTIVE_FIGHTS:
        await query.edit_message_text("❌ Fight no longer active.")
        return
    
    fight = ACTIVE_FIGHTS[chat_id]
    
    if data.startswith("fight_join_"):
        if any(f.user_id == user_id for f in fight.fighters):
            await query.answer("❌ You're already in this battle!", show_alert=True)
            return
        
        if len(fight.fighters) >= 8:
            await query.answer("❌ Battle is full (8 fighters max)!", show_alert=True)
            return
        
        # Check user balance
        user_data = get_user_data(user_id)
        if not user_data or user_data['degencoins'] < fight.entrance_fee:
            await query.answer(f"❌ You need {fight.entrance_fee} degencoins to join!", show_alert=True)
            return
        
        # Deduct entrance fee and add to fight
        update_user_degencoins(user_id, user_data['degencoins'] - fight.entrance_fee)
        fight.add_fighter(user_id, username)
        
        # Update message
        fighter_list = "\n".join([f"• {f.name} - {f.weapon}" for f in fight.fighters])
        
        keyboard = [
            [InlineKeyboardButton("⚔️ Join Battle", callback_data=f"fight_join_{fight.fighters[0].user_id}")],
            [InlineKeyboardButton("🏁 Start Fight", callback_data=f"fight_start_{fight.fighters[0].user_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"fight_cancel_{fight.fighters[0].user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚔️ **BATTLE ROYALE LOBBY** ⚔️\n\n"
            f"🎭 **Scenario:** {fight.scenario}\n"
            f"💰 **Entrance Fee:** {fight.entrance_fee} degencoins\n"
            f"🏆 **Current Pot:** {fight.total_pot} degencoins\n"
            f"👥 **Fighters ({len(fight.fighters)}/8):**\n{fighter_list}\n\n"
            f"✅ {username} joined with {fight.fighters[-1].weapon}!\n"
            f"💡 More can join or start the fight now!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    elif data.startswith("fight_start_"):
        if len(fight.fighters) < 2:
            await query.answer("❌ Need at least 2 fighters to start!", show_alert=True)
            return
        
        await query.edit_message_text(
            f"⚔️ **BATTLE BEGINNING** ⚔️\n\n"
            f"🥊 {len(fight.fighters)} fighters ready!\n"
            f"💰 Prize pool: {fight.total_pot} degencoins\n\n"
            f"🎭 **Generating epic turn-based battle...**",
            parse_mode='Markdown'
        )
        
        # Start the turn-based battle
        await start_turn_based_battle(update, context, fight)
        
    elif data.startswith("fight_cancel_"):
        if user_id != fight.fighters[0].user_id:
            await query.answer("❌ Only the fight initiator can cancel!", show_alert=True)
            return
        
        # Refund all participants
        for fighter in fight.fighters:
            user_data = get_user_data(fighter.user_id)
            refund_amount = fight.entrance_fee
            update_user_degencoins(fighter.user_id, user_data['degencoins'] + refund_amount)
        
        await query.edit_message_text(
            f"❌ **Battle Cancelled**\n\n"
            f"All entrance fees have been refunded to participants.",
            parse_mode='Markdown'
        )
        
        del ACTIVE_FIGHTS[chat_id]