#!python.exe
import site

import pika
import json
import datetime

#Create connection to Broker
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', heartbeat_interval=0))
channel = connection.channel()

channel.queue_declare(queue='Log')

def callback(ch, method, properties, body):
    jsonBody = json.loads(body)

    # Parse vars for  genLog
    if jsonBody['logType'] == "genLog":
        logFile = 'C:\\FastLab_API\\Logs\\genLog.txt'
        time = jsonBody['timeStamp']
        apiIn = jsonBody['input']
        env = jsonBody['env']
        user = jsonBody['user']
        action = jsonBody['action']
        output = jsonBody['output']
        endTime = jsonBody['endTime']

        log = "\n======================%s======================\nAPI input: %s \n environment: %s, user: %s," \
              " action: %s \nCloudshell Result:\n%s\n======================%s======================\n" % (time,
                                                                                                                 apiIn,
                                                                                                                 env,
                                                                                                                 user,
                                                                                                                 action,
                                                                                                                 output,
                                                                                                                 endTime)
        #print log
        logger(logFile, log)
    # Parse vars for apiLog
    elif jsonBody['logType'] == "apiLog":
        # Set the log file
        logFile = 'C:\\FastLab_API\\Logs\\apiLog.txt'

        time = jsonBody['timeStamp']
        env = jsonBody['env']
        user = jsonBody['user']
        action = jsonBody['action']
        status = jsonBody['status']
        statusMsg = jsonBody['statusMsg']
        log = "%s API exec -- environment: %s, user: %s, action: %s, status: %s, statusMessage: %s\n" % (time,
                                                                           env, user, action, status, statusMsg)
        print log
        logger(logFile, log)


def logger(file, msg):
    f = open(file, 'a')
    f.write(msg)
    f.close()

"""
    #post log into spark if an error has occured.
    if error == True:
        url =  "https://api.ciscospark.com/v1/messages"

        headers = {
            'authorization': "Bearer NWJiMmVlNTQtYmRmNi00ZGNlLTg3ZmMtMWYwMWRlNWQ0MGQ1NjkyYzNkNmItZGNi",
            'content-type': "application/json; charset=utf-8",
        }

        payload1 = '{"roomId": "Y2lzY29zcGFyazovL3VzL1JPT00vYWRmMzU0NDAtYmQ3NC0xMWU2LThhMzktN2QzNzFiOWY5N2U2",'
        payload2 = '"text": "%s"}' % msg
        payload = payload1 + payload2

        resp = requests.request("POST", url, headers=headers,  data=payload)
        print resp.text
"""

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,
                      queue='Log',
                      no_ack=True)

print ' [*] Waiting for messages. To exit press CTRL+C'
channel.start_consuming()
