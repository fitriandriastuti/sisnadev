
import numpy as np
import pandas as pd
import spacy
# import seaborn as sns
# import matplotlib.pyplot as plt

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

spacy.load("en_core_web_md")
spacy.load("en_core_web_sm")

def prepare_models():
    nlp = spacy.load('en_core_web_md')
    tokenize = spacy.load('en_core_web_sm', disable=['parser', 'ner', 'tok2vec', 'attribute_ruler'])
    return  nlp, tokenize

nlp, tokenize = prepare_models()

# count vectorizer
def count_vectorizer(sentences, metric = 'cosine'):
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(sentences)
    arr = X.toarray()
    if metric == 'cosine':
        return cosine_similarity(arr)
    else:
        return 1/np.exp((euclidean_distances(arr)))

# tfidf vectorizer
def tfid_vectorizer(sentences, metric = 'cosine'):
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(sentences)
    arr = X.toarray()
    if metric == 'cosine':
        return cosine_similarity(arr)
    else:
        return 1/np.exp((euclidean_distances(arr)))

# word2vec
def word2vec(dataapbd, akun, metric = 'cosine'):
    docs1 = [nlp(sentence1) for sentence1 in dataapbd]
    docs = [nlp(sentence) for sentence in akun]
    similarity = []

    for i in range(len(docs1)):
        row = []
        for j in range(len(docs)):
            if metric == 'cosine':
              row.append(docs1[i].similarity(docs[j]))
            else:
               row.append(1/np.exp((euclidean_distances(docs1[i].vector.reshape(1, -1), docs[j].vector.reshape(1, -1))[0][0])))
        similarity.append(row)
    return similarity

# word2vecpepo
def word2vecpepo(dataapbd, akun, metric = 'cosine'):
    docs1 = nlp(dataapbd)
    docs = [nlp(sentence) for sentence in akun]
    similarity = []

    row = []
    for j in range(len(docs)):
        if metric == 'cosine':
            print(docs1, ' - ', docs[j])
            row.append(docs1.similarity(docs[j]))
        else:
            row.append(1 / np.exp((euclidean_distances(docs1.vector.reshape(1, -1), docs[j].vector.reshape(1, -1))[0][0])))
    similarity.append(row)

    return row

# helper methods
def remove_punctuations(normalized_tokens):
    punctuations=['?',':','!',',','.',';','|','(',')','--']
    for word in normalized_tokens:
        if word in punctuations:
            normalized_tokens.remove(word)
    return normalized_tokens

def jaccard_similarity(x,y):
    """ returns the jaccard similarity between two lists """
    intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
    union_cardinality = len(set.union(*[set(x), set(y)]))
    return intersection_cardinality/float(union_cardinality)

def calc_jaccard(sentences):
  similarity = []
  for i in range(len(sentences)):
    row = []
    for j in range(len(sentences)):
      row.append(jaccard_similarity(sentences[i], sentences[j]))
    similarity.append(row)
  return similarity

def calc_similarity(sentences, base):
    docs = [tokenize(sentence) for sentence in sentences]
    tokens = []

    for doc in docs:
        temp = []
        for token in doc:
            temp.append(token.lemma_)
        tokens.append(temp)
    tokens_no_punc = list(map(remove_punctuations, tokens))
    similarity = calc_jaccard(tokens_no_punc)
    print(similarity)

def similairty_word2vec(db, dataapbd, akun, data_A2022, m_akun):
    w2v = word2vec(dataapbd, akun)
    print(w2v)
    i = 0
    for w2v_ in w2v:
        if 1 in w2v_:
            max_val_w2v = 1
        else:
            max_val_w2v = max(w2v_)
        idx_max = w2v_.index(max_val_w2v)
        idx = idx_max
        # print('Higest Score: ', max_val_w2v, ' - in Index: ', idx, ' - Hasilnya Masuk Akun: ', akun[idx], ' - m_akun: ', m_akun[idx],' - Data APBD Awalnya: ', dataapbd[i],' - data_A2022: ', data_A2022[i])
        print('Higest Score: ', max_val_w2v, ' - in Index: ', idx, ' - Hasilnya Masuk Akun: ', akun[idx], ' - Data APBD Awalnya: ', dataapbd[i])
        # q_akun = db['m_akun'].find_one(
        #     {
        #         'nama_akun': {'$regex': akun[idx], '$options': 'i'}
        #     },
        # )
        # print(q_akun)
        score_similarity = {
            'score_similarity_word2vec': max_val_w2v,
            'idx_similarity_word2vec': idx,
            # '_id_akun': m_akun[idx]['_id_akun'],
            # 'kode_akun': q_akun['kode_akun'],
            'nama_akun': akun[idx],
        }
        insert_result_similarity = data_A2022[i].update(score_similarity)
        # print(insert_result_similarity)

        new_user = db["m_similarity"].insert_one(insert_result_similarity)
        i += 1
















