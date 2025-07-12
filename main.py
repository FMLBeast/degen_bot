from multiprocessing import Process
from listeners.eth_listener import run as eth_run

if __name__=='__main__':
    targets=[eth_run]
    procs=[]
    for t in targets:
        p=Process(target=t); p.daemon=True; p.start(); procs.append(p)
    for p in procs: p.join()
