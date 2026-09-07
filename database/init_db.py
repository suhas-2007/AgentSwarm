from database.connection import Base, engine
from database import models


def init_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("DATABASE TABLES RESET AND CREATED SUCCESSFULLY")


if __name__ == "__main__":
    init_database()