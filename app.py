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
    print(f"Message is {msg}")

    # Checking that sending responses works too
    res = {"msg": f"Msg: {msg}"}
    return jsonify(res)


if __name__ == '__main__':
    app.run()
