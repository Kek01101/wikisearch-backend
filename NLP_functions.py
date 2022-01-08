import nltk, string
from copy import deepcopy
from math import log
from collections import Counter


def tokenize(document):
    """
    Given a document(or sub-doc like a sentence), this function will return a list of all the lowercase words in that
    document.

    This also removes any punctuation or "stopwords" - common meaningless words such as "an", "and", etc.

    Results of tokenization immediately saved to sentence dict, where each sentence is represented by its sentence
    tokens.
    """
    # word_tokenize splits each word and punctuation into a separate item in a list - all lowercase
    words = nltk.word_tokenize(document.lower())
    # remove punctuation and stopwords from words list
    for word in deepcopy(words):
        if word in string.punctuation or word in nltk.corpus.stopwords.words('english'):
            words.remove(word)
    return words


def calc_idfs(documents):
    """
    Given a dictionary of a document or many sentences mapped from sentence/doc: words, return dictionary mapping words
    to IDF values.

    IDF - Inverse document frequency, how rare a word is within a "document"

    Results from the comp_idfs will be used for more document recommendations as well as calculating query matches
    """
    words = dict()
    clearlist = []
    for doc in documents:
        for word in documents[doc]:
            if word not in clearlist:
                clearlist.append(word)
    for word in clearlist:
        count = 0
        for doc in documents:
            if word in documents[doc]:
                count += 1
        words[word] = log((len(documents))/count)
    return words


def sentence_match(query, sentences, word_scores, n=3):
    """
    Given a query, sentences, and the IDF values of the words in those sentences, provide the n best sentence
    matches for said query. If there is an IDF tie, the query term density will be used to settle the tie.
    """
    def sortByScore(sList):
        return sList[1]
    rankings = []
    output = []
    for sentence in sentences:
        score = 0
        qtd = 0
        for word in query:
            for term in sentences[sentence]:
                if word == term:
                    score += word_scores[word]
                    qtd += 1
        qtd = qtd/len(sentences[sentence])
        rankings.append((sentence, score, qtd))
    rankings.sort(key=sortByScore, reverse=True)
    print(rankings)
    raise NotImplementedError
    for a in range(n):
        output.append((rankings[0], rankings[1]))
    return output


def article_match(query, articles, article_scores, n=2):
    """
    Finds other articles already within the DB which may also be helpful for the user. Functions in much the same way
    that the sentence_match function does.

    Full TF-IDF is used here, whereas only IDF is used for the actual sentence matching. This is because this considers
    many documents, and sentence match only considers one at a time.
    """
    def sortByScore(sList):
        return sList[1]
    rankings = []
    output = []
    for article in articles:
        articles[article] = Counter(articles[article]).most_common()
        score = 0
        for word in query:
            for term, frequency in articles[article]:
                if word == term:
                    score += float(frequency)*article_scores[term]
        rankings.append((article, score))
    rankings.sort(key=sortByScore, reverse=True)
    for a in range(n):
        output.append(rankings[a][0])
    return output