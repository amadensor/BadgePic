import flask
import json
import boto3

app=flask.Flask(__name__)
IOT=boto3.client("iot-data")

@app.route('/',methods=['GET'])
def static_page():   
    return flask.render_template('static_form.html')

@app.route('/',methods=['POST'])
def do_stuff():
    x={
        'pic': flask.request.form['pic']
    }
    IOT.publish(topic="badge/pic",payload=json.dumps(x))

    return flask.render_template('static_form.html')
