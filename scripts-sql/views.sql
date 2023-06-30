/* # Produtos mais vendidos
		SELECT * FROM vw_produto_mais_vendido;
*/
CREATE or REPLACE VIEW vw_produto_mais_vendido AS
	SELECT p.Nome_Produto,
		SUM(dc.Quantidade) AS Total_Vendas
	FROM produtos as p
	JOIN detalhamento_compra as dc ON (p.ID_Produto = dc.ID_Produto)
	GROUP BY p.Nome_Produto
	ORDER BY Total_Vendas DESC
	LIMIT 10;  /* Os 10 mais vendidos*/
	


/* # Categorias mais vendidos
		SELECT * FROM vw_categorias_mais_vendidas;

*/
CREATE or REPLACE VIEW vw_categorias_mais_vendidas AS
	SELECT cat.Nome_Categoria,
		SUM(dc.Quantidade) AS Total_Vendas
	FROM categorias as cat
	JOIN produtos as p ON cat.ID_Categoria = p.ID_Categoria
	JOIN detalhamento_compra as dc ON (p.ID_Produto = dc.ID_Produto)
	GROUP BY cat.ID_Categoria, cat.Nome_Categoria
	ORDER BY Total_Vendas DESC
	LIMIT 5;  /* As 5 mais vendidos*/
	
	
	
/* # TOP 1 vendedor de cada país
		SELECT * FROM vw_top1_vendedor_por_pais;
*/
CREATE VIEW vw_top1_vendedor_por_pais AS
SELECT f.Pais, f.Nome
COUNT(*) AS Total_Vendas
FROM funcionarios as f
JOIN compras as c ON f.ID_Funcionario = c.ID_Vendedor
GROUP BY f.Pais, f.Nome
HAVING COUNT(*) = (
    SELECT MAX(NumVendas)
    FROM (
        SELECT COUNT(*) AS NumVendas
        FROM funcionarios f2
        JOIN compras c2 ON f2.ID_Funcionario = c2.ID_Vendedor
        WHERE f2.Pais = f.Pais
        GROUP BY f2.Pais, f2.Nome
    ) AS T
)
ORDER BY f.Pais;


CREATE VIEW vw_top1_vendedor_por_pais AS
SELECT Pais, Nome_Vendedor, Total_Vendas
FROM (
    SELECT f.Pais, f.Nome AS Nome_Vendedor, COUNT(*) AS Total_Vendas,
           ROW_NUMBER() OVER (PARTITION BY f.Pais ORDER BY COUNT(*) DESC) AS Rank
    FROM funcionarios f
    JOIN compras c ON f.ID_Funcionario = c.ID_Vendedor
    GROUP BY f.Pais, f.Nome
) AS T
WHERE Rank = 1
ORDER BY Pais; 


/*
View de pedidos com detalhes do cliente e produto:

    SELECT * FROM vw_orders;
*/
CREATE VIEW vw_pedidos AS
SELECT c.ID_Compra, c.Data_Venda, cli.Representante_Empresa, p.Nome_Produto
FROM compras c
INNER JOIN clientes cli ON cli.ID_Cliente = c.ID_Cliente
INNER JOIN detalhamento_compra dc ON dc.ID_Compra = c.ID_Compra
INNER JOIN produtos p ON dc.ID_Produto = p.ID_Produto;
