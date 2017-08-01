# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
import logging

from flask import Flask
from flask import render_template
import datetime, pymongo, os

app = Flask(__name__)

username = os.environ.get('mongo_user') or None
password = os.environ.get('mongo_pass') or None
credential =''
if (username is not None) and (password is not None): 
  credential=username+":"+password+"@"
shard0="box1-shard-00-00-kkflw.mongodb.net:27017"
shard1="box1-shard-00-01-kkflw.mongodb.net:27017"
shard2="box1-shard-00-02-kkflw.mongodb.net:27017"
client = pymongo.MongoClient('mongodb://'+credential+shard0+','+shard1+','+shard2+'/speedtest?ssl=true&replicaSet=Box1-shard-0&authSource=admin')
# ret = col.find({},{"_id":0,"timestamp":1,"download":1,"upload":1}).sort("timestamp", direction=1)

start_date=datetime.datetime(year=2017,month=1,day=1)

@app.route('/')
def index():
    col = client.speedtest.get_collection('speedtests')
    ret = col.aggregate([{"$match": {"_id" : {"$gt": start_date}}},
      {"$group": {
          "_id": {
            "year" : {"$year" : "$_id"},
            "month" : {"$month" : "$_id"},
            "day" : {"$dayOfMonth" : "$_id"},
            "hour": {"$hour" : "$_id"},
            "minutes" : {"$minute":"$_id"},
            "seconds": {"$second" : "$_id"}
          },
          # "download_min":{"$min": {"$multiply": [1.25e-7, "$download"]}},
          # "download_max":{"$max": {"$multiply": [1.25e-7, "$download"]}},
          "download_avg":{"$avg": {"$multiply": [1.25e-7, "$download"]}},
          # "upload_min":{"$min": {"$multiply": [1.25e-7, "$upload"]}},
          # "upload_max":{"$max": {"$multiply": [1.25e-7, "$upload"]}},
          "upload_avg":{"$avg" : {"$multiply": [1.25e-7, "$upload"]}},
          "count":{"$sum":1}
          }
      },
       {"$sort": {"_id.year":-1,"_id.month":-1,"_id.day":-1}}
    ])
    data = dict()
    data['type']="full"
    data['HOSTNAME']=os.environ.get('HOSTNAME', '??')
    data['data']=list(ret)
    return render_template('chart.html', data=data)

@app.route('/daily')
def daily():
    col = client.speedtest.get_collection('speedtests')
    ret = col.aggregate([{"$match": {"_id" : {"$gt": start_date}}},
      {"$group": {
         "_id": {
            "year" : {"$year" : "$_id"},
            "month" : {"$month" : "$_id"},
            "day" : {"$dayOfMonth" : "$_id"},
            "dayOfYear" : {"$dayOfYear" : "$_id"}
            # "hour": {"$multiply": [0,{"$hour" : "$_id"}]},
            # "minutes" : {"$multiply": [0, {"$minute":"$_id"}]},
            # "seconds": {"$multiply": [0, {"$second" : "$_id"}]}
          },
          "download_min":{"$min": {"$multiply": [1.25e-7, "$download"]}},
          "download_max":{"$max": {"$multiply": [1.25e-7, "$download"]}},
          "download_avg":{"$avg": {"$multiply": [1.25e-7, "$download"]}},
          "upload_min":{"$min": {"$multiply": [1.25e-7, "$upload"]}},
          "upload_max":{"$max": {"$multiply": [1.25e-7, "$upload"]}},
          "upload_avg":{"$avg": {"$multiply": [1.25e-7, "$upload"]}},
          "count":{"$sum":1}
          }},
       {"$sort": {"_id.dayOfYear":-1}}
    ])
    data = dict()
    data['type']=str("daily")
    data['HOSTNAME']=os.environ.get('HOSTNAME', '??')
    data['data']=list(ret)
    return render_template('chart.html', data=data)

@app.route('/hourly')
def hourly():
    col = client.speedtest.get_collection('speedtests')
    ret = col.aggregate([{"$match": {"_id" : {"$gt": start_date}}},
      {"$group": {
          "_id": {
            "hourly": {"$hour" : "$_id"}
          },
          "download_avg":{"$push":{"$multiply": [1.25e-7,"$download"]}},
          "upload_avg":{"$push":{"$multiply": [1.25e-7,"$upload"]}},
          "count":{"$sum":1}
          }
      },
       {"$sort": {"_id.year":-1,"_id.month":-1,"_id.day":-1}}
      ])
    data = dict()
    data['type']=str("hourly")
    data['HOSTNAME']=os.environ.get('HOSTNAME', '??')
    data['data']=list(ret)
    for d in data['data']:
      d['download_avg'] = [ [int(d['_id']['hourly']), float("{}".format(x))] for x in d['download_avg']]

    return render_template('chart_.html', data=data)

@app.route('/weekly')
def weekly():
    col = client.speedtest.get_collection('speedtests')
    ret = col.aggregate([{"$match": {"_id" : {"$gt": start_date}}},
      {"$group": {
          "_id": {
            "dayOfWeek": {"$dayOfWeek" : "$_id"}
          },
          "download_avg":{"$avg":{"$multiply": [1.25e-7,"$download"]}},
          "upload_avg":{"$avg":{"$multiply": [1.25e-7,"$upload"]}},
          "count":{"$sum":1}
          }
      },
      {"$sort": {"_id.dayOfWeek":-1}}
      ])
    data = dict()
    data['type']=str("dayOfWeek")
    data['HOSTNAME']=os.environ.get('HOSTNAME', '??')
    data['data']=list(ret)
    return render_template('chart_.html', data=data)

@app.route("/_env")
def get_env():

  html=""
  for i in os.environ.items():
    html = html + "<div><code>{}</code></div>".format(i)
  html = "<div>"+html+"</div>"
  title = "<h1>[~.1 ~]</h1>"

  return title+html

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.


    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000), debug=True)
# [END app]
