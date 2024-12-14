
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 8 + 1
worker_class = "uvicorn.workers.UvicornWorker"
preload_app = True
timeout = 200  # Modify as needed

# Uvicorn specific settings
uvicorn_config = {
    "interface": "asgi3",  # Ensuring that Uvicorn uses ASGI3 interface
    "loop": "auto",
    "http": "auto"
}

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")