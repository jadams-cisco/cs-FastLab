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

channel.queue_declare(queue='managePool')

def callback(ch, method, properties, body):
    timeStamp = str(datetime.datetime.now())
    jsonBody = json.loads(body)

    args = [jsonBody['environment'], jsonBody['action'], jsonBody['user'], '0']
    try:
        prog = subprocess.Popen(['C:\FastLab_API\cs-FastLab\CloudShell\FastLab_CSDriver.exe'] + args,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = prog.communicate()
        endTime = str(datetime.datetime.now())
        writeGenLog("Log", "genLog", timeStamp, "ManagePool Consumer", args[0], args[1], args[2], json.dumps(output), endTime)
        print str(args)
    except Exception as e:
        log = "%s [error] Failed to execute %s: %s\n" % (timeStamp, str(jsonBody['action']), str(e))
        print log
        writeGenLog("Log", "genLog", timeStamp, "ManagePool Consumer", args[0], args[1], args[2], str(e), "na")

def writeGenLog(queue, type, timeStamp, apiIn, env, action, user, apiOut, endTime):
    # Setup body
    body = {
        "logType": type,
        "timeStamp": timeStamp,
        "input": apiIn,
        "env": env,
        "user": user,
        "action": action,
        "output": apiOut,
        "endTime": endTime
    }
    # Create connection to Broker on local host
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    # Start connection channel
    channel = connection.channel()
    # instantiate queue as Log
    channel.queue_declare(queue=queue)

    channel.basic_publish(exchange='',
                          routing_key=queue,
                          body=json.dumps(body))
    # Close connection with broker
    connection.close()


channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,
                      queue='managePool',
                      no_ack=True)

print ' [*] Waiting for messages. To exit press CTRL+C'
channel.start_consuming()
