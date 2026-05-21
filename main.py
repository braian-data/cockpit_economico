import os
import logging
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class DatabaseManager:
    
    def __init__(self):
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.db_name = os.getenv("DB_NAME")
        
        
        self.connection_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        self.engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def inicializar_banco(self):
        
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if not os.path.exists(schema_path):
                logger.error("Arquivo schema.sql não encontrado na raiz.")
                return

            with open(schema_path, 'r') as file:
                sql_script = file.read()

            with self.engine.begin() as conn:
                conn.execute(text(sql_script))
            logger.info("Fase 1 concluída: Tabelas dim_indicadores e fato_indicadores verificadas/criadas.")
        except Exception as e:
            logger.error(f"Falha crítica na inicialização do banco de dados: {e}")
            raise e

if __name__ == "__main__":
    logger.info("Iniciando validação do motor de ingestão...")
    db = DatabaseManager()
    db.inicializar_banco()