# Ethminer JSON-RPC API Client Library
# Version: 0.2.0
# Author: Ziah Jyothi

import socket
import fcntl, os
import json
import time

class EthminerApi:
    jsonApiVersion = "2.0"

    def __init__(self):
        self.debug = False
        self.sock = None
        self.connected = False
        self.lastConnected = 0
        self.nextRequestId = 0
    def __del__(self):
        self.disconnect()

    def connect(self, host = "localhost", port = 3333):
        self.connected = False
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            self.sock.connect((host, port))
            self.sock.settimeout(None)

            fcntl.fcntl(self.sock, fcntl.F_SETFL, os.O_NONBLOCK)
        except OSError as e:
            self.onDisconnect()
            raise e

        self.connected = True
        self.onConnect()

    def disconnect(self):
        self.onDisconnect()

    def onConnect(self):
        if self.debug:
            print("Miner connected: {}".format(self.sock))
        self.lastConnected = 0

    def onDisconnect(self):
        if self.sock:
            self.sock.close()

        if self.connected:
            self.connected = False

            if self.debug:
                print("Miner disconnected: {}".format(self.sock))

            self.lastConnected = time.time()
        elif self.debug:
            print("Miner connection failed again: {}".format(self.sock))

    def sendRequest(self, request):
        if not self.connected or not self.sock:
            raise RuntimeError("Unable to send request when disconnected")

        request["id"] = self.nextRequestId
        self.nextRequestId = self.nextRequestId + 1

        if self.debug:
            print("Sending: {}".format(request))

        requestStr = json.dumps(request)
        try:
            self.sock.sendall(requestStr.encode("utf-8") + b"\n")
        except ConnectionError:
            self.onDisconnect()
            raise

        response = b""
        bytesReceived = 0
        timeout = time.time() + 1

        while time.time() < timeout:
            try:
                response += self.sock.recv(1024)
            except BlockingIOError:
                time.sleep(10 / 1000)
                continue
            except ConnectionError:
                self.onDisconnect()
                raise
            else:
                bytesReceived += len(response)

                if b"\n" in response:
                    response = response.strip()

                    response = json.loads(response)

                    if self.debug:
                        print("Response: {}".format(response))

                    if response["id"] == request["id"]:
                        return response
                    else:
                        print("Warning: response doesn't have same ID as request {} != {}, waiting for another response...".format(response["id"], request["id"]))

    def handleResponse(self, response, errMsg = "", expectedResponse = True):
        if not response:
            raise RuntimeError(errMsg)
        elif "error" in response:
            raise RuntimeError("{} ({}): {}".format(errMsg, response["error"]["code"], response["error"]["message"]))
        elif "result" not in response:
            raise RuntimeError("{}: invalid response, missing result".format(errMsg))
        elif expectedResponse != None and response["result"] != expectedResponse:
            raise RuntimeError("{}: invalid response, unexpected result: {} != {}".format(errMsg, response["result"], expectedResponse))

    def authorize(self, password):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "api_authorize", "params": { "psw": password }})

        self.handleResponse(response, "Failed to authorize")

    def ping(self):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_ping"})

        self.handleResponse(response, "Failed to ping", "pong")

    def getStats(self):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_getstat1"})

        self.handleResponse(response, "Failed to get statistics", None)

        status1 = response["result"][2].split(";")
        gpuHashrates = [int(i) / 1000 for i in list(map(int, response["result"][3].split(";")))]
        gpuTempFanSpeed = list(map(int, response["result"][6].split(";")))
        status2 = response["result"][8].split(";")

        return {"version": response["result"][0], "runtime": int(response["result"][1]), "hashrate": int(status1[0]) / 1000, "sharesAccepted": int(status1[1]), "sharedRejected": int(status1[2]), "sharesFailed": int(status2[0]), "gpuHashrates": gpuHashrates, "gpuTempFanSpeed": gpuTempFanSpeed, "activePool": response["result"][7], "poolSwitches": int(status2[1])}

    def restart(self):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_restart"})

        self.handleResponse(response, "Failed to restart miner")

    def shuffleScrambler(self):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_shuffle"})

        self.handleResponse(response, "Failed to shuffle scramble nonce")

    def getScramblerInfo(self):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_getscramblerinfo"})

        self.handleResponse(response, "Failed to get scrambler info", None)

        return response["result"]

    def setScramblerInfo(self, nonceScrambler, segmentWidth):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_setscramblerinfo", "params": {"noncescrambler": nonceScrambler, "segmentwidth": segmentWidth}})

        self.handleResponse(response, "Failed to set scrambler info", None)

        return response["result"]

    def getPools(self):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_getconnections"})

        self.handleResponse(response, "Failed to get pools", None)

        return response["result"]

    def setActivePool(self, index):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_setactiveconnection", "params": { "index": index }})

        self.handleResponse(response, "Failed to set active pool")

    def pauseGpu(self, index, pause = True):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_pausegpu", "params": { "index": index, "pause": pause }})

        self.handleResponse(response, "Failed to pause GPU")

    def setVerbosity(self, verbosity):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_setverbosity", "params": { "verbosity": verbosity }})

        self.handleResponse(response, "Failed to set verbosity")