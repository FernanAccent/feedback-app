import sqlalchemy
import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
 
# Initialize Cloud SQL Connector
#connector = Connector()
 
def getconn():
    conn = psycopg2.connect(
        host= os.getenv("ALLOYDB_LOCALHOST"),  # The AlloyDB proxy is running locally
        port=os.getenv("ALLOYDB_PORT"),       # Default port for the AlloyDB Proxy
        dbname=os.getenv("ALLOYDB_DATABASE"),  # Your AlloyDB database name
        user=os.getenv("ALLOYDB_USER"),  # Your AlloyDB database user
        password=os.getenv("ALLOYDB_PASSWORD")  # Your AlloyDB database password
    )
    return conn



# Construct the database URI using environment variables
DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('ALLOYDB_USER')}:{os.getenv('ALLOYDB_PASSWORD')}"
    f"@{os.getenv('ALLOYDB_LOCALHOST')}:{os.getenv('ALLOYDB_PORT')}/{os.getenv('ALLOYDB_DATABASE')}"
)

# Use the SQLAlchemy engine with psycopg2
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()
 