# NBMiner REST API Client Library
# Author: Ziah Jyothi

import json
import time
import urllib.request, urllib.parse, urllib.error

class NBMinerApi:
    API_V1_PATH = "/api/v1"

    def __init__(self):
        self.url = None

    def connect(self, url="http://localhost:22333"):
        self.url = url

    def disconnect(self):
        self.url = None

    #def authorize(self, password):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "api_authorize", "params": { "psw": password }})

        #self.handleResponse(response, "Failed to authorize")

    #def ping(self):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_ping"})

        #self.handleResponse(response, "Failed to ping", "pong")

    def getStats(self):
        request = urllib.request.Request("{}{}/status".format(self.url, NBMinerApi.API_V1_PATH))
        resp = urllib.request.urlopen(request, timeout=1)
        response = json.loads(resp.read().decode(resp.info().get_param('charset') or 'utf-8'))

        #gpuHashrates = [float(i["hashrate_raw"]) / 1000000 for i in response["miner"]["devices"]]
        devices = []
        for dev in response["miner"]["devices"]:
            devices.append({
                "name": dev["info"],
                "pci_bus_id": dev["pci_bus_id"],
                "accepted_shares": dev["accepted_shares"],
                "rejected_shares": dev["rejected_shares"],
                "invalid_shares": dev["invalid_shares"],
                "hashrate": float(dev["hashrate_raw"]) / 1000000,
                "core_clock": dev["core_clock"],
                "memory_clock": dev["mem_clock"],
                "core_usage": dev["core_utilization"],
                "memory_usage": dev["mem_utilization"],
                "lhr_target": dev["lhr"],
                "core_temp": dev["temperature"],
                "mem_temp": dev["memTemperature"],
                "fan": dev["fan"],
                "power": dev["power"]
            })

        return {
            "version": response["version"],
            "runtime": int(time.time() - response["start_time"]),
            "hashrate": float(response["miner"]["total_hashrate_raw"]) / 1000000,
            "sharesAccepted": response["stratum"]["accepted_shares"],
            "sharesRejected": response["stratum"]["rejected_shares"],
            "sharesFailed": response["stratum"]["invalid_shares"],
            "devices": devices
        } #, "gpuTempFanSpeed": gpuTempFanSpeed, "activePool": response["result"][7], "poolSwitches": int(status2[1])}

    #def getDetailedStats(self):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_getstatdetail"})

        #self.handleResponse(response, "Failed to get detailed statistics", None)

        #return response["result"]

    #def restart(self):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_restart"})

        #self.handleResponse(response, "Failed to restart miner")

    #def shuffleScrambler(self):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_shuffle"})

        #self.handleResponse(response, "Failed to shuffle scramble nonce")

    #def getScramblerInfo(self):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_getscramblerinfo"})

        #self.handleResponse(response, "Failed to get scrambler info", None)

        #return response["result"]

    #def setScramblerInfo(self, nonceScrambler, segmentWidth):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_setscramblerinfo", "params": {"noncescrambler": nonceScrambler, "segmentwidth": segmentWidth}})

        #self.handleResponse(response, "Failed to set scrambler info", None)

        #return response["result"]

    #def getPools(self):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_getconnections"})

        #self.handleResponse(response, "Failed to get pools", None)

        #return response["result"]

    #def setActivePool(self, index):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_setactiveconnection", "params": { "index": index }})

        #self.handleResponse(response, "Failed to set active pool")

    #def pauseGpu(self, index, pause = True):
        #indices = []
        #if index == -1:
            #stats = self.getStats()
            #for idx in range(0, len(stats["gpuHashrates"])):
                #indices.append(idx)
        #else:
            #indices.append(index)

        #for idx in indices:
            #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_pausegpu", "params": { "index": idx, "pause": pause }})

            #self.handleResponse(response, "Failed to pause GPU {}".format(idx))

    #def setVerbosity(self, verbosity):
        #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_setverbosity", "params": { "verbosity": verbosity }})

        #self.handleResponse(response, "Failed to set verbosity")

    #def setLhrTune(self, index, tune):
        #indices = []
        #if index == -1:
            #stats = self.getStats()
            #for idx in range(0, len(stats["gpuHashrates"])):
                #indices.append(idx)
        #else:
            #indices.append(index)

        #for idx in indices:
            #response = self.sendRequest({"jsonrpc": EthminerApi.jsonApiVersion, "method": "miner_setlhrtune", "params": { "index": idx, "tune": tune}})

            #self.handleResponse(response, "Failed to set LHR tune for GPU {}".format(idx))