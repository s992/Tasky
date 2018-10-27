import os
import ConfigParser


class Config:
    def __init__(self):
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.optionxform = str

        try:
            self.cfg.read(os.path.expanduser("~/.taskyrc"))
        except Exception, ex:
            return

    def get_default_filter(self):
        try:
            return self.cfg.get("Filters", "default")
        except Exception, ex:
            return ""

    def get_bind(self, key):
        try:
            return self.cfg.get("Keybinds", key)
        except Exception, ex:
            return
