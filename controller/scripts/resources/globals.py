from flask import Flask
from flask_restful import Api
import os

app = Flask(__name__)

api = Api(app)

#Import Balena API keys
BALENA_SUPERVISOR_API_KEY = os.environ['BALENA_SUPERVISOR_API_KEY']
BALENA_SUPERVISOR_ADDRESS = os.environ['BALENA_SUPERVISOR_ADDRESS']