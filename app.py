from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import psycopg2, json, requests, wikipediaapi, nltk, re
from NLP_functions import tokenize, calc_idfs, sentence_match, article_match

# nltk dependencies download
nltk.download("punkt")
nltk.download("stopwords")
# Flask app setup
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# Database connection setup
conn = psycopg2.connect(host="ec2-54-163-254-204.compute-1.amazonaws.com", dbname="dpt2unfirlin7", user="gtktnnqqdhhtga",
                        password="eba958fc92598e3d580d84917af58f67488ea2c64d4af83ebfc096bd082bc532")
cur = conn.cursor()
# Wikipedia API link setup
placeholder = "[PLACEHOLDER]"
api_search = f"http://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={placeholder}&srlimit=6&format=json"
citation_pull = f"http://en.wikipedia.org/w/api.php?action=parse&page={placeholder}&prop=wikitext&format=json"
# Wikipedia API extraction setup
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI
)


@app.route('/')
@cross_origin()
def hello_world():
    return 'CORS test'


@app.route('/api-test/', methods=['GET'])
@cross_origin()
def apicheck():
    # Checking that intended message is received
    msg = request.args.get("msg", None)
    msg2 = request.args.get("msg2", None)
    print(f"Message is {msg}")
    print(f"Message 2 is {msg2}")

    # Checking that sending responses works too
    res = {"msg": f"Msg: {msg2}"}
    return jsonify(res)


@app.route('/db-test/', methods=['GET'])
@cross_origin()
def dbcheck():
    # Checking that intended message is received, and that DB saving works
    id_count = 0
    # Need to actually keep track of PK, id_count does this
    test_json_1 = {"test": True, "type": 1}
    test_json_2 = {"test": "True", "type": 2}
    score = str(request.args.get("score", None))
    # DB values are (PK, article text, article tokens, article idfs)
    cur.execute("INSERT INTO main VALUES (%s, %s, %s, %s)", (id_count, score, json.dumps(test_json_1), json.dumps(test_json_2)))
    conn.commit()
    return jsonify({"msg": "Data saved to SQL database successfully"})


@app.route('/wikimatch/', methods=['GET'])
@cross_origin()
def wikimatch():
    """
    This function handles searching wikipedia for the subject, and then returning 5 possible wiki pages to the user

    First request to the backend should ONLY include the subject, query should be sent to main wiki_search function
    """
    # Handles the actual wiki searching, handles all functionality using appropriate modules
    subject = str(request.args.get("subject", None))

    # Formats and sends a request to the wikipedia API for 5 most-related pages to subject
    subject.replace(' ', "%20")
    page_search = api_search.replace(placeholder, subject)
    # Saves top 5 returned pages to top_pages list
    top_pages = requests.get(page_search).json()["query"]["search"]
    # Formats response as JSON with 5 keys, each one representing a different term
    res = dict()
    for a in range(5):
        res[f"data{a}"] = top_pages[a]["title"]
    return jsonify(res)


@app.route('/wikisearch/', methods=['GET'])
@cross_origin()
def wiki_search():
    """
    Wiki page sanitization
    """
    query = str(request.args.get("query", None))
    title = str(request.args.get("title", None))
    # Pulls the desired article text using wikipedia-api library
    p_wiki = wiki_wiki.page(title)
    article = str(p_wiki.text)
    # Manually pulls all citations from a wikipedia page using regex
    title.replace(' ', "%20")
    citation_search = citation_pull.replace(placeholder, title)
    data = requests.get(citation_search).json()["parse"]["wikitext"]["*"]
    matches = re.findall(r'<ref>(.*?)</ref>', data)
    # URLs formatted and saved to "citations" array
    unclean_citations = []
    for match in matches:
        unclean_citations.append(str(re.findall(r'\|url=(.*?)\|', match)).strip("[']"))
    # Cleaning up citations a bit more, and removing "empty" citations
    citations = []
    for citation in unclean_citations:
        if citation != "":
            citations.append(citation.strip(" "))

    """
    NLP
    """
    # taking all articles from DB in order to calculate article_idfs
    articles = dict()
    article_titles = dict()
    article_ids = dict()
    cur.execute('SELECT * FROM main;')
    rows = cur.fetchall()
    if rows is not None:
        for row in rows:
            articles[row[1]] = row[2]
            article_titles[row[1]] = row[3]
            article_ids[row[3]] = row[0]
    # saving article tokens and idfs to an array for DB saving
    article_words = tokenize(article)
    articles[article] = article_words
    # take all articles from DB and use them to calculate article_idfs
    article_idfs = calc_idfs(articles)
    # split document into a list of ordered tokens and save to sentence dict, and also sentence_index array
    sentence_index = []
    sentences = dict()
    for sentence in nltk.sent_tokenize(article):
        tokens = tokenize(sentence)
        if tokens:
            sentence_index.append(sentence)
            sentences[sentence] = tokens
    # calculate IDF values for each sentence and save to word_score dict
    word_score = calc_idfs(sentences)

    """
    Saving new data to database - will update old data if page already present
    """
    id_count = len(articles)
    # Saving the new ripped article values to the DB - add function for updating old articles later
    try:
        article_ids[title]
        cur.execute(f"UPDATE main SET article = (%s), tokens = (%s) WHERE id = (%s);",
                    (article, json.dumps(article_words), article_ids[title]))
    except KeyError:
        cur.execute("INSERT INTO main VALUES (%s, %s, %s, %s);",
                    (id_count, article, json.dumps(article_words), title))
    conn.commit()

    """
    Query matching
    """
    # Tokenize the query so that matching can be performed
    query = set(tokenize(str(query)))
    # Saving 3 most relevant sentences to the query to "top_sentences" array
    top_sentences = sentence_match(query, sentences, word_score)
    # matching queries to articles to find if there are any more-relevant articles
    top_articles = article_match(query, articles, article_idfs)
    # sending better articles to frontend if they exist
    article_1 = ""
    article_2 = ""
    if article != top_articles[0] and article != top_articles[1]:
        article_1 = top_articles[0]
        article_2 = top_articles[1]
    elif article != top_articles[0]:
        article_1 = top_articles[0]

    """
    Sentences and associated citations are put into JSON form for response to frontend
    """
    res = {
        "sentence_1": top_sentences[0],
        "sentence_2": top_sentences[1],
        "sentence_3": top_sentences[2],
        "url": str(p_wiki.fullurl),
        "article_1": article_1,
        "article_1_title": article_titles[article_1],
        "article_2": article_2,
        "article_2_title": article_titles[article_2]
    }
    # catchall for if there is only one, or if there are no citations
    # citations assigned based upon sentence position in wikipedia article - not perfect, but the best solution I found
    if len(citations) != 1 and len(citations) != 0:
        res["citation_1"] = citations[int(round(sentence_index.index(top_sentences[0]) / len(sentences) * len(citations)))]
        res["citation_2"] = citations[int(round(sentence_index.index(top_sentences[1]) / len(sentences) * len(citations)))]
        res["citation_3"] = citations[int(round(sentence_index.index(top_sentences[2]) / len(sentences) * len(citations)))]
    elif len(citations) == 0:
        res["citation_1"] = "Sorry, no citations were found!"
        res["citation_2"] = "Sorry, no citations were found!"
        res["citation_3"] = "Sorry, no citations were found!"
    else:
        res["citation_1"] = citations[0]
        res["citation_2"] = citations[0]
        res["citation_3"] = citations[0]
    # If articles are so short they only contain one or two sentences, an appropriate message is returned
    if res["sentence_3"] == "":
        res["sentence_3"] = "Sorry, no more sentences were found in this document"
        res["citation_3"] = "There are no citations for non-sentences"
    if res["sentence_2"] == "":
        res["sentence_2"] = "Sorry, no more sentences were found in this document"
        res["citation_2"] = "There are no citations for non-sentences"

    # Response is returned to frontend in JSON form
    return jsonify(res)


if __name__ == '__main__':
    app.run()
