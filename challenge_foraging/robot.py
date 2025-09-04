ForageBot.reset_days(limit=5000)

import numpy as np
from forage_bot import ForageBot, Tree, BerryBush

# Set random seed for reproducibility
np.random.seed(69)
forageBot = ForageBot()

print("=== FORAGEBOT PROFIT MAXIMIZATION STRATEGY ===")
print(f"Starting on day {forageBot.what_day_is_it()}")
print(f"Goal: Maximize profit in 5000 days")
print()

# Price analysis from the code:
# apple_prices = [1, 4, 4, 1, 1, 1, 1]  # Mon, Tue, Wed, Thu, Fri, Sat, Sun
# berry_prices = [3, 3, 3, 3, 3, 5, 5]  # Mon, Tue, Wed, Thu, Fri, Sat, Sun

def get_expected_profit_per_day(candidate, sample_amount, fruit_type):
    """Calculate expected profit per day for a candidate"""
    if fruit_type == 'berries':
        # Berries: 3€ weekdays, 5€ weekends
        # Rain reduces yield by 50%
        rain_prob = 0.4
        normal_yield = sample_amount
        rain_yield = sample_amount * 0.5  # approximate from rain effect
        
        avg_yield = (1 - rain_prob) * normal_yield + rain_prob * rain_yield
        
        # Price: 5 days at 3€, 2 days at 5€
        avg_price = (5 * 3 + 2 * 5) / 7
        expected_profit = avg_yield * avg_price
        
    else:  # apples
        # Apples: 1€ most days, 4€ on Tue/Wed
        avg_yield = sample_amount  # No rain effect
        avg_price = (5 * 1 + 2 * 4) / 7  # 5 days at 1€, 2 days at 4€
        expected_profit = avg_yield * avg_price
    
    return expected_profit, avg_yield

def find_best_source(exploration_budget=100):
    """Find the best foraging source with proper sampling"""
    print(f"=== EXPLORATION PHASE (Budget: {exploration_budget} days) ===")
    
    best_candidate = None
    best_profit_per_day = 0
    best_info = None
    candidates_tested = []
    
    days_used = 0
    
    while days_used < exploration_budget and forageBot.what_day_is_it() < 5000:
        # Explore new candidate
        candidate = forageBot.explore()
        days_used += 1
        current_day = forageBot.what_day_is_it()
        
        if days_used >= exploration_budget:
            print(f"Day {current_day}: Exploration budget exhausted")
            break
            
        # Sample the candidate multiple times for better estimate
        samples = []
        sample_days = min(5, exploration_budget - days_used)  # Take up to 5 samples
        
        for i in range(sample_days):
            if forageBot.what_day_is_it() >= 5000:
                break
                
            fruit_type, amount = candidate.forage()
            # Note: we can't actually forage without using the bot's method
            # So let's use bot's forage method
            amount = forageBot.forage(candidate, verbose=False)
            days_used += 1
            samples.append(amount)
            
        if not samples:
            continue
            
        avg_sample = np.mean(samples)
        candidate_type = type(candidate).__name__
        fruit_type = 'berries' if candidate_type == 'BerryBush' else 'apples'
        
        expected_profit, avg_yield = get_expected_profit_per_day(candidate, avg_sample, fruit_type)
        
        candidates_tested.append({
            'candidate': candidate,
            'type': candidate_type,
            'fruit_type': fruit_type,
            'samples': samples,
            'avg_yield': avg_yield,
            'expected_profit': expected_profit
        })
        
        print(f"Day {forageBot.what_day_is_it()}: Tested {candidate_type}")
        print(f"    Samples: {[f'{s:.2f}' for s in samples]} kg")
        print(f"    Average yield: {avg_yield:.2f} kg/day")
        print(f"    Expected profit: {expected_profit:.2f} €/day")
        
        if expected_profit > best_profit_per_day:
            best_profit_per_day = expected_profit
            best_candidate = candidate
            best_info = candidates_tested[-1]
            print(f"    *** NEW BEST CANDIDATE! Expected profit: {expected_profit:.2f} €/day ***")
        
        print()
    
    print(f"=== EXPLORATION COMPLETE ===")
    print(f"Days used for exploration: {days_used}")
    print(f"Candidates tested: {len(candidates_tested)}")
    
    if best_candidate:
        print(f"Best candidate: {best_info['type']} producing {best_info['fruit_type']}")
        print(f"Expected yield: {best_info['avg_yield']:.2f} kg/day")
        print(f"Expected profit: {best_profit_per_day:.2f} €/day")
        print(f"Projected total profit: {best_profit_per_day * (5000 - forageBot.what_day_is_it()):.2f} €")
    
    print()
    return best_candidate, best_info

def optimal_selling_strategy(fruit_type):
    """Determine optimal selling days based on fruit type"""
    if fruit_type == 'berries':
        # Berries: sell on weekends (Sat/Sun = days 5,6) for 5€ instead of 3€
        return [5, 6]  # Saturday, Sunday
    else:
        # Apples: sell on Tue/Wed (days 1,2) for 4€ instead of 1€
        return [1, 2]  # Tuesday, Wednesday

def should_sell_today(current_day, fruit_type, bot_inventory):
    """Decide whether to sell today based on prices and spoilage"""
    weekday = current_day % 7
    optimal_days = optimal_selling_strategy(fruit_type)
    
    if not bot_inventory:
        return False, "empty_inventory"
    
    # Sell if it's an optimal price day
    if weekday in optimal_days:
        return True, "optimal_price"
    
    # Get the minimum days left from bot's inventory (format: (fruit, amount, days_left))
    min_days_left = min(item[2] for item in bot_inventory)
    
    # Sell if anything will spoil tomorrow or today
    if min_days_left <= 1:
        return True, "spoilage_risk"
    
    # If we have inventory that's 2 days old and tomorrow isn't optimal, sell today
    if min_days_left <= 2 and (current_day + 1) % 7 not in optimal_days:
        return True, "preemptive_spoilage"
    
    return False, "hold"

def exploit_best_source(candidate, source_info):
    """Exploit the best source with optimal timing"""
    print(f"=== EXPLOITATION PHASE ===")
    print(f"Starting day: {forageBot.what_day_is_it()}")
    print(f"Remaining days: {5000 - forageBot.what_day_is_it()}")
    print(f"Source: {source_info['type']} producing {source_info['fruit_type']}")
    print()
    
    total_foraged = 0
    total_sold = 0
    sell_counts = {'optimal_price': 0, 'spoilage_risk': 0, 'preemptive_spoilage': 0, 'empty_inventory': 0}
    
    while forageBot.what_day_is_it() < 5000:
        current_day = forageBot.what_day_is_it()
        weekday = current_day % 7
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        is_raining = forageBot.is_it_raining()
        
        # Forage from our best source
        amount = forageBot.forage(candidate, verbose=False)
        total_foraged += amount
        
        # Get current inventory from the bot
        current_inventory = forageBot.inventory
        
        # Decide whether to sell
        should_sell, reason = should_sell_today(current_day, source_info['fruit_type'], current_inventory)
        
        daily_info = f"Day {current_day} ({weekday_names[weekday]}): Foraged {amount:.2f} kg"
        if is_raining and source_info['fruit_type'] == 'berries':
            daily_info += " (RAIN)"
        
        if should_sell and current_inventory:
            money_earned = forageBot.sell(verbose=False)
            items_sold = len(current_inventory)
            kg_sold = sum(item[1] for item in current_inventory)
            total_sold += kg_sold
            
            sell_counts[reason] += 1
            
            print(f"{daily_info} | SOLD {items_sold} items ({kg_sold:.2f} kg) for €{money_earned:.2f} ({reason}) | Total: €{ForageBot.earnings:.2f}")
        else:
            inventory_size = len(current_inventory)
            inventory_kg = sum(item[1] for item in current_inventory) if current_inventory else 0
            min_age = min(item[2] for item in current_inventory) if current_inventory else 0
            print(f"{daily_info} | Inventory: {inventory_size} items ({inventory_kg:.2f} kg, min age: {min_age}) | Total: €{ForageBot.earnings:.2f}")
    
    # Final sale
    if forageBot.inventory:
        final_money = forageBot.sell(verbose=False)
        print(f"Final sale: €{final_money:.2f}")
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Total earned: €{ForageBot.earnings:.2f}")
    print(f"Total foraged: {total_foraged:.2f} kg")
    print(f"Total sold: {total_sold:.2f} kg")
    print(f"Sell reasons: {sell_counts}")
    print(f"Average profit per day: €{ForageBot.earnings/5000:.2f}")
    
    return ForageBot.earnings

# Execute the strategy
print("Starting optimization strategy...")
print()

# Phase 1: Find the best source
best_source, source_info = find_best_source(exploration_budget=200)

if best_source is None:
    print("ERROR: No viable source found!")
else:
    # Phase 2: Exploit the best source
    final_profit = exploit_best_source(best_source, source_info)
    
    print(f"\n{'='*50}")
    print(f"FINAL PROFIT: €{final_profit:.2f}")
    print(f"TARGET: €100,000.00")
    print(f"SUCCESS: {'YES' if final_profit >= 100000 else 'NO'}")
    print(f"{'='*50}")