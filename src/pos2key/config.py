import tomli

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Config(metaclass=Singleton):
    def __init__(self, entry: dict=None):
        if entry is not None:
            self.settings = entry
        else:
            with open("config.toml", "rb") as f:
                toml_dict = tomli.load(f)
            self.settings = toml_dict

    # def __set__(self, key, value):
    #     self.settings[]

    def get(self, key, default=None):
        return self.settings.get(key, default)