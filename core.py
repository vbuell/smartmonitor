class Singleton(object):
    obj = None
    def __new__(cls,*dt,**mp):
        if cls.obj is None:
            cls.obj = object.__new__(cls,*dt,**mp)
            cls.obj.__soft_init__()
        return cls.obj


class SmartMonContext(Singleton):

    def __soft_init__(self):
        self.command_line_arguments = None
        self.monitor_name = None
        self.state_variables = None
        self.datastore_directory = "./data"
        pass
