# build a FAISS index from transactions, and search it with a query
# FAISS -> similarity search library
# normal DB: stores text/numbers, searches by exact match or filters
# FAISS: stores vectors, searches by similarity

import numpy as np
import faiss 
from categoriser import get_st_model

_index_cache = {} # (user_id, txn_count) -> faiss index

def _build_index(transactions):
    model = get_st_model() # sentence transformer model
    descriptions = [
        f"{tx.get('description', '')} {tx.get('predicted_category', '')} {tx.get('date', '')}".strip()
        for tx in transactions
    ]
    embeddings = model.encode(descriptions, show_progress_bar=False) # turn each desc into a vector
    embeddings = np.array(embeddings, dtype='float32') # convert to faiss format
    faiss.normalize_L2(embeddings) # normalize for cosine similarity
    index = faiss.IndexFlatIP(embeddings.shape[1]) # create an empty faiss index
    index.add(embeddings) # dump all the vectors into the index
    return index

def search(query, transactions, user_id, top_k=None, threshold=0.3):
    if not transactions: # if no transactions
        return [] 
    
    cache_key = (user_id, len(transactions)) # check if we have a faiss index built for this user w this many transactions
    if cache_key not in _index_cache:
        # evict old index for this user, rebuild
        for k in [k for k in _index_cache if k[0] == user_id]:
            del _index_cache[k]
        _index_cache[cache_key] = _build_index(transactions)
    
    index = _index_cache[cache_key] # grab index from cache
    model = get_st_model()

    q = model.encode([query], show_progress_bar=False) # turn search query into a vector 
    q = np.array(q, dtype="float32")
    faiss.normalize_L2(q)

    k = min(top_k, len(transactions)) if top_k else len(transactions)
    scores, indices = index.search(q, k) # return most similar transactions and their similarity scores

    return [{**transactions[i], "similarity": float(s)} for s, i in zip(scores[0], indices[0]) if i >= 0 and s >= threshold]
