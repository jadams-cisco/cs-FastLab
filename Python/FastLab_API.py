#!python.exe
import site

# Created by Jacob Adams and Dan Klingler
# API which integrates with CloudShell .exe drivers to provide 'labs' to end users without logging in and 'instantly'
# Contact devnetsandbox@cisco.com with questions.
#import statements
from flask import Flask, jsonify, send_from_directory
from flask import request
from waitress import serve
import json
import subprocess
import pika
import datetime

# Declare web application instace as 'app'
app = Flask(__name__)

# API URL only accepting posts - all functions of the API work through this singular URL
@app.route('/v1', methods=['POST'])
def post():
    # Grabs current time for logging purposes
    timeStamp = str(datetime.datetime.now())

    # Parses the input data from the POST - preforms exception/error checking
    errorCondition, apiObjects, errorJSON  = inputHandler(request.data)

    # If no errors from data parsing, continue normal code
    if errorCondition == False:
        apiToken = apiObjects[0]
        apiUser = apiObjects[1]
        apiEnvironment = apiObjects[2]
        apiAction = apiObjects[3]
        apiTTL = apiObjects[4]

        # Authenticate the session given the token
        authenticated = auth(apiToken)

        # Returns error if not authenticated
        if authenticated == False:
            apiReturn = {
                "status": "error",
                "statusMessage": "Invalid API Token"
            }
            #asyncCsAutomations("log", "error", "na", "na", json.dumps(apiReturn))
            writeLog("apiLog", timeStamp, apiEnvironment, apiUser, apiAction, "error", "Invalid API token")
            return jsonify(apiReturn), 401

        # Initalize csAction object
        csApiObject = csAction(apiEnvironment, apiUser, apiTTL)
        # Trigger the automation for the csAction object by passing the the apiAction var
        apiReturn = csApiObject.triggerAction(apiAction)

        print apiReturn

        #logs the api call to API log
        try:
            if not str(apiReturn['statusMessage']):
                writeLog("apiLog", timeStamp, apiEnvironment, apiUser, apiAction, apiReturn["status"],
                         "null")
            else:
                writeLog("apiLog", timeStamp, apiEnvironment, apiUser, apiAction, apiReturn["status"],
                         apiReturn["statusMessage"])
        # This exception will catch an error if the cloudshell exe didn't return valid JSON.
        except:
            writeLog("apiLog", timeStamp, apiEnvironment, apiUser, apiAction, "CloudShell Error",
                     str(apiReturn))

        #logs the api to genLog
        try:
            writeGenLog("genLog", timeStamp, str(request.data), apiEnvironment, apiAction, apiUser, json.dumps(apiReturn),
                        str(datetime.datetime.now()))
        except Exception as e:
            writeGenLog("genLog", timeStamp, str(request.data), apiEnvironment, apiAction, apiUser, str(e),
                        str(datetime.datetime.now()))

        # Runs async process for managing the ready pool of systems.
        if apiAction == "request" or "terminate":
            asyncCsAutomations("managePool", apiEnvironment, "managePool", "adminWorker")

        # Returns the output of the API to the enduser if CS ran sucessfully
        try:
            return jsonify(apiReturn)
        # retuns error  response if CS fails to return JSON
        except:
            resp = {
                "status": "fail",
                "statusMessage": "Cloudshell has encountered a fatal error",
                "actionResult": str(apiReturn)
            }
            return jsonify(resp), 400
    # If parsing has returned an error, return the client the error.
    else:
        # logs the api call
        #asyncCsAutomations("log", "error", "na", "na", json.dumps(errorJSON))
        return jsonify(errorJSON), 400

@app.route('/apiLog', methods=['GET', 'POST'])
def apiLog():
    return send_from_directory(directory="C:\\FastLab_API\\Logs", filename="apiLog.txt")

@app.route('/genLog', methods=['GET', 'POST'])
def genLog():
    return send_from_directory(directory="C:\\FastLab_API\\Logs", filename="genLog.txt")

@app.route('/asyncLog', methods=['GET', 'POST'])
def asyncLog():
    return send_from_directory(directory="C:\\FastLab_API\\Logs", filename="asyncLog.txt")

# Extracts data from input body, handles data errors and exceptions.
def inputHandler(apiBody):
    # declare vars
    errorCondition = False
    statusMessage =["", "", ""]
    finalStatusMessage = ""
    inputJSON = ""
    apiObjects = ["", "", "", "", ""]
    apiMissingElements = []
    apiErrorObjects = []
    #Checks to see if the body of JSON input is valid
    try:
        inputJSON = json.loads(apiBody)
    except Exception as e:
        errorCondition = True
        statusMessage[0] = "The supplied JSON is invalid"

    # Loops through all elements, all valid elements are loaded into apiObjects
    # All invalid elements are loaded into apiErrorObjects and raises the errorCondition to true
    for i in inputJSON:
        if i == "token":
            apiObjects[0] = inputJSON[i]
        elif i == "user":
            apiObjects[1] = inputJSON[i]
        elif i == "environment":
            apiObjects[2] = inputJSON[i]
        elif i == "action":
            apiObjects[3] = inputJSON[i]
        elif i == "TTL":
            apiObjects[4] = inputJSON[i]
        else:
            errorCondition = True
            statusMessage[1] = "The following element(s) in the request body are invalid: "
            apiErrorObjects.append(json.dumps(i))

    # TTL is optional, if TTL is not found, it is set to 0 in apiObjects
    if 'TTL' not in inputJSON:
        apiObjects[4] = "0"

    # iterates apiObjects to look for empty required list items.
    for i in xrange(len(apiObjects)):
        if apiObjects[i] == "":
            errorCondition = True
            statusMessage[2] = "The following element(s) are reqired in the request body: "
            if i == 0:
                apiMissingElements.append('token')
            elif i == 1:
                apiMissingElements.append('user')
            elif i == 2:
                apiMissingElements.append('environment')
            elif i == 3:
                apiMissingElements.append('action')
            else:
                pass

    for i in statusMessage:
        if i != "":
            if i == statusMessage[0]:
                finalStatusMessage += str(statusMessage[0])
                break
            elif i == statusMessage[1]:
                finalStatusMessage += "%s %s " % (str(statusMessage[1]), str(apiErrorObjects))
            elif i == statusMessage[2]:
                finalStatusMessage += "%s %s" % (str(statusMessage[2]), str(apiMissingElements))

    errorJSON = {
        "status": "error",
        "statusMessage": finalStatusMessage,
        "minsToReady": "",
        "actionResult": ""
    }

    return errorCondition, apiObjects, errorJSON

# Authenticates the session
def auth(apiToken):
    #opens and reads file containing auth key and retrieves it for auth
    f = open('C:\\FastLab_API\\auth.txt', 'r')
    metaData = json.loads(f.read())
    authToken = metaData['auth']
    f.close()

    authenticated = False


    for i in authToken:
        if apiToken == i['token']:
            authenticated = True
        else:
            pass

    return authenticated

# Sends a message to the broker to manage the ReadyPool for the given lab.
def asyncCsAutomations(queue, env, action, user):
    # Setup body
    body = {
        "environment": env,
        "action": action,
        "user": user
    }
    # Create connection to Broker on local host
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    # Start connection channel
    channel = connection.channel()
    # instantiate queue as ManagePool
    channel.queue_declare(queue=queue)

    channel.basic_publish(exchange='',
                          routing_key=queue,
                          body=json.dumps(body))
    # Close connection with broker
    connection.close()

#writes the log in an asynchronous thread
def writeLog(type, timeStamp, env, user, action, status, statusMsg):
    # Setup body
    body = {
        "logType": type,
        "timeStamp": timeStamp,
        "env": env,
        "user": user,
        "action": action,
        "status": status,
        "statusMsg": statusMsg
    }
    # Create connection to Broker on local host
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    # Start connection channel
    channel = connection.channel()
    # instantiate queue as Log
    channel.queue_declare(queue='Log')

    channel.basic_publish(exchange='',
                          routing_key='Log',
                          body=json.dumps(body))
    # Close connection with broker
    connection.close()

def writeGenLog(type, timeStamp, apiIn, env, action, user, apiOut, endTime):
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
    channel.queue_declare(queue='Log')

    channel.basic_publish(exchange='',
                          routing_key='Log',
                          body=json.dumps(body))
    # Close connection with broker
    connection.close()

"""
Handles communication with CloudShell to kick off automations.
Returns a JSON body with the proper result of the called action
"""
class csAction(object):
    # Istantiate a csAction object
    def __init__(self, environment, username, TTL):
        # Returns a new csAction objec
        self.environment = environment
        self.username = username
        self.TTL = TTL

    # Takes the action and runs the appropriate method for CS automation.
    def triggerAction(self, action):
        # Initialize vars
        args = [self.environment, action, self.username, self.TTL]
        if action == "terminate":
            asyncCsAutomations("Terminate", self.environment, action, self.username)
            output = {
                "status": "success",
                "minsToReady": "",
                "actionResult": "",
                "statusMessage": "System session associated with user %s has been terminated." % self.username
            }
            return output
        else:
            try:
                prog = subprocess.Popen(['C:\FastLab_API\cs-FastLab\CloudShell\FastLab_CSDriver.exe'] + args,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, error = prog.communicate()
                jsonResp = json.loads(output)
                return jsonResp
            except Exception as e:
                csError = str(e)
                output = {
                    "status": "error",
                    "statusMessage": csError,
                    "actionResult": ""
                }
                return output



# Runs the web application with waitress
if __name__ == "__main__":
    serve(app, listen="*:80", threads='45')
