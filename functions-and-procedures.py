import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'user',
    'password': 'password',
    'database': 'database'
}

arquivo_log = "errors.log"

with open(arquivo_log, 'w') as log_arquivo:
    log_arquivo.write("Comandos falhos:\n")

procedure_backfill = '''
DELIMITER //

CREATE PROCEDURE backfill_calcular_preco_total()
BEGIN
    UPDATE compras c
    JOIN (
        SELECT ID_Compra, SUM(Preco_Unitario * Quantidade *(1 - Desconto)) AS total
        FROM detalhamento_compra
        GROUP BY ID_Compra
    ) dc ON dc.ID_Compra = c.ID_Compra
    SET c.Preco_Total = IFNULL(dc.total, 0);
END //

DELIMITER ;
'''

function_preco_total_por_cliente = '''
DELIMITER //
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

DELIMITER ;
'''

realiza_backfill = '''CALL backfill_calcular_preco_total();''' 

def preco_total_por_cliente(cliente):
    consulta_sql = "SELECT calcular_preco_total_cliente('" + cliente + "')"
    return consulta_sql

def executar_comando(query_sql, db_config):

    # Configurar a conexão com o banco de dados
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    try: 

        # Executar a consulta SQL 
        cursor.execute(query_sql)
        connection.commit()
        print("Comando executado com sucesso!")

    except Exception as e:
        # Registra a query com o seu respectivo erro no arquivo de log
        with open(arquivo_log, 'a') as log_arquivo:
            log_arquivo.write(f"{query_sql}: {str(e)}\n")

    cursor.close()
    connection.close()

backfill = [procedure_backfill, realiza_backfill]

for query in backfill:
    executar_comando(query, db_config)

executar_comando(function_preco_total_por_cliente, db_config)

executar_comando(preco_total_por_cliente(""), db_config)