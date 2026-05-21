import os
import time
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
                logger.error("Arquivo schema.sql nao encontrado.")
                return

            with open(schema_path, 'r') as file:
                sql_script = file.read()

            with self.engine.begin() as conn:
                conn.execute(text(sql_script))
            logger.info("Banco inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar o banco: {e}")
            raise e

class BancoCentralExtractor:
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.api_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/{n}?formato=json"

    def popular_dimensao_indicadores(self, id_indicador: int, nome: str, sigla: str):
        query_dim = text("""
            INSERT INTO dim_indicadores (id, nome_indicador, sigla_indicador)
            VALUES (:id, :nome, :sigla)
            ON CONFLICT (id) DO NOTHING;
        """)
        with self.db.engine.begin() as conn:
            conn.execute(query_dim, {"id": id_indicador, "nome": nome, "sigla": sigla})
        logger.info(f"Dimensao atualizada: {sigla}")

    def extrair_e_carregar(self, codigo_indicador: int, ultimos_n_registros: int = 15, max_tentativas: int = 3):
        url = self.api_url.format(codigo=codigo_indicador, n=ultimos_n_registros)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        resposta = None
        for tentativa in range(1, max_tentativas + 1):
            try:
                logger.info(f"Buscando {ultimos_n_registros} ultimos registros da API (Indicador {codigo_indicador}) - Tentativa {tentativa}/{max_tentativas}...")
                
                # TIMEOUT EXPANDIDO PARA 45 SEGUNDOS
                resposta = requests.get(url, headers=headers, timeout=45)
                resposta.raise_for_status() 
                break 
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Falha de rede na tentativa {tentativa}: {e}")
                if tentativa == max_tentativas:
                    logger.error(f"Erro fatal apos {max_tentativas} tentativas de conexao com BCB.")
                    return
                time.sleep(3) # Delay antes de tentar novamente

        try:
            dados_brutos = resposta.json()
            df = pd.DataFrame(dados_brutos)
            
            df['data_referencia'] = pd.to_datetime(df['data'], format='%d/%m/%Y').dt.date
            df['valor_indicador'] = pd.to_numeric(df['valor'])
            df['indicador_id'] = codigo_indicador

            df = df[['data_referencia', 'indicador_id', 'valor_indicador']].dropna()

            query_fato = text("""
                INSERT INTO fato_indicadores (data_referencia, indicador_id, valor_indicador)
                VALUES (:data_referencia, :indicador_id, :valor_indicador)
                ON CONFLICT (data_referencia, indicador_id) 
                DO UPDATE SET 
                    valor_indicador = EXCLUDED.valor_indicador,
                    criado_em = CURRENT_TIMESTAMP;
            """)

            registros_carregados = 0
            with self.db.engine.begin() as conn:
                for _, row in df.iterrows():
                    conn.execute(query_fato, {
                        "data_referencia": row['data_referencia'],
                        "indicador_id": row['indicador_id'],
                        "valor_indicador": row['valor_indicador']
                    })
                    registros_carregados += 1

            logger.info(f"Carga finalizada. {registros_carregados} registros processados.")

        except Exception as e:
            logger.error(f"Erro no processamento dos dados do indicador {codigo_indicador}: {e}")

if __name__ == "__main__":
    logger.info("Iniciando pipeline do Cockpit Economico...")
    
    db_manager = DatabaseManager()
    db_manager.inicializar_banco()

    extractor = BancoCentralExtractor(db_manager)
    
    extractor.popular_dimensao_indicadores(id_indicador=11, nome="Taxa Selic Diária", sigla="SELIC")
    extractor.extrair_e_carregar(codigo_indicador=11, ultimos_n_registros=15)
