/*
Para exibir os triggers do banco
mysql> SHOW TRIGGERS FROM nome_do_banco_de_dados;
*/


/*Trigger para atualizar o estoque de produtos após uma compra*/
CREATE TRIGGER atualizar_estoque
AFTER INSERT ON compras
FOR EACH ROW
BEGIN
    UPDATE produtos
    SET Unidades_em_Estoque = Unidades_em_Estoque - NEW.Quantidade
    WHERE ID_Produto = NEW.ID_Produto;
END;


/*Trigger para calcular o total da compra após a inserção de um novo detalhamento de compra*/
CREATE TRIGGER calcular_total_compra
AFTER INSERT ON detalhamento_compra
FOR EACH ROW
BEGIN
    UPDATE compras
    SET Total = (SELECT SUM((Preco_Unitario * Quantidade) - Desconto) FROM detalhamento_compra WHERE ID_Compra = NEW.ID_Compra)
    WHERE ID_Compra = NEW.ID_Compra;
END;

/*Trigger para verificar se o supervisor de um funcionário existe*/
DELIMITER //
CREATE TRIGGER verificar_supervisor
BEFORE INSERT ON funcionarios /* insert or update*/
FOR EACH ROW
BEGIN
    IF NEW.Supervisor IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM funcionarios WHERE ID_Funcionario = NEW.Supervisor) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Supervisor não encontrado.';
        END IF;
    END IF;
END //

DELIMITER ;
