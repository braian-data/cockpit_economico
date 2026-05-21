
# Cockpit Econômico Brasil

Projeto prático de Engenharia de Dados e BI com foco na extração, limpeza e armazenamento de indicadores macroeconômicos do Banco Central do Brasil (SGS/Bacen). O objetivo é manter uma base relacional atualizada para consumo em dashboards.

##  Tecnologias Utilizadas
- **Python:** Pandas, Requests, SQLAlchemy
- **Banco de Dados:** PostgreSQL
- **Infraestrutura:** Docker e Docker Compose

##  Funcionalidades e Soluções
* **Modelagem Relacional (Star Schema):** Separação estrutural entre metadados (`dim_indicadores`) e séries temporais (`fato_indicadores`) para garantir a integridade referencial.
* **Carga Idempotente (Upsert):** Utilização da cláusula `ON CONFLICT` no banco de dados. O pipeline pode ser executado múltiplas vezes sem risco de duplicidade de registros.
* **Contêinerização:** Isolamento do banco de dados e do motor de ingestão via Docker, padronizando o ambiente de execução.
* **Resiliência de Rede:** Implementação de cabeçalhos de navegador (User-Agent) para contornar bloqueios de segurança (WAF) da API governamental, além de um sistema de *retry* automático e expansão de *timeout* para mitigar instabilidades nos servidores do Banco Central.

## Como Executar
1. Clone o repositório.
2. Crie um arquivo `.env` na raiz do projeto contendo as credenciais: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`.
3. Execute os comandos de orquestração:
   ```bash
   docker compose down -v
   docker compose build --no-cache
   docker compose run --rm pipeline