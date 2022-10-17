import json
from flask_cors import CORS
from flask import Flask,jsonify, request, render_template, session
from flask_session import Session 
import ldclient
from ldclient.config import Config
import os
import eventlet
import uuid
import boto3
eventlet.monkey_patch()
from config import ApplicationConfig
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_url_path='',
                  static_folder='build',
                  template_folder='build')
app.config.from_object(ApplicationConfig)

server_session = Session(app)

# LD_KEY = os.environ.get('LD_SERVER_KEY')
LD_KEY = 'sdk-946ca72c-3389-4324-bdc6-b275d88b1d93'
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')

status_api = 'v2.3344'

fallback = '{"dbhost":"db","mode":"local"}'

user = {
    "key": "anonymous"
}
ldclient.set_config(Config(LD_KEY))


@app.route('/')
def default_path():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def app_login():
    request_data = request.get_json()
    session['key'] = request_data['key']
    # session['device'] = request_data['device']
    # session['operatingSystem'] = request_data['operatingSystem']
    status = {
        "status": session['key']+" has been logged in"
    }
    return jsonify(status) 

@app.route("/logout")
def app_logout():
    session.pop('key', default=None)
    status = {
        "status":"logged out"
    }
    return jsonify(status)


@app.route("/health")
def get_api():
    ldclient.set_config(Config(LD_KEY))
    print(session)
    try: 
        user = {
            "key": session['key']
        }
    except:
        user = {
            "key": 'debuguser'
        }
    ldclient.get().identify(user)
    dbinfo = ldclient.get().variation('dbinfo', user, fallback)
    print(user)
    if dbinfo['mode'] == "cloud":
        stats = {
            'version': '2',
            'status': 'Healthy - Migration Successful',
            'location': 'Cloud'
        }
    elif dbinfo['mode'] == "local":
        stats = {
            'version': '1',
            'status': 'Not Migrated',
            'location': 'Local'
        } 
    else:
        stats = {
            'version': '???',
            'status': 'unhealthy',
            'location': 'DebugData'
        }
    return jsonify(stats)

@app.route("/datas", methods=["GET", "POST"])
def thedata():
    ldclient.set_config(Config(LD_KEY))
    try: 
        user = {
            "key": session['key']
        }
    except:
        user = {
            "key": 'debuguser'
        }
    ldclient.get().identify(user)
    # logstatus = ldclient.get().variation('logMode', user, 'default')

    ############################################################################################
    #                                                                                          #
    #                                                                                          #
    #             Code for implementing a database read feature flag is below                  #
    #                                                                                          #
    #                                                                                          #
    ############################################################################################

    dbinfo = ldclient.get().variation('dbinfo', user, fallback)
    print(dbinfo)
    if dbinfo['mode'] == 'local':
        dummyData = [(
            {
                "id":1,
                "title":"Debug Ipsum 1",
                "text":"This is our debug text. Charlie ate the last candy bar."
            },
            {
                "id":2,
                "title":"Debug Ipsum 2",
                "text":"We're debugging all the Unicorns. They are trampling our code."
            },
            {
                "id":3,
                "title":"Debug Ipsum 3",
                "text":"Will it ever end? Speculation is nay. It likely won't."
            }
        )]
        return jsonify(dummyData)
    else:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('LD_Demo_Dynamo')
        data = table.get_item(Key={'teamid': '1'})
        realData = [(
            {
                "id":1,
                "title":data['Item']['title1'],
                "text":data['Item']['text1']
            },
            {
                "id":1,
                "title":data['Item']['title2'],
                "text":data['Item']['text2']
            },
            {
                "id":1,
                "title":data['Item']['title3'],
                "text":data['Item']['text3']
            }
        )]
        return jsonify(realData)

# @app.route("/teamdebug")
# def teamdebug():
#     if session['key'] != None:
#         user = {
#             "key": session['key']
#         }
#     else:
#         user = {
#             "key": "debuguser"
#         }
#     ldclient.get().identify(user)
#     logstatus = ldclient.get().variation('logMode', user, 'default')
#     if logstatus == "debug":
#         teamid = os.environ.get("TEAM_ID")
#         dynamodb = boto3.resource('dynamodb')
#         table = dynamodb.Table('GamedayDB')
#         data = table.get_item(Key={'teamid': str(teamid)})
#         teamval = {
#             "teamid": teamid,
#             "loglevel": logstatus,
#             "debugcode": data['Item']['debugcode']
#         }
#         return jsonify(teamval)
#     else:
#         data = {
#             "loglevel": logstatus,
#             "message": "Logging is currently in default mode. No debug data available. Have you checked LaunchDarkly?"
#         }
#         return jsonify(data)
   

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,OPTIONS')
    return response