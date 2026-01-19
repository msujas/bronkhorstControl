class Verbose():
    def __init__(self, level:int):
        self.level = level
    def print(self, *args, plevel:int = 0, **kwargs):
        if self.level >= plevel:
            print(*args, **kwargs)