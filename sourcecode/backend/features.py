# Behavioural feature engineering
# Transforms raw transactions into a behavioural fingerprint
# These features capture HOW someone spends, not just WHAT they spend on

def extract_features(transactions: list) -> dict:
    """
    Takes a list of categorised transactions and extracts
    15 behavioural features that represent the user's financial personality.
    """

    if not transactions:
        return {}

    total = len(transactions)
    total_amount = sum(tx["amount"] for tx in transactions)

    # ── TEMPORAL FEATURES ──

    # 1. Late night spend ratio
    # proportion of transactions that happen after 10pm
    # high ratio = comfort seeking, impulse spending
    late_night = [tx for tx in transactions if _is_late_night(tx.get("time", ""))]
    late_night_ratio = len(late_night) / total

    # 2. Weekend spend ratio
    # high ratio = social spender, experience maximiser
    weekend = [tx for tx in transactions if _is_weekend(tx.get("day", ""))]
    weekend_ratio = len(weekend) / total

    # 3. Average transaction size
    # big infrequent purchases vs small frequent ones
    avg_transaction = total_amount / total

    # ── CATEGORY FEATURES ──

    # 4. Category entropy
    # how diverse or concentrated is spending across categories
    # low entropy = spends on few things (focused/anxious saver)
    # high entropy = spends on many things (experience maximiser)
    category_counts = {}
    for tx in transactions:
        cat = tx.get("predicted_category", tx.get("category", "Others"))
        category_counts[cat] = category_counts.get(cat, 0) + 1
    entropy = _calculate_entropy(category_counts, total)

    # 5. Top category dominance
    # what fraction of total spend goes to the single biggest category
    # high dominance = very focused spender
    category_amounts = {}
    for tx in transactions:
        cat = tx.get("predicted_category", tx.get("category", "Others"))
        category_amounts[cat] = category_amounts.get(cat, 0) + tx["amount"]

    top_category = max(category_amounts, key=category_amounts.get) if category_amounts else "Others"
    top_category_amount = category_amounts.get(top_category, 0)
    top_category_dominance = top_category_amount / total_amount if total_amount > 0 else 0

    # 6. Food ratio
    # food spending as fraction of total
    # high food ratio = comfort seeker, social spender
    food_amount = category_amounts.get("Food", 0) + category_amounts.get("Groceries", 0)
    food_ratio = food_amount / total_amount if total_amount > 0 else 0

    # 7. Food delivery ratio
    # grab/foodpanda as fraction of total food spend
    # SG-specific signal — high ratio = comfort seeking, low effort food
    delivery_keywords = ["grab", "foodpanda", "deliveroo", "grabfood"]
    delivery_amount = sum(
        tx["amount"] for tx in transactions
        if any(k in tx["description"].lower() for k in delivery_keywords)
    )
    food_delivery_ratio = delivery_amount / food_amount if food_amount > 0 else 0

    # 8. Shopping ratio
    # shopping as fraction of total
    # high = status signaller
    shopping_amount = category_amounts.get("Shopping", 0)
    shopping_ratio = shopping_amount / total_amount if total_amount > 0 else 0

    # 9. Subscription density
    # number of subscription transactions relative to total
    # high = inertia holder
    subscription_count = sum(
        1 for tx in transactions
        if tx.get("predicted_category", tx.get("category", "")) == "Subscriptions"
    )
    subscription_density = subscription_count / total

    # ── BEHAVIOURAL FEATURES ──

    # 10. Merchant loyalty score
    # do they return to the same merchants or constantly try new ones
    # high loyalty = inertia holder, comfort seeker
    # low loyalty = experience maximiser, status signaller
    merchant_counts = {}
    for tx in transactions:
        merchant = tx["description"].lower().split()[0]  # use first word as merchant proxy
        merchant_counts[merchant] = merchant_counts.get(merchant, 0) + 1
    repeat_merchants = sum(1 for count in merchant_counts.values() if count > 1)
    merchant_loyalty = repeat_merchants / len(merchant_counts) if merchant_counts else 0

    # 11. Impulse indicator
    # ratio of late-night high-value transactions
    # high = impulse spender, present hedonist
    avg_amount = total_amount / total
    impulse_transactions = [
        tx for tx in transactions
        if _is_late_night(tx.get("time", "")) and tx["amount"] > avg_amount * 1.5
    ]
    impulse_indicator = len(impulse_transactions) / total

    # 12. Entertainment ratio
    # entertainment as fraction of total
    # high = experience maximiser, present hedonist
    entertainment_amount = category_amounts.get("Entertainment", 0)
    entertainment_ratio = entertainment_amount / total_amount if total_amount > 0 else 0

    # ── PSYCHOLOGICAL FEATURES ──

    # 13. Present bias score (0-100)
    # combines late night ratio, impulse indicator, food delivery ratio
    # higher = more present-biased
    present_bias_score = min(100, round(
        (late_night_ratio * 40) +
        (impulse_indicator * 35) +
        (food_delivery_ratio * 25)
    ))

    # 14. Comfort seeking score (0-100)
    # combines food ratio, late night ratio, delivery ratio
    # higher = more comfort-seeking behaviour
    comfort_score = min(100, round(
        (food_ratio * 40) +
        (late_night_ratio * 35) +
        (food_delivery_ratio * 25)
    ))

    # 15. Status signalling score (0-100)
    # combines shopping ratio, merchant novelty, entertainment ratio
    # higher = more status-signalling behaviour
    merchant_novelty = 1 - merchant_loyalty
    status_score = min(100, round(
        (shopping_ratio * 50) +
        (merchant_novelty * 30) +
        (entertainment_ratio * 20)
    ))

    return {
        # temporal
        "late_night_ratio": round(late_night_ratio, 3),
        "weekend_ratio": round(weekend_ratio, 3),
        "avg_transaction": round(avg_transaction, 2),

        # category
        "entropy": round(entropy, 3),
        "top_category": top_category,
        "top_category_dominance": round(top_category_dominance, 3),
        "food_ratio": round(food_ratio, 3),
        "food_delivery_ratio": round(food_delivery_ratio, 3),
        "shopping_ratio": round(shopping_ratio, 3),
        "subscription_density": round(subscription_density, 3),
        "entertainment_ratio": round(entertainment_ratio, 3),

        # behavioural
        "merchant_loyalty": round(merchant_loyalty, 3),
        "impulse_indicator": round(impulse_indicator, 3),

        # psychological scores
        "present_bias_score": present_bias_score,
        "comfort_score": comfort_score,
        "status_score": status_score,

        # summary
        "total_transactions": total,
        "total_amount": round(total_amount, 2),
        "top_category_amount": round(top_category_amount, 2),
    }


# ── HELPER FUNCTIONS ──

def _is_late_night(time_str: str) -> bool:
    """Returns True if transaction happened after 10pm or before 6am"""
    late_night_indicators = ["late night", "night", "22", "23", "00", "01", "02"]
    return any(indicator in time_str.lower() for indicator in late_night_indicators)


def _is_weekend(day_str: str) -> bool:
    """Returns True if transaction happened on a weekend"""
    return any(day in day_str.lower() for day in ["saturday", "sunday", "sat", "sun"])


def _calculate_entropy(category_counts: dict, total: int) -> float:
    """
    Higher entropy = more diverse spending.
    Lower entropy = more concentrated spending.
    """
    import math
    if total == 0:
        return 0
    entropy = 0
    for count in category_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy