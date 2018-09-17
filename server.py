#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, redirect, url_for, Response
from logging.handlers import RotatingFileHandler
from time import strftime
import traceback
import logging
from flask_bootstrap import Bootstrap
import predictor
import json


class Server:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

server = Server()
app = Flask(__name__)
Bootstrap(app)


@app.route('/predict', methods=['POST'])
def predict():
    try:
        text = request.form["input"]
        if text is None or text == "" or text == " ":
            logger.error("No data provided")
            return render_template("index.html", error="Bitte gib einen Begriff ein, bevor du auf Abschicken drückst.")

        logger.info("Data: " + json.dumps(text))
        prediction = server.predictor.predict(text=text)
        if len(prediction) == 0:
            return render_template("index.html", error="Leider konnten wir den Begriff " + str(text) + " nicht finden.")
        return render_template("index.html", prediction=prediction, baseterm=text)
    except Exception as e:
        return str(e)


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@app.route('/predict', methods=['GET'])
def index():
    return render_template("index.html")



@app.after_request
def after_request(response):
    """ Logging after every request. """
    # This avoids the duplication of registry in the log,
    # since that 500 is already logged via @app.errorhandler.
    if response.status_code != 500:
        ts = strftime('[%Y-%b-%d %H:%M]')
        logger.error('%s %s %s %s %s %s',
                      ts,
                      request.remote_addr,
                      request.method,
                      request.scheme,
                      request.full_path,
                      response.status)
    return response


@app.errorhandler(Exception)
def exceptions(e):
    """ Logging after every Exception. """
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                  ts,
                  request.remote_addr,
                  request.method,
                  request.scheme,
                  request.full_path,
                  tb)
    return "Internal Server Error", 500


if __name__ == '__main__':
    print("Starting server")
    pred = predictor.Predictor()
    pred.load_embeddings()

    server = Server(predictor=pred)
    handler = RotatingFileHandler('./log/app.log', maxBytes=10000, backupCount=3)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    app.run(port=8000)