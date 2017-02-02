#!python.exe
import site

import pika
import subprocess
import json
import datetime
import requests

#Create connection to Broker
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', heartbeat_interval=0))
channel = connection.channel()

channel.queue_declare(queue='ManagePool')

def callback(ch, method, properties, body):
    jsonBody = json.loads(body)

    if jsonBody['type'] == "execute":
        logFile = 'C:\\FastLab_API\\Logs\\asyncLog.txt'
        args = [jsonBody['environment'], jsonBody['action'], jsonBody['user'], '0']
        try:
            prog = subprocess.Popen(['C:\\FastLab_API\\cs-FastLab\\CloudShell\\LearningLabsLabs_EnvDriver.exe'] + args,
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = prog.communicate()
            log = "%s [x] Executed %s: %s\n" % (str(datetime.datetime.now()), str(jsonBody['action']), str(output))
            print log
            logger(logFile, log, False)
        except Exception as e:
            log = "%s [error] Failed to execute %s: %s\n" % (str(datetime.datetime.now()), str(jsonBody['action']), str(e))
            print log
            logger(logFile, log, True)
        else:
            pass
def logger(file, msg, error):
    f = open(file, 'a')
    f.write(msg)
    f.close()


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

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,
                      queue='ManagePool',
                      no_ack=True)

print ' [*] Waiting for messages. To exit press CTRL+C'
channel.start_consuming()
