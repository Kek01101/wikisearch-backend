from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


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


if __name__ == '__main__':
    app.run()
