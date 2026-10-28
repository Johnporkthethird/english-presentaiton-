import sys, pickle, threading
sys.path.insert(0, sys.argv[1])
import rbxl
sys.setrecursionlimit(1000000)
threading.stack_size(512*1024*1024)
def go():
    p = rbxl.load(sys.argv[2])
    with open(sys.argv[3], "wb") as f: pickle.dump(p, f, protocol=5)
t = threading.Thread(target=go); t.start(); t.join()
