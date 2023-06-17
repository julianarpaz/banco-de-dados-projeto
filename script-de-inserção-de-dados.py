import pandas as pd
import os
import mysql.connector

# Configurações do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'seu_usuario',
    'password': 'sua_senha',
    'database': 'seu_banco_de_dados'
}

# Nome da pasta com arquivos csv
pasta_csv = 'base_de_dados'

# Nome do arquivo de log de erros
arquivo_log = "errors.log"

diretorio_atual = os.path.dirname(os.path.abspath(__file__))

pasta_csv_caminho = os.path.join(diretorio_atual, pasta_csv)

arquivo_log_caminho = os.path.join(diretorio_atual, arquivo_log)

def criar_tabelas_csv(pasta, db_config, arquivo_log):
    # Estabelece conexão com o banco de dados
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Cria o arquivo de log (caso não exista)
    with open(arquivo_log, 'w') as log_file:
        log_file.write("Arquivos CSV com erro na inserção de dados:\n")

    # Percorre todos os arquivos da pasta
    for arquivo in os.listdir(pasta):

        # Tenta ler o arquivo CSV e inserir dados no banco 
        try:
            # Verifica se o arquivo é um arquivo CSV
            if arquivo.endswith(".csv"):

                # Caminho completo para o arquivo CSV
                caminho_arquivo = os.path.join(pasta, arquivo)

                # Lê o arquivo CSV usando o pandas
                df = pd.read_csv(caminho_arquivo)

                # Nome da tabela a ser criada (usando o nome do arquivo sem a extensão)
                nome_tabela = os.path.splitext(arquivo)[0]

                # Cria a tabela no banco de dados (caso não exista)
                create_table_query = f"CREATE TABLE IF NOT EXISTS {nome_tabela} ("

                # Obtém os nomes das colunas do arquivo CSV
                colunas = df.columns.tolist()

                # Adiciona as colunas à consulta SQL de criação da tabela
                for coluna in colunas:
                    create_table_query += f"{coluna} VARCHAR(255), "

                # Remove a última vírgula e fecha a consulta SQL
                create_table_query = create_table_query[:-2] + ")"

                # Executa a consulta SQL para criar a tabela
                cursor.execute(create_table_query)

                # Insere os dados do arquivo CSV na tabela
                for linha in df.itertuples(index=False):
                    insert_query = f"INSERT INTO {nome_tabela} ({', '.join(colunas)}) VALUES {linha}"
                    cursor.execute(insert_query)
                
                # Confirma as alterações no banco de dados para cada tabela criada
                conn.commit()
                
        except Exception as e:

            # Registrar o nome do arquivo CSV com erro no arquivo de log
                with open(arquivo_log, 'a') as log_file:
                    log_file.write(f"{arquivo}: {str(e)}\n")


    # Fecha a conexão com o banco de dados
    cursor.close()
    conn.close()

    print("Leitura de arquivos concluída!")

# criar_tabelas_csv(pasta_csv_caminho, db_config, arquivo_log_caminho)
