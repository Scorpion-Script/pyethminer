# Ethminer JSON-RPC API Client Library
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
            self.sock.settimeout(1)
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
        #gpuHashrates = [float(i) / 1000 for i in response["result"][3].split(";")]
        #gpuTempFanSpeed = list(map(float, response["result"][6].split(";")))
        status2 = response["result"][8].split(";")

        devices = []
        gpuHashrateData = response["result"][3].split(";")
        gpuTempFanData = response["result"][6].split(";")
        for i in range(round(len(gpuTempFanData) / 2)):
            devices.append({
                #"name": dev["info"],
                #"pci_bus_id": dev["pci_bus_id"],
                #"accepted_shares": dev["accepted_shares"],
                #"rejected_shares": dev["rejected_shares"],
                #"invalid_shares": dev["invalid_shares"],
                "hashrate": float(gpuHashrateData[i]) / 1000,
                #"core_clock": dev["core_clock"],
                #"memory_clock": dev["mem_clock"],
                #"core_usage": dev["core_utilization"],
                #"memory_usage": dev["mem_utilization"],
                #"lhr_target": dev["lhr"],
                "core_temp": int(gpuTempFanData[i * 2]),
                #"mem_temp": dev["memTemperature"],
                "fan": int(gpuTempFanData[i * 2 + 1]),
                #"power": dev["power"]
            })

        return {
            "version": response["result"][0],
            "runtime": int(int(response["result"][1]) * 60),
            "hashrate": float(status1[0]) / 1000,
            "sharesAccepted": int(status1[1]),
            "sharesRejected": int(status1[2]),
            "sharesFailed": int(status2[0]),
            "devices": devices,
            #"gpuTempFanSpeed": gpuTempFanSpeed,
            "activePool": response["result"][7],
            "poolSwitches": int(status2[1])
        }

    def getDetailedStats(self):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_getstatdetail"})

        self.handleResponse(response, "Failed to get detailed statistics", None)

        return response["result"]

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
        indices = []
        if index == -1:
            stats = self.getStats()
            for idx in range(0, len(stats["gpuHashrates"])):
                indices.append(idx)
        else:
            indices.append(index)

        for idx in indices:
            response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_pausegpu", "params": { "index": idx, "pause": pause }})

            self.handleResponse(response, "Failed to pause GPU {}".format(idx))

    def setVerbosity(self, verbosity):
        response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_setverbosity", "params": { "verbosity": verbosity }})

        self.handleResponse(response, "Failed to set verbosity")

    def setLhrTune(self, index, tune):
        indices = []
        if index == -1:
            stats = self.getStats()
            for idx in range(0, len(stats["gpuHashrates"])):
                indices.append(idx)
        else:
            indices.append(index)

        for idx in indices:
            response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_setlhrtune", "params": { "index": idx, "tune": tune}})

            self.handleResponse(response, "Failed to set LHR tune for GPU {}".format(idx))