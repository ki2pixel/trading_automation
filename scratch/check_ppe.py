from concurrent.futures import ProcessPoolExecutor
import time
def worker():
    time.sleep(1)
executor = ProcessPoolExecutor(max_workers=2)
f1 = executor.submit(worker)
print(executor._processes)
executor.shutdown(wait=False)
