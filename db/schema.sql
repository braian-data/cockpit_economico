CREATE TABLE IF NOT EXISTS dim_indicadores (
    id INT PRIMARY KEY, 
    nome_indicador VARCHAR(50) NOT NULL,
    sigla_indicador VARCHAR(15) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_sigla UNIQUE (sigla_indicador)
);


CREATE TABLE IF NOT EXISTS fato_indicadores (
    id SERIAL PRIMARY KEY,
    data_referencia DATE NOT NULL,
    indicador_id INT NOT NULL, 
    valor_indicador NUMERIC(12, 4) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_indicador FOREIGN KEY (indicador_id) REFERENCES dim_indicadores(id) ON DELETE CASCADE,
    CONSTRAINT uq_indicador_data UNIQUE (data_referencia, indicador_id),
    CONSTRAINT chk_valor_positivo CHECK (valor_indicador >= 0)
);