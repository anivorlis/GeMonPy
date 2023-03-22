import sys
import time
import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from settings.config import PATH_TO_DATA
from main import process_new_data

class DatabaseWatcher:
    def __init__(self, src_path):
        self.__src_path = src_path
        self.__event_handler = ExtensionHandler('.db')
        self.__event_observer = Observer()

    def run(self):
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def start(self):
        self.__schedule()
        self.__event_observer.start()

    def stop(self):
        self.__event_observer.stop()
        self.__event_observer.join()

    def __schedule(self):
        self.__event_observer.schedule(
            self.__event_handler,
            self.__src_path,
            recursive=True
        )

class ExtensionHandler(FileSystemEventHandler):

    def __init__(self, extension):
        self.extension = extension
        super().__init__()

    def on_created(self, event):
        self.process(event)

    def process(self, event):
        if event.src_path.endswith(self.extension):
            filename, ext = os.path.split(event.src_path)
            fsize = -1
            while fsize != os.path.getsize(event.src_path):
                fsize = os.path.getsize(event.src_path)
                print(fsize)
                time.sleep(0.010)
            process_new_data()

if __name__ == "__main__":
    src_path = PATH_TO_DATA
    DatabaseWatcher(src_path).run()