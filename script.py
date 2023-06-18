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

def criar_tabela(tabela_sql, db_config):

    # Configurar a conexão com o banco de dados
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Executar a consulta SQL para criar a tabela
    cursor.execute(tabela_sql)
    connection.commit()
    print(f"Tabela{tabela_sql} criada com sucesso!")

    # Fechar a conexão com o banco de dados
    cursor.close()
    connection.close()

# Tabelas 
tabela_funcionarios = '''
CREATE TABLE funcionarios (
    ID_Funcionario int PRIMARY KEY,
    Sobrenome varchar(20) NOT NULL,
    Nome varchar(10) NOT NULL,
    Cargo varchar(30),
    Titulo varchar(25),
    Endereco varchar(60),
    Cidade varchar(15),
    Pais varchar(15),
    Telefone varchar(24)
);
'''
tabela_categorias = '''
CREATE TABLE categorias (
    ID_Categoria int PRIMARY KEY,
    Nome_Categoria varchar(15) NOT NULL,
    Descricao longtext
);
'''

tabela_clientes = '''
CREATE TABLE clientes (
    ID_Cliente char(10) PRIMARY KEY NOT NULL,
    Nome_Empresa varchar(40) NOT NULL,
    Representante_Empresa varchar(30),
    Cargo_Representante varchar(50),
    Endereco varchar(60),
    Cidade varchar(15),
    Pais varchar(15),
    Telefone varchar(24)
);
'''

tabela_compras = '''
CREATE TABLE compras (
    ID_Compra int PRIMARY KEY NOT NULL,
    ID_Cliente char(5),
    ID_Funcionario int,
    Data_Venda datetime,
    Frete decimal(10,2) DEFAULT 0,
    FOREIGN KEY (ID_Cliente) REFERENCES clientes(ID_Cliente),
    FOREIGN KEY (ID_Funcionario) REFERENCES funcionarios(ID_Funcionario)
);
'''

tabela_produtos = '''
CREATE TABLE produtos (
    ID_Produto int PRIMARY KEY,
    Nome_Produto varchar(40) NOT NULL,
    ID_Categoria int,
    Preco_Unitario decimal(19,4) DEFAULT 0,
    Unidades_em_Estoque smallint DEFAULT 0,
    Descontinuados bit NOT NULL DEFAULT b'0',
    FOREIGN KEY (ID_Categoria) REFERENCES categorias(ID_Categoria),
    CONSTRAINT CK_produtos_preco_unitario CHECK (Preco_Unitario >= 0),
    CONSTRAINT CK_Unidades_em_Estoque CHECK (Unidades_em_Estoque >= 0)
);
'''

tabela_detalhamento_compra ='''
CREATE TABLE detalhamento_compra (
    ID_Compra int NOT NULL,
    ID_Produto int NOT NULL,
    Preco_Unitario decimal(10,2) NOT NULL DEFAULT 0,
    Quantidade smallint NOT NULL DEFAULT 1,
    Desconto float NOT NULL DEFAULT 0,
    CONSTRAINT PK_detalhamento_compra PRIMARY KEY (ID_Compra, ID_Produto),
    FOREIGN KEY (ID_Compra) REFERENCES compras(ID_Compra),
    FOREIGN KEY (ID_Produto) REFERENCES produtos(ID_Produto),
    CONSTRAINT CK_Desconto CHECK (Desconto >= 0 AND Desconto <= 1),
    CONSTRAINT CK_Quantidade CHECK (Quantidade > 0),
    CONSTRAINT CK_Preco_Unitario CHECK (Preco_Unitario >= 0)
);
'''

# Cria o arquivo de log
with open(arquivo_log, 'w') as log_arquivo:
    log_arquivo.write("Arquivos CSV com erro na insercao de dados:\n")

def preencher_tabela(nome_arquivo, db_config, arquivo_log):
    # Estabelece conexão com o banco de dados
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    pasta_caminho = os.path.join(diretorio_atual, pasta_csv)
    
    try:
        # Verifica se o arquivo é um arquivo CSV
        if nome_arquivo.endswith(".csv"):
            # Caminho completo para o arquivo CSV
            caminho_arquivo = os.path.join(pasta_caminho, nome_arquivo)

            # Nome da tabela a ser criada (usando o nome do arquivo sem a extensão)
            nome_tabela = os.path.splitext(nome_arquivo)[0]

            # Verifica se o arquivo é referente a alguma tabela criada no banco
            query = f"SHOW TABLES LIKE '{nome_tabela}'"
            cursor.execute(query)
            table_exists = cursor.fetchone()

            if not table_exists:
                print(f"A tabela '{nome_tabela}' não existe no banco de dados.")
                return

            # Lê o arquivo CSV
            with open(caminho_arquivo, 'r') as csv_arquivo:
                csv_reader = csv.reader(csv_arquivo)

                # Pula a primeira linha (cabeçalhos das colunas)
                next(csv_reader)

                # Insere os dados do CSV na tabela
                for linha in csv_reader:
                    # Verifica e converte os campos numéricos para números
                    linha_formatada = []
                    for value in linha:
                        try:
                            valor_formatado = int(value)
                        except ValueError:
                            try:
                                valor_formatado = float(value)
                            except ValueError:
                                valor_formatado = value

                        linha_formatada.append(valor_formatado)

                    # Monta a consulta SQL para inserir os valores na tabela
                    placeholders = ', '.join(['%s'] * len(linha_formatada))
                    insert_query = f"INSERT INTO {nome_tabela} VALUES ({placeholders})"
                    cursor.execute(insert_query, linha_formatada)

            print(f"Os dados do arquivo '{nome_arquivo}' foram importados com sucesso para a tabela '{nome_tabela}'.")
            conn.commit()

    except Exception as e:
        # Registra o nome do arquivo CSV com erro no arquivo de log
        with open(arquivo_log, 'a') as log_arquivo:
            log_arquivo.write(f"{nome_arquivo}: {str(e)}\n")

    # Fecha a conexão com o banco de dados
    cursor.close()
    conn.close()

tabelas = [tabela_funcionarios, tabela_categorias, tabela_clientes, tabela_compras, tabela_produtos, tabela_detalhamento_compra]

arquivos_csv = ['funcionarios.csv', 'categorias.csv', 'clientes.csv', 'compras.csv',  'produtos.csv', 'detalhamento_compra.csv']

for tabela in tabelas:
    criar_tabela(tabela, db_config)

for nome_arquivo in arquivos_csv:
    preencher_tabela(nome_arquivo, db_config, arquivo_log_caminho)
