from crewai import CrewBase

class BaseCrew(CrewBase):
    def __init__(self):
        self.config_path = 'src/drmz/config/'
