import pandas as pd
import os
import csv
import mysql.connector

# Configurações do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'user',
    'password': 'password',
    'database': 'database'
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

    # Cria o arquivo de log
    with open(arquivo_log_caminho, 'w') as log_file:
        log_file.write("Arquivos CSV com erro na inserção de dados:\n")

    # Percorre todos os arquivos da pasta
    for arquivo in os.listdir(pasta):

        # Tenta ler o arquivo CSV e inserir dados no banco 
        try:
            # Verifica se o arquivo é um arquivo CSV
            if arquivo.endswith(".csv"):

                # Caminho completo para o arquivo CSV
                caminho_arquivo = os.path.join(pasta, arquivo)

                # Nome da tabela a ser criada (usando o nome do arquivo sem a extensão)
                nome_tabela = os.path.splitext(arquivo)[0]

                # Lê o arquivo CSV
                with open(caminho_arquivo, 'r') as csv_file:
                    csv_reader = csv.reader(csv_file)
                    header = next(csv_reader)  # Ler a primeira linha como cabeçalho

                    # Criar a tabela com base nas colunas do CSV
                    colunas = [f"{coluna} VARCHAR(255)" for coluna in header]
                    create_table_query = f"CREATE TABLE IF NOT EXISTS {nome_tabela} ({', '.join(colunas)})"
                    cursor.execute(create_table_query)

                    # Inserir os dados do CSV na tabela
                    for row in csv_reader:
                        insert_query = f"INSERT INTO {nome_tabela} VALUES {tuple(row)}"
                        cursor.execute(insert_query)

                    # Confirmar as alterações no banco de dados
                    conn.commit()
                
        except Exception as e:

            # Registrar o nome do arquivo CSV com erro no arquivo de log
                with open(arquivo_log, 'a') as log_file:
                    log_file.write(f"{arquivo}: {str(e)}\n")


    # Fecha a conexão com o banco de dados
    cursor.close()
    conn.close()

    print("Leitura de arquivos concluída!")

criar_tabelas_csv(pasta_csv_caminho, db_config, arquivo_log_caminho)	
