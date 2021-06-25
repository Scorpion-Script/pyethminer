#!/usr/bin/env python3

from pyethminer import EthminerApi
import toml
import argparse
import sys

class MineCtl(object):
    commands = ["help", "pause", "resume", "pools", "pool"]

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Control ethminer via API",
            usage='''minectl [-h] [-c CONFIG] <command> [args]
            
Valid commands:
    pause/resume [miner (default: all)] [gpu index (default: 0)] - Pauses or resumes mining on a GPU
    pools [miner (default: all)] - Lists pools
    pool [miner (default: all)] <pool index> - Sets the active pool
''')
        parser.add_argument("command", help="Subcommand to run")
        parser.add_argument("-c", "--config", help="path to config file (default: /etc/minectl.toml)", default="/etc/minectl.toml")
        args = parser.parse_args(sys.argv[1:2])

        loadConfig(args.config)

        if not hasattr(self, args.command):
            print 'Unrecognized command'
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def loadConfig(self, configFile):
        global miners

        config = toml.load(configFile)

        if "miners" not in config:
            print("Failed to parse config: unable to find miners list")
            sys.exit(1)

        for miner in config["miners"]:
            miner["api"] = None
            miner["pools"] = []
            miner["activePool"] = None
            miners[miner["name"]] = miner

    def connectMiners(self, minerSelection):
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

    def listPools(self, miner):
        pools = []
        activePool = None

        srcPools = miner["api"].getPools()
        for pool in srcPools:
            pools.append("{}://{}:{}".format(pool["scheme"], pool["host"], pool["port"]))

            if pool["active"] == True:
                activePool = pool["index"]

        return (pools, activePool)

    def printPools(self, pools, activePool):
        i = 0
        for pool in pools:
            print("{}[{}] {}".format("* " if i == activePool else "", i, pool))
            i = i + 1

    def pauseOrResume(pause):
        parser = argparse.ArgumentParser(
            description="{} miner GPU".format("Pause" if pause else "Resume"))
        parser.add_argument("miner", nargs='?', default="all", help="Miner name to {}".format("pause" if pause else "resume"))
        parser.add_argument("gpu", type=int, nargs='?', default=0, help="Gpu index to {}".format("pause" if pause else "resume"))

        args = parser.parse_args(sys.argv[2:])

        #minerSelection = None
        #gpuIndex = None
        #if len(sys.argv) >= 4:
            #minerSelection = sys.argv[2]
            #gpuIndex = int(sys.argv[3])
        #elif len(sys.argv) >= 3:
            #minerSelection = sys.argv[2]
            #gpuIndex = 0
        #else:
            #minerSelection = "all"
            #gpuIndex = 0

        connectMiners(args.miner)

        for minerName in miners:
            if not miners[minerName]["api"]:
                continue

            miners[minerName]["api"].pauseGpu(args.gpu, pause)
            print("{} GPU {} on miner {}".format("Paused" if pause else "Resumed", args.gpu, minerName))

    def pause(self):
        pauseOrResume(True)

    def resume(self):
        pauseOrResume(False)

    def pools(self):
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