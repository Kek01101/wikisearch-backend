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
# Wikipedia API link setup
placeholder = "[PLACEHOLDER]"
api_search = f"http://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={placeholder}&srlimit=6&format=json"
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
    print(len(top_pages))
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
    searchpage = str(request.args.get("page", None))
    # Would normally ask user for preferred page, just pulls from the top page for now
    p_wiki = wiki_wiki.page(searchpage)
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
    with open("id_count.txt", "r") as file:
        id_count = int(file.readline())
    id_count += 1
    # Saving the new ripped article values to the DB - add function for updating old articles later
    cur.execute("INSERT INTO main VALUES (%s, %s, %s, %s)",
                (id_count, article, json.dumps(article_words), json.dumps(article_idfs)))
    conn.commit()
    with open("id_count.txt", "w") as file:
        file.write(str(id_count))

    """
    Query matching
    """
    # Tokenize the query so that matching can be performed
    query = set(tokenize(str(query)))
    # Saving 3 most relevant sentences to the query to "top_sentences" array
    top_sentences = sentence_match(query, sentences, word_score)

    """
    Placeholder response - for now
    """
    res = {
        "sentence_1": top_sentences[0],
        "sentence_2": top_sentences[1],
        "sentence_3": top_sentences[2]
    }
    return jsonify(res)


if __name__ == '__main__':
    app.run()
