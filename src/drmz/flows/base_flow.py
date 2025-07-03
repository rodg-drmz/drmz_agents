import os

class BaseFlow:
    def get_config_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
