import sqlalchemy as db
from sqlalchemy import MetaData
from sqlalchemy.orm import Session


class DBHandler:
    def __init__(self,path):
        self.engine = db.create_engine(path, echo=False)
        self.session = Session(self.engine)
        self.metadata = MetaData()
        #print(self.metadata.tables.keys())
