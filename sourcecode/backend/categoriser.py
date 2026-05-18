import re
import pickle
import os

# ── load ML model ──
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'categoriser_model.pkl')
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            with open(MODEL_PATH, 'rb') as f:
                _model = pickle.load(f)
        except Exception as e:
            print(f"Warning: could not load ML model: {e}")
    return _model

def clean_description(text):
    text = str(text).lower()
    text = re.sub(r'\*[a-z0-9\-]+', ' grab ', text)
    text = re.sub(r'bill_[a-z0-9]+', ' parking ', text)
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Rule-based transaction categoriser for Singapore merchants -- fallback if ML model is funky
RULES = {
    # check these first — more specific categories before general ones
    'Groceries': [
        'ntuc fairprice', 'ntuc fp', 'fairprice app', 'fairprice online',
        'fairprice finest', 'fairprice xtra',
        'giant hypermart', 'giant supermarket', 'sheng siong',
        'cold storage', 'redmart', 'jasons marketplace',
    ],
    'Subscriptions': [
        'netflix', 'spotify', 'disney+', 'disney plus', 'apple.com/bill',
        'google one', 'youtube premium', 'amazon prime', 'microsoft 365',
        'adobe', 'dropbox', 'icloud', 'canva', 'notion',
        'm1 limited', 'singtel', 'starhub', 'circles life',
    ],
    'Utilities': [
        'sp services', 'sp digital', 'sp group', 'singapore power',
        'union gas', 'cnergy', 'city gas', 'geneco', 'sembcorp',
        'keppel electric', 'senoko', 'pub singapore',
    ],
    'Health': [
        'raffles medical', 'raffles hospital', 'mount elizabeth',
        'gleneagles', 'parkway', 'thomson medical', 'polyclinic',
        'bfit', 'fitness first', 'anytime fitness', 'virgin active',
        'watsons', "watson's", 'watson s', 'unity pharmacy', 'guardian health',
        'physio', 'physiotherapy', 'urology', 'orthopaedic',
        'greateasternlife', 'great eastern', 'prudential', 'aia singapore',
        'ntuc income', 'aviva', 'fwd insurance',
    ],
    'Transport': [
        'grab*', 'bus/mrt', 'mrt', 'transitlink', 'ez-link', 'ezlink',
        'comfort', 'comfortdelgro', 'cdg', 'gojek', 'tada', 'ryde',
        'parking.sg', 'parking.sgbill', 'wilson parking', 'ura parking',
        'shell', 'caltex', 'esso', 'exxonmobil', 'spc petrol', 'bp petrol',
        'singaporeair', 'singapore airlines', 'scoot', 'jetstar', 'airasia',
        'tigerair', 'batik air', 'egencia',
    ],
    'Entertainment': [
        'golden village', 'gv cinema', 'shaw theatres', 'cathay cinema',
        'filmgarde', 'we cinemas', 'klook', 'kkday', 'sistic',
        'universal studios', 'night safari', 'singapore zoo',
        'solace studios', 'photobooth',
    ],
    'Shopping': [
        'shopee', 'lazada', 'amazon sg', 'qoo10', 'zalora',
        'uniqlo', 'h&m', 'zara', 'cotton on', 'isetan',
        'daiso', 'daisojapan', 'lotte dfs', 'lotte t2', 'lotte t3',
        'guardian pharmacy',
    ],
    'Food': [
        'kopitiam', 'hawker', 'foodpanda', 'deliveroo',
        'mcdonalds', 'mcdonald', 'kfc', 'burger king', 'subway',
        'starbucks', 'toastbox', 'ya kun', 'yakun',
        'gongcha', 'gong cha', 'liho', 'koi cafe', 'playmade',
        'tiger sugar', 'tealive', 'sharetea',
        'sakae sushi', 'sushi express', 'itacho',
        'old chang kee', 'bengawan solo', 'breadtalk', 'prima deli',
        'dondondonki', 'don don donki',
        'saizeriya', 'mooloolabar', 'morganfields',
        'maccha house', 'yochi', 'icetalk', 'ice talk',
    ],
}

def rule_based_categorise(description):
    desc_lower = description.lower()
    for category, keywords in RULES.items():
        for kw in keywords:
            if kw in desc_lower:
                return category
    return None

def ml_categorise(description):
    model = get_model()
    if model is None:
        return None, 0.0
    try:
        cleaned = clean_description(description)
        pred = model.predict([cleaned])[0]
        proba = max(model.predict_proba([cleaned])[0]) # predict_proba() returns a probability for every category & max picks the highest one
        return pred, proba
    except Exception:
        return None, 0.0


def categorise_transactions(transactions):
    result = []
    for tx in transactions:
        desc = tx.get('description', '')
        user_cat = tx.get('category', '')
        
        if user_cat and user_cat != 'Others':
            predicted = user_cat # if user set it, respect it and skip ML 
        else:
            pred, conf = ml_categorise(desc) # ask ML model 
            if pred and conf > 0.25: # if ML is confident enough, use it
                predicted = pred 
            else:
                rule_pred = rule_based_categorise(desc) # fallback on rules 
                predicted = rule_pred if rule_pred else 'Others'
        
        result.append({**tx, 'predicted_category': predicted}) # add category to tx
    return result