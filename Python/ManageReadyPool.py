import pika
import subprocess
import json

#Create connection to Broker
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='ManagePool')

def callback(ch, method, properties, body):
    jsonBody = json.loads(body)
    args = [jsonBody['environment'], jsonBody['action'], jsonBody['user'], '0']
    try:
        prog = subprocess.Popen(['C:\\FastLab_API\\cs-FastLab\\LearningLabsLabs_EnvDriver.exe'] + args,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = prog.communicate()
        print " [x] Executed Manage Pool %r" % output
    except Exception as e:
        print str(e)


channel.basic_consume(callback,
                      queue='ManagePool',
                      no_ack=True)

print ' [*] Waiting for messages. To exit press CTRL+C'
channel.start_consuming()
