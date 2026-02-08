from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

SqlAlchemyBase = declarative_base()

__factory = None

def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = create_engine(conn_str,     
                           pool_size=10,    
                           max_overflow=20,  
                           pool_timeout=60,
                           pool_recycle=60)
    __factory = sessionmaker(bind=engine)

    from . import _models

    SqlAlchemyBase.metadata.create_all(engine)

def create_session() -> Session:
    global __factory
    return __factory()