import sys
import toml
import colorama
from pyethminer import EthminerApi
from pyethminer import NBMinerApi

configFile = "/etc/minectl.toml"
miners = {}

colorama.init()

def loadConfig(configFile):
    global miners

    config = None
    try:
        config = toml.load(configFile)
    except FileNotFoundError as e:
        print("Configuration file not found: {}".format(e))
        sys.exit(1)

    try:
        for miner in config["miners"]:
            miner["api"] = None
            miner["pools"] = []
            miner["activePool"] = None
            miner["connectionError"] = False
            miners[miner["name"]] = miner
    except RuntimeError as e:
        print("Failed to parse configuration: {}".format(e))
        sys.exit(1)

def connectMiners(minerSelection):
    global miners

    if minerSelection == "all":
        for miner in miners:
            if miners[miner]["api_type"] == "nbminer":
                try:
                    miners[miner]["api"] = NBMinerApi()
                    miners[miner]["api"].connect(miners[miner]["url"])
                except (OSError, RuntimeError) as e:
                    #print("Failed to connect to miner \"{}\": {}".format(miner, e))
                    miners[miner]["api"] = None
                    miners[miner]["connectionError"] = True
            elif miners[miner]["api_type"] == "ethminer":
                try:
                    miners[miner]["api"] = EthminerApi()
                    miners[miner]["api"].connect(miners[miner]["host"], miners[miner]["port"])
                except (OSError, RuntimeError) as e:
                    #print("Failed to connect to miner \"{}\": {}".format(miner, e))
                    miners[miner]["api"] = None
                    miners[miner]["connectionError"] = True
            else:
                print("Unknown miner API type: {}".format(miners[miner]["api_type"]))
                #sys.exit(1)
                miners[miner]["api"] = None
                miners[miner]["connectionError"] = True
    else:
        if minerSelection not in miners:
            print("No such miner: {}".format(minerSelection))
            sys.exit(1)
        if miners[minerSelection]["api_type"] == "nbminer":
            try:
                miners[minerSelection]["api"] = NBMinerApi()
                miners[minerSelection]["api"].connect(miners[minerSelection]["url"])
            except (OSError, RuntimeError) as e:
                #print("Failed to connect to miner \"{}\": {}".format(minerSelection, e))
                miners[minerSelection]["api"] = None
                miners[minerSelection]["connectionError"] = True
        elif miners[minerSelection]["api_type"] == "ethminer":
            try:
                miners[minerSelection]["api"] = EthminerApi()
                miners[minerSelection]["api"].connect(miners[minerSelection]["host"], miners[minerSelection]["port"])
            except (OSError, RuntimeError) as e:
                #print("Failed to connect to miner \"{}\": {}".format(minerSelection, e))
                miners[minerSelection]["api"] = None
                miners[minerSelection]["connectionError"] = True
        else:
            print("Unknown miner API type: {}".format(miners[minerSelection]["api_type"]))
            #sys.exit(1)
            miners[minerSelection]["api"] = None
            miners[minerSelection]["connectionError"] = True

def listPools(miner):
    if miner["api_type"] != "ethminer":
        return None

    pools = []
    activePool = None

    srcPools = miner["api"].getPools()
    for pool in srcPools:
        pools.append("{}://{}:{}".format(pool["scheme"], pool["host"], pool["port"]))

        if pool["active"] == True:
            activePool = pool["index"]

    return (pools, activePool)

def printPools(pools, activePool):
    i = 0
    for pool in pools:
        print("{}[{}] {}".format("* " if i == activePool else "", i, pool))
        i = i + 1

def printHelp():
    print("""minectl help
------------
Config file: {}

Commands:
  confighelp - Print an example config
  status [miner (default: all)] - Print miner status(es)
  statistics [miner (default: all)] - Print miner statistics
  pause/resume [miner (default: all)] [gpu index (default: 0)] - Pauses or resumes mining on a GPU
  pools [miner (default: all)] - Lists pools
  pool [miner (default: all)] <pool index> - Sets the active pool
  lhr [miner (default: all)] <tune> - Sets the LHR tune value for a miner""".format(configFile))

def main():
    global miners

    if len(sys.argv) < 2:
        print("Usage: {} <command> [command args]".format(sys.argv[0]))
        sys.exit(1)

    command = sys.argv[1]

    if command == "help":
        printHelp()
        return

    elif command == "confighelp":
        print("""Example config
--------------
miners = [
    { name = "local", host = "localhost", port = 3333 },
    { name = "remote", host = "10.0.0.123", port = 3333 }
]""")
        return

    elif command == "status" or command == "statistics" or command == "stats":
        loadConfig(configFile)
        connectMiners(sys.argv[2] if len(sys.argv) >= 3 else "all")

        minerStats = {}

        for minerName in miners:
            miner = miners[minerName]
            if not miner["api"]:
                if miner["connectionError"]:
                    minerStats[minerName] = None

                continue

            try:
                minerStats[minerName] = miner["api"].getStats()
            except (OSError, RuntimeError) as e:
                #print("Failed to connect to miner {}: {}".format(minerName, e))
                minerStats[minerName] = None

        minerStatsLen = len(minerStats)
        i = 0

        for minerName in minerStats:
            stats = minerStats[minerName]
            #print(stats)

            statsStr = "{}Miner {}{} - ".format(colorama.Fore.WHITE + colorama.Style.BRIGHT, minerName, colorama.Style.RESET_ALL) if minerStatsLen > 1 else ""

            if stats is not None:
                hours, minutes = divmod(stats["runtime"] / 60, 60)

                shareStr = "{}A{}{}".format(colorama.Fore.GREEN + colorama.Style.BRIGHT, stats["sharesAccepted"], colorama.Style.RESET_ALL)
                if stats["sharesRejected"] > 0:
                    shareStr += " {}R{}{}".format(colorama.Fore.YELLOW + colorama.Style.BRIGHT, stats["sharesRejected"], colorama.Style.RESET_ALL)
                if stats["sharesFailed"] > 0:
                    shareStr += " {}F{}{}".format(colorama.Fore.RED + colorama.Style.BRIGHT, stats["sharesFailed"], colorama.Style.RESET_ALL)

                multiGpu = len(stats["devices"]) > 1

                hashrateStr = ""

                if stats["sharesAccepted"] != 0:
                    if stats["sharesRejected"] != 0:
                        hashrateStr += " {}R{:.2f}%{}".format(colorama.Fore.YELLOW + colorama.Style.BRIGHT, stats["sharesRejected"] / stats["sharesAccepted"] * 100, colorama.Style.RESET_ALL)

                    if stats["sharesFailed"] != 0:
                        hashrateStr += " {}F{:.2f}%{} ".format(colorama.Fore.RED + colorama.Style.BRIGHT, stats["sharesFailed"] / stats["sharesAccepted"] * 100, colorama.Style.RESET_ALL)

                hashrateStr += "\n{}{:.2f}Mh/s{}".format(colorama.Fore.CYAN + colorama.Style.BRIGHT, stats["hashrate"], colorama.Style.RESET_ALL)

                if multiGpu:
                    hashrateStr += "  "
                    curGpu = 0
                    for dev in stats["devices"]:
                        if curGpu > 0:
                            hashrateStr += " "
                        hashrateStr += "{}{:.2f}Mh/s {}{}C{}".format(colorama.Fore.CYAN + colorama.Style.BRIGHT, dev["hashrate"], colorama.Style.RESET_ALL + colorama.Fore.RED, dev["core_temp"], colorama.Style.RESET_ALL)
                        curGpu += 1

                statsStr += "{}{:02d}:{:02d}{} {} {}".format(colorama.Fore.CYAN, round(hours), round(minutes), colorama.Style.RESET_ALL, shareStr, hashrateStr)
            else:
                statsStr += "Connection Error"


            print(statsStr)

            i += 1
            if minerStatsLen > 1 and i < minerStatsLen:
                print()

    elif command == "pause" or command == "resume":
        pause = command != "resume"

        minerSelection = "all"
        gpuIndex = -1
        if len(sys.argv) >= 4:
            minerSelection = sys.argv[2]
            gpuIndex = int(sys.argv[3])
        elif len(sys.argv) >= 3:
            minerSelection = sys.argv[2]

        loadConfig(configFile)
        connectMiners(minerSelection)

        for minerName in miners:
            miner = miners[minerName]
            if not miner["api"] or miner["api_type"] != "ethminer":
                continue

            miner["api"].pauseGpu(gpuIndex, pause)
            if gpuIndex == -1:
                print("{} all GPUs on miner {}".format("Paused" if pause else "Resumed", minerName))
            else:
                print("{} GPU {} on miner {}".format("Paused" if pause else "Resumed", gpuIndex, minerName))

    elif command == "pools":
        loadConfig(configFile)
        connectMiners(sys.argv[2] if len(sys.argv) >= 3 else "all")

        for minerName in miners:
            miner = miners[minerName]
            if not miner["api"] or miner["api_type"] != "ethminer":
                continue

            pools, activePool = listPools(miner)
            if pools is None:
                print("Failed to get pools")
                sys.exit(1)
            print("-- Miner {} --".format(minerName))
            printPools(pools, activePool)

    elif command == "pool":
        if len(sys.argv) < 3:
            print("Usage: {} {} [miner (default: all)] <pool index>".format(sys.argv[0], command))
            sys.exit(1)

        selectedMiner = None
        selectedPool = None
        if len(sys.argv) >= 4:
            selectedMiner = sys.argv[2]
            selectedPool = int(sys.argv[3])
        else:
            selectedMiner = "all"
            selectedPool = int(sys.argv[2])

        loadConfig(configFile)
        connectMiners(selectedMiner)

        for minerName in miners:
            miner = miners[minerName]
            if not miner["api"] or miner["api_type"] != "ethminer":
                continue

            pools, activePool = listPools(miner)
            if selectedPool > (len(pools) - 1):
                print("Pool index {} out of range 0-{} for miner {}, skipping".format(selectedPool, len(pools) - 1, minerName))
                continue

            miner["api"].setActivePool(selectedPool)
            print("Selected pool {} on miner {}".format(pools[selectedPool], minerName))

    elif command == "lhr":
        minerSelection = "all"
        gpuIndex = -1
        if len(sys.argv) >= 5:
            minerSelection = sys.argv[2]
            gpuIndex = int(sys.argv[3])
            tune = int(sys.argv[4])
        elif len(sys.argv) >= 4:
            minerSelection = sys.argv[2]
            tune = int(sys.argv[3])
        elif len(sys.argv) >= 3:
            tune = int(sys.argv[2])
        else:
            print("Missing argument \"tune\"")
            sys.exit(1)

        loadConfig(configFile)
        connectMiners(minerSelection)

        for minerName in miners:
            miner = miners[minerName]
            if not miner["api"] or miner["api_type"] != "ethminer":
                continue

            miner["api"].setLhrTune(gpuIndex, tune)
            if gpuIndex == -1:
                print("LHR tune set to {} for all GPUs on miner {}".format(tune, minerName))
            else:
                print("LHR tune set to {} for GPU {} on miner {}".format(tune, gpuIndex, minerName))

    else:
        print("Unknown command: {}".format(command))
        sys.exit(1)

if __name__ == "__main__":
    main()
    sys.exit(0)