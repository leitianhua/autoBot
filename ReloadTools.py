from module_hot_loading import monitor_dir
from threading import Event

if __name__ == "__main__":
    event = Event()
    event.set()
    path = "."
    monitor_dir(path, event, __file__, interval=2, only_import_exist=False)
