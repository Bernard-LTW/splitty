import os

from db_models import Base
from db_manager import DBHandler
import dotenv

## Load environment variables
dotenv.load_dotenv()
db = DBHandler(os.getenv("DATABASE_URL"))#DATABASE_URL=sqlite:///data/splitty_dev.sqlite

## Create tables
Base.metadata.drop_all(db.engine)
Base.metadata.create_all(db.engine)