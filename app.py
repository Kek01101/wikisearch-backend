from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import psycopg2, json, requests, wikipediaapi, nltk
from NLP_functions import tokenize, calc_idfs, sentence_match

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
# Database primary key variable setup
id_count = 0
# Wikipedia API link setup
placeholder = "[PLACEHOLDER]"
api_search = f"http://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={placeholder}&srlimit=5&format=json"
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
    # Need to actually keep track of PK, id_count does this
    global id_count
    id_count += 1
    test_json_1 = {"test": True, "type": 1}
    test_json_2 = {"test": "True", "type": 2}
    score = str(request.args.get("score", None))
    # DB values are (PK, article text, article tokens, article idfs)
    cur.execute("INSERT INTO main VALUES (%s, %s, %s, %s)", (id_count, score, json.dumps(test_json_1), json.dumps(test_json_2)))
    conn.commit()
    return jsonify({"msg": "Data saved to SQL database successfully"})


@app.route('/wikisearch/', methods=['GET'])
@cross_origin()
def wiki_search():
    # Handles the actual wiki searching, handles all functionality using appropriate modules
    query = str(request.args.get("query", None))
    subject = str(request.args.get("subject", None))

    # Formats and sends a request to the wikipedia API for 5 most-related pages to subject
    subject.replace(' ', "%20")
    page_search = api_search.replace(placeholder, subject)
    # Saves top 5 returned pages to top_pages list
    top_pages = requests.get(page_search).json()["query"]["search"]

    """
    Wiki page sanitization
    """
    # Would normally ask user for preferred page, just pulls from the top page for now
    p_wiki = wiki_wiki.page(top_pages[0]["title"])
    article = str(p_wiki.text)

    """
    NLP
    """
    # saving article tokens and idfs to an array for DB saving
    article_words = tokenize(article)
    # take all articles from DB and use them to calculate article_idfs, then re-save
    article_idfs = calc_idfs({article: article_words})
    # split document into a list of ordered tokens and save to sentence dict
    sentences = dict()
    for sentence in nltk.sent_tokenize(article):
        tokens = tokenize(sentence)
        if tokens:
            sentences[sentence] = tokens
    # calculate IDF values for each sentence and save to word_score dict
    word_score = calc_idfs(sentences)

    """
    DB Hookup
    """
    global id_count
    id_count += 1
    # Saving the new ripped article values to the DB - add function for updating old articles later
    cur.execute("INSERT INTO main VALUES (%s, %s, %s, %s)",
                (id_count, article, json.dumps(article_words), json.dumps(article_idfs)))
    conn.commit()

    """
    Query matching
    """
    # Tokenize the query so that matching can be performed
    query = set(tokenize(str(query)))
    # Saving 3 most relevant sentences to the query to "top_sentences" array
    top_sentences = sentence_match(query, sentences, word_score)
    print(top_sentences)

    """
    Placeholder response - for now
    """
    res = {
        "article": article,
        "sentence_1": top_sentences[0],
        "sentence_2": top_sentences[1],
        "sentence_3": top_sentences[2]
    }
    return jsonify(res)


if __name__ == '__main__':
    app.run()
