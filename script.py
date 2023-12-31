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
    # print(f"Tabela{tabela_sql} criada com sucesso!")

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

procedure_backfill = '''
CREATE PROCEDURE backfill_calcular_preco_total()
BEGIN
    UPDATE compras c
    JOIN (
        SELECT ID_Compra, SUM(Preco_Unitario * Quantidade *(1 - Desconto)) AS total
        FROM detalhamento_compra
        GROUP BY ID_Compra
    ) dc ON dc.ID_Compra = c.ID_Compra
    SET c.Preco_Total = IFNULL(dc.total, 0);
END
'''

function_preco_total_por_cliente = '''
CREATE FUNCTION calcular_preco_total_cliente(ID_Cliente_param CHAR(10))
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE preco_total DECIMAL(10,2);
    
    SELECT SUM(dc.Preco_Unitario * dc.Quantidade * (1 - Desconto))
    INTO preco_total
    FROM compras c
    JOIN detalhamento_compra dc ON dc.ID_Compra = c.ID_Compra
    WHERE c.ID_Cliente = ID_Cliente_param;
    
    IF preco_total IS NULL THEN
        SET preco_total = 0;
    END IF;
    
    RETURN preco_total;
END;
'''

realiza_backfill = '''CALL backfill_calcular_preco_total();''' 

vw_produto_mais_vendido = '''
CREATE or REPLACE VIEW vw_produto_mais_vendido AS
	SELECT p.Nome_Produto,
		SUM(dc.Quantidade) AS Total_Vendas
	FROM produtos as p
	JOIN detalhamento_compra as dc ON (p.ID_Produto = dc.ID_Produto)
	GROUP BY p.Nome_Produto
	ORDER BY Total_Vendas DESC
	LIMIT 10;
'''

vw_categorias_mais_vendidas = '''
CREATE or REPLACE VIEW vw_categorias_mais_vendidas AS
	SELECT cat.Nome_Categoria,
		SUM(dc.Quantidade) AS Total_Vendas
	FROM categorias as cat
	JOIN produtos as p ON cat.ID_Categoria = p.ID_Categoria
	JOIN detalhamento_compra as dc ON (p.ID_Produto = dc.ID_Produto)
	GROUP BY cat.ID_Categoria, cat.Nome_Categoria
	ORDER BY Total_Vendas DESC
	LIMIT 5;
'''

vw_top1_vendedor_por_pais = '''
CREATE or REPLACE VIEW vw_top1_vendedor_por_pais AS
SELECT T.Pais, T.Nome_Vendedor, T.Total_Vendas
FROM (
    SELECT f.Pais, f.Nome AS Nome_Vendedor, COUNT(*) AS Total_Vendas
    FROM funcionarios f
    JOIN compras c ON f.ID_Funcionario = c.ID_Funcionario
    GROUP BY f.Pais, f.Nome
) AS T
JOIN (
    SELECT Pais, MAX(Total_Vendas) AS Max_Vendas
    FROM (
        SELECT f.Pais, f.Nome AS Nome_Vendedor, COUNT(*) AS Total_Vendas
        FROM funcionarios f
        JOIN compras c ON f.ID_Funcionario = c.ID_Funcionario
        GROUP BY f.Pais, f.Nome
    ) AS V
    GROUP BY Pais
) AS M ON T.Pais = M.Pais AND T.Total_Vendas = M.Max_Vendas
ORDER BY T.Pais;
'''

vw_pedidos = '''
CREATE VIEW vw_pedidos AS
SELECT c.ID_Compra, c.Data_Venda, cli.Representante_Empresa, p.Nome_Produto
FROM compras c
INNER JOIN clientes cli ON cli.ID_Cliente = c.ID_Cliente
INNER JOIN detalhamento_compra dc ON dc.ID_Compra = c.ID_Compra
INNER JOIN produtos p ON dc.ID_Produto = p.ID_Produto;
'''

trigger_atualiza_estoque ='''
CREATE TRIGGER atualizar_estoque
AFTER INSERT ON detalhamento_compra
FOR EACH ROW
BEGIN
    UPDATE produtos
    SET Unidades_em_Estoque = Unidades_em_Estoque - NEW.Quantidade
    WHERE ID_Produto = NEW.ID_Produto;
END;
'''

trigger_calcular_total_compra = '''
CREATE TRIGGER calcular_total_compra
AFTER INSERT ON detalhamento_compra
FOR EACH ROW
BEGIN
    UPDATE compras
    SET Total = (SELECT SUM((Preco_Unitario * Quantidade) - Desconto) FROM detalhamento_compra WHERE ID_Compra = NEW.ID_Compra)
    WHERE ID_Compra = NEW.ID_Compra;
END;'''


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

    # Lê os resultados e fecha conexão com o banco de dados
    cursor.close()
    conn.close()

def executar_comando(query_sql, db_config, arquivo_log):

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    try: 

        # Executar a consulta SQL 
        cursor.execute(query_sql)
        connection.commit()

    except Exception as e:
        # Registra a query com o seu respectivo erro no arquivo de log
        with open(arquivo_log, 'a') as log_arquivo:
            log_arquivo.write(f"Comando falho:{query_sql}: {str(e)}\n")

    for row in cursor.fetchall():
        print(row)
        cursor.close()

    cursor.close()
    connection.close()

def preco_total_por_cliente(cliente):
    consulta_sql = "SELECT calcular_preco_total_cliente('" + cliente + "')"
    return consulta_sql

def executar_view (view):
    consulta = "SELECT * FROM " + view + ";"
    return consulta

views_criacao = [vw_produto_mais_vendido, vw_categorias_mais_vendidas, vw_top1_vendedor_por_pais]

views = ["vw_produto_mais_vendido", "vw_categorias_mais_vendidas", "vw_top1_vendedor_por_pais"]

triggers = [trigger_atualiza_estoque, trigger_calcular_total_compra]

tabelas = [tabela_funcionarios, tabela_categorias, tabela_clientes, tabela_compras, tabela_produtos, tabela_detalhamento_compra]

arquivos_csv = ['funcionarios.csv', 'categorias.csv', 'clientes.csv', 'compras.csv',  'produtos.csv', 'detalhamento_compra.csv']

backfill = [procedure_backfill, realiza_backfill]

clientes = ["ALFKI", "HANAR", "BLONP"]

preco_total_coluna = '''
ALTER TABLE db_projeto_bd2.compras
ADD COLUMN Preco_Total DECIMAL(10,2) DEFAULT 0;
'''

for tabela in tabelas:
    criar_tabela(tabela, db_config)

for nome_arquivo in arquivos_csv:
    preencher_tabela(nome_arquivo, db_config, arquivo_log_caminho)

#criacao de nova coluna preco_total
executar_comando(preco_total_coluna, db_config, arquivo_log_caminho)

#criando a função de gastos totais do cliente
executar_comando(function_preco_total_por_cliente, db_config, arquivo_log_caminho)

for query in backfill:
    executar_comando(query, db_config, arquivo_log_caminho)

for cliente in clientes:
    print("Gastos totais do cliente " + cliente)
    executar_comando(preco_total_por_cliente(cliente), db_config, arquivo_log_caminho)

for view in views_criacao:
    executar_comando(view, db_config, arquivo_log_caminho)

for view in views:
    print(view)
    executar_comando(executar_view(view), db_config, arquivo_log_caminho)

for trigger in triggers:
    executar_comando(trigger, db_config, arquivo_log_caminho)