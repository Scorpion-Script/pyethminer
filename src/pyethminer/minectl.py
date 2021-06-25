from pyethminer import EthminerApi
import toml
import sys

configFile = "/etc/minectl.toml"
miners = {}

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
            miners[miner["name"]] = miner
    except RuntimeError as e:
        print("Failed to parse configuration: {}".format(e))
        sys.exit(1)

def connectMiners(minerSelection):
    global miners

    if minerSelection == "all":
        for miner in miners:
            miners[miner]["api"] = EthminerApi()
            miners[miner]["api"].connect(miners[miner]["host"], miners[miner]["port"])
    else:
        if minerSelection not in miners:
            print("No such miner: {}".format(minerSelection))
            sys.exit(1)
        miners[minerSelection]["api"] = EthminerApi()
        miners[minerSelection]["api"].connect(miners[minerSelection]["host"], miners[minerSelection]["port"])

def listPools(miner):
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
  status[ml] [miner (default: all)] - Print miner status(es) (statusml is multiline)
  pause/resume [miner (default: all)] [gpu index (default: 0)] - Pauses or resumes mining on a GPU
  pools [miner (default: all)] - Lists pools
  pool [miner (default: all)] <pool index> - Sets the active pool""".format(configFile))

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

    loadConfig(configFile)

    if command == "status" or command == "statusml":
        multiLine = command == "statusml"

        connectMiners(sys.argv[2] if len(sys.argv) >= 3 else "all")

        minerStats = {}

        for minerName in miners:
            if not miners[minerName]["api"]:
                continue

            minerStats[minerName] = miners[minerName]["api"].getStats()

        for minerName in minerStats:
            stats = minerStats[minerName]

            hours, minutes = divmod(stats["runtime"], 60)
            shareStr = ":R{}".format(stats["sharesRejected"]) if stats["sharesRejected"] > 0 else ""
            if stats["sharesFailed"] > 0:
                shareStr += ":F{}".format(stats["sharesFailed"])

            hashrateStr = "\n" if multiLine else ""
            hashrateStr += "{:.2f} Mh/s".format(stats["hashrate"])

            minerNameStr = "Miner {} - ".format(minerName) if len(minerStats) > 1 else ""

            print("{}{:02d}:{:02d} A{}{} {}".format(minerNameStr, hours, minutes, stats["sharesAccepted"], shareStr, hashrateStr))

    elif command == "pause" or command == "resume":
        pause = command != "resume"

        minerSelection = None
        gpuIndex = None
        if len(sys.argv) >= 4:
            minerSelection = sys.argv[2]
            gpuIndex = int(sys.argv[3])
        elif len(sys.argv) >= 3:
            minerSelection = sys.argv[2]
            gpuIndex = 0
        else:
            minerSelection = "all"
            gpuIndex = 0

        connectMiners(minerSelection)

        for minerName in miners:
            if not miners[minerName]["api"]:
                continue

            miners[minerName]["api"].pauseGpu(gpuIndex, pause)
            print("{} GPU {} on miner {}".format("Paused" if pause else "Resumed", gpuIndex, minerName))

    elif command == "pools":
        connectMiners(sys.argv[2] if len(sys.argv) >= 3 else "all")

        for minerName in miners:
            if not miners[minerName]["api"]:
                continue

            pools, activePool = listPools(miners[minerName])
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

        connectMiners(selectedMiner)

        for minerName in miners:
            if not miners[minerName]["api"]:
                continue

            pools, activePool = listPools(miners[minerName])
            if selectedPool > (len(pools) - 1):
                print("Pool index {} out of range 0-{} for miner {}, skipping".format(selectedPool, len(pools) - 1, minerName))
                continue

            miners[minerName]["api"].setActivePool(selectedPool)
            print("Selected pool {} on miner {}".format(pools[selectedPool], minerName))
    else:
        print("Unknown command: {}".format(command))
        sys.exit(1)

if __name__ == "__main__":
    main()
    sys.exit(0)