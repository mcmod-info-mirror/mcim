import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 - 1

from prometheus_client import multiprocess

def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)

import os, shutil
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus_multiproc_dir"
if os.path.exists("/tmp/prometheus_multiproc_dir"):
    shutil.rmtree("/tmp/prometheus_multiproc_dir")
os.makedirs("/tmp/prometheus_multiproc_dir", exist_ok=True)

access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'