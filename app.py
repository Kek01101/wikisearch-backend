from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import psycopg2, json

# Obligatory app setup
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
conn = psycopg2.connect(host="ec2-54-163-254-204.compute-1.amazonaws.com", dbname="dpt2unfirlin7", user="gtktnnqqdhhtga",
                        password="eba958fc92598e3d580d84917af58f67488ea2c64d4af83ebfc096bd082bc532")
cur = conn.cursor()


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
    test_json_1 = {"test": True, "type": 1}
    test_json_2 = {"test": "True", "type": 2}
    score = int(request.args.get("score", None))
    print(score)
    cur.execute("INSERT INTO main VALUES (%s, %s, %s, %s)", (1, score, json.dumps(test_json_1), json.dumps(test_json_2)))
    conn.commit()
    return jsonify({"msg": "Data saved to SQL database successfully"})


if __name__ == '__main__':
    app.run()
