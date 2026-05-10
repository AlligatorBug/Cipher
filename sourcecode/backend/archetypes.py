# Rule-based archetype assignment using behavioural features
# Will be replaced with DBSCAN clustering once we have enough user data

ARCHETYPES = {
    "The Comfort Seeker": {
        "description": "You spend to feel better. Your transactions reveal emotional regulation patterns — food and entertainment spike when stress is high, especially late at night.",
        "behavioural_root": "Emotional regulation spending",
        "signals": ["high food ratio", "high late night ratio", "high food delivery ratio"],
        "color": "#D4537E"
    },
    "The Present Hedonist": {
        "description": "You live for now. Your spending reflects a strong preference for immediate pleasure over future security — payday velocity is high and savings signals are absent.",
        "behavioural_root": "Present bias",
        "signals": ["high impulse indicator", "high late night ratio", "high entertainment ratio"],
        "color": "#ED93B1"
    },
    "The Status Signaller": {
        "description": "Your spending reflects how you want to be seen. Shopping dominates your transactions and you constantly try new merchants — your wallet reflects your social identity.",
        "behavioural_root": "Social comparison theory",
        "signals": ["high shopping ratio", "low merchant loyalty", "high entertainment ratio"],
        "color": "#2E7D32"
    },
    "The Anxious Saver": {
        "description": "You protect yourself from loss. Your spending is highly consistent and concentrated — you stick to what you know and avoid discretionary purchases.",
        "behavioural_root": "Loss aversion",
        "signals": ["low entropy", "high merchant loyalty", "low impulse indicator"],
        "color": "#81C784"
    },
    "The Optimism Spender": {
        "description": "You genuinely believe next month will be different. Your spending is inconsistent and impulsive — optimism about future income drives present overspending.",
        "behavioural_root": "Optimism bias",
        "signals": ["high impulse indicator", "high category entropy", "low subscription density"],
        "color": "#C8E6C9"
    },
    "The Inertia Holder": {
        "description": "Most of your spending isn't chosen — it's defaulted into. High subscription density and merchant loyalty suggest your wallet runs largely on autopilot.",
        "behavioural_root": "Status quo bias",
        "signals": ["high subscription density", "high merchant loyalty", "low entropy"],
        "color": "#999999"
    }
}


def assign_archetype(features: dict) -> tuple:
    """
    Takes the feature vector and assigns the most fitting archetype.
    Uses a scoring system — each archetype gets points based on
    how strongly the features match its signature.
    Returns (archetype_name, archetype_data, scores)
    """

    scores = {name: 0 for name in ARCHETYPES} # every archetype starts with a score of 0

    # ── Comfort Seeker signals ──
    # high food ratio, high late night, high delivery
    if features.get("food_ratio", 0) > 0.3:
        scores["The Comfort Seeker"] += 3
    if features.get("late_night_ratio", 0) > 0.2:
        scores["The Comfort Seeker"] += 2
    if features.get("food_delivery_ratio", 0) > 0.3:
        scores["The Comfort Seeker"] += 3
    if features.get("comfort_score", 0) > 50:
        scores["The Comfort Seeker"] += 2

    # ── Present Hedonist signals ──
    # high impulse, high late night, high entertainment
    if features.get("impulse_indicator", 0) > 0.15:
        scores["The Present Hedonist"] += 3
    if features.get("late_night_ratio", 0) > 0.25:
        scores["The Present Hedonist"] += 2
    if features.get("entertainment_ratio", 0) > 0.2:
        scores["The Present Hedonist"] += 2
    if features.get("present_bias_score", 0) > 60:
        scores["The Present Hedonist"] += 3

    # ── Status Signaller signals ──
    # high shopping, low merchant loyalty, high entertainment
    if features.get("shopping_ratio", 0) > 0.25:
        scores["The Status Signaller"] += 3
    if features.get("merchant_loyalty", 0) < 0.2:
        scores["The Status Signaller"] += 2
    if features.get("entertainment_ratio", 0) > 0.15:
        scores["The Status Signaller"] += 2
    if features.get("status_score", 0) > 50:
        scores["The Status Signaller"] += 3

    # ── Anxious Saver signals ──
    # low entropy, high merchant loyalty, low impulse
    if features.get("entropy", 0) < 1.5:
        scores["The Anxious Saver"] += 3
    if features.get("merchant_loyalty", 0) > 0.4:
        scores["The Anxious Saver"] += 2
    if features.get("impulse_indicator", 0) < 0.05:
        scores["The Anxious Saver"] += 2
    if features.get("top_category_dominance", 0) > 0.5:
        scores["The Anxious Saver"] += 2

    # ── Optimism Spender signals ──
    # high impulse, high entropy, low subscriptions
    if features.get("impulse_indicator", 0) > 0.1:
        scores["The Optimism Spender"] += 2
    if features.get("entropy", 0) > 2.0:
        scores["The Optimism Spender"] += 3
    if features.get("subscription_density", 0) < 0.1:
        scores["The Optimism Spender"] += 2
    if features.get("avg_transaction", 0) > 50:
        scores["The Optimism Spender"] += 2

    # ── Inertia Holder signals ──
    # high subscriptions, high merchant loyalty, low entropy
    if features.get("subscription_density", 0) > 0.15:
        scores["The Inertia Holder"] += 3
    if features.get("merchant_loyalty", 0) > 0.5:
        scores["The Inertia Holder"] += 3
    if features.get("entropy", 0) < 1.8:
        scores["The Inertia Holder"] += 2

    # pick the archetype with the highest score
    best_archetype = max(scores, key=scores.get)
    archetype_data = ARCHETYPES[best_archetype]

    return best_archetype, archetype_data, scores


def generate_insights(features: dict, archetype_name: str) -> list:
    """
    Generates real behavioural insights based on actual feature values.
    """
    insights = []

    top_cat = features.get("top_category", "Food")
    top_cat_pct = round(features.get("top_category_dominance", 0) * 100)
    top_cat_amount = features.get("top_category_amount", 0)

    if archetype_name == "The Status Signaller":
        insights.append({
            "color": "#2E7D32",
            "label": "Merchant novelty",
            "text": "You rarely return to the same merchants — always trying something new. This reflects a desire for novelty and variety in your spending."
        })
    elif archetype_name == "The Inertia Holder":
        insights.append({
            "color": "#999999",
            "label": "Spending on autopilot",
            "text": "A large portion of your spending happens automatically — subscriptions, habits, defaults. You may be paying for things you've forgotten about."
        })
    elif archetype_name == "The Anxious Saver":
        insights.append({
            "color": "#81C784",
            "label": "Concentrated spending",
            "text": f"Your spending is highly focused on {top_cat}. You stick to what you know — this reflects a cautious, loss-averse financial personality."
        })
    elif archetype_name == "The Comfort Seeker":
        insights.append({
            "color": "#D4537E",
            "label": "Emotional spending",
            "text": "Your spending spikes during stressful periods — food and entertainment are your comfort mechanisms. Your wallet is doing emotional work."
        })
    elif archetype_name == "The Present Hedonist":
        insights.append({
            "color": "#ED93B1",
            "label": "Living for now",
            "text": "You consistently prioritise present pleasure over future security. Your spending reflects a strong preference for immediate rewards."
        })
    elif archetype_name == "The Optimism Spender":
        insights.append({
            "color": "#C8E6C9",
            "label": "Optimism bias",
            "text": "You spend as if next month will be better — but the data shows a consistent pattern. Awareness is the first step to breaking the cycle."
        })

    # late night spending insight
    late_night_pct = round(features.get("late_night_ratio", 0) * 100)
    if late_night_pct > 20:
        insights.append({
            "color": "#D4537E",
            "label": "Late night spending",
            "text": f"{late_night_pct}% of your transactions happen after 10pm. These tend to be more impulsive and emotionally driven."
        })
    else:
        insights.append({
            "color": "#2E7D32",
            "label": "Healthy spending hours",
            "text": f"Most of your spending happens during the day — a sign of more deliberate financial decisions."
        })

    # top category insight
    top_cat = features.get("top_category", "Food")
    top_cat_pct = round(features.get("top_category_dominance", 0) * 100)
    top_cat_amount = features.get("top_category_amount", 0)
    insights.append({
        "color": "#81C784",
        "label": f"{top_cat} dominance",
        "text": f"{top_cat} is your biggest category at {top_cat_pct}% of your spending (${top_cat_amount}). {'This is above average for your archetype.' if top_cat_pct > 40 else 'Your spending is fairly balanced across categories.'}"
    })

    # subscription insight
    sub_density = features.get("subscription_density", 0)
    if sub_density > 0.1:
        sub_count = round(sub_density * features.get("total_transactions", 10))
        insights.append({
            "color": "#ED93B1",
            "label": "Subscription creep",
            "text": f"About {sub_count} of your transactions are recurring subscriptions. Review them regularly — unused subscriptions are one of the easiest ways to leak money."
        })
    else:
        insights.append({
            "color": "#2E7D32",
            "label": "Low subscription load",
            "text": "You have few recurring subscriptions — good. Subscription creep is one of the most common ways people lose money without noticing."
        })

    # food delivery insight
    delivery_ratio = features.get("food_delivery_ratio", 0)
    if delivery_ratio > 0.3:
        insights.append({
            "color": "#D4537E",
            "label": "Food delivery habit",
            "text": f"{round(delivery_ratio * 100)}% of your food spend goes to delivery apps. Convenience is costing you — cooking even 2x a week could save you significantly."
        })

    return insights[:3]  # return top 3 most relevant insights