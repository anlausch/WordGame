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
import unicodedata
import doctest

class Server:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


    def normalize_string(self, s):
        """
        >>> s = Server(); s.normalize_string("Mädchen")
        'Maedchen'
        >>> s = Server(); s.normalize_string("Mädchen Hut")
        'Maedchen_Hut'
        >>> s = Server(); s.normalize_string("Mädchen Hütte Hälfte")
        'Maedchen_Huette_Haelfte'
        """
        umlaut_dict = {u'ä': u'ae',
                       u'ö': u'oe',
                       u'ü': u'ue',
                       u'ß': u'ss',
                       u'Ä': u'Ae',
                       u'Ö': u'Oe',
                       u'Ü': u'Ue',
                       }
        for (key, value) in umlaut_dict.items():
            s = s.replace(key, value)
        multi_word = s.split(" ")
        if len(multi_word) > 1:
            s = '_'.join(multi_word)
        return s

    def guess_check(self, prediction=[], guess=""):
        """
        >>> s = Server(); s.guess_check(["Maedchen"],"Mädchen")
        'Mädchen'
        >>> s = Server(); s.guess_check(["maerchen_schloss"],"Märchen Schloss")
        'Märchen Schloss'
        """
        original = guess
        #guess = unicodedata.normalize('NFD', guess)#.encode('ascii', 'ignore')
        guess = self.normalize_string(guess)
        if guess in prediction or guess.capitalize() in prediction or guess.lower() in prediction:
            return original
        else:
            return None

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
        text = server.normalize_string(text)
        prediction = server.predictor.predict(text=text)
        if len(prediction) == 0:
            prediction = server.predictor.predict(text=text.lower())
            if len(prediction) == 0:
                prediction = server.predictor.predict(text=text.capitalize())
                if len(prediction) == 0:
                    return render_template("index.html", error="Leider konnten wir den Begriff " + str(text) + " nicht finden.")
        return render_template("index.html", prediction=prediction, baseterm=text, no_hits=len(prediction))
    except Exception as e:
        return str(e)

@app.route('/guess', methods=['POST'])
def guess():
    try:
        guess = request.form["guess"]
        prediction = eval(request.form["prediction"])
        baseterm = request.form["baseterm"]
        correct_guesses = request.form["correct_guesses"]
        if correct_guesses != "":
            correct_guesses = eval(correct_guesses)
        else:
            correct_guesses = []
        if guess is None or guess == "" or guess == " ":
            logger.error("No data provided")
            return render_template("index.html", prediction=prediction, no_hits=len(prediction), correct_guesses=correct_guesses, baseterm=baseterm, error="Bitte gib einen Begriff ein, wenn du rätst.")

        logger.info("Guess: " + json.dumps(guess))
        correct_guess = server.guess_check(guess=guess, prediction=prediction)
        if correct_guess is None:
            return render_template("index.html", prediction=prediction, no_hits=len(prediction),
                                   correct_guesses=correct_guesses, baseterm=baseterm, guess=guess, wrong_guess="Leider falsch. Die Assoziation \"" + str(guess) + "\" hat unser System nicht gefunden.")
        correct_guesses.append(correct_guess)
        return render_template("index.html", prediction=prediction, no_hits=len(prediction), correct_guesses=correct_guesses,
                               baseterm=baseterm, right_guess="Ein Volltreffer! Die Assoziation \"" + str(guess) + "\" wurde auch von unserem System gefunden.")
    except Exception as e:
        return str(e)

@app.route('/solution', methods=['POST'])
def show_solution():
    try:
        prediction = eval(request.form["prediction"])
        baseterm = request.form["baseterm"]
        correct_guesses = request.form["correct_guesses"]
        if correct_guesses != "":
            correct_guesses = eval(correct_guesses)
        else:
            correct_guesses = []
        return render_template("index.html", prediction=prediction, no_hits=len(prediction), correct_guesses=correct_guesses, baseterm=baseterm, show=True)
    except Exception as e:
        return str(e)


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@app.route('/predict', methods=['GET'])
@app.route('/guess', methods=['GET'])
@app.route('/solution', methods=['GET'])
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