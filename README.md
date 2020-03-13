# Rankrawler

> Estes scripts fizeram parte da primeira atividade avaliativa da disciplina de programação para a internet I.

## Atividade

A atividade consistia em:
    * Fazer scraping em profundidade a partir dos seguintes parametros: url inicial, palavra-chave e profundidade;
    * Guardar os resultados em um banco de dados;
    * Fazer um rankeamento das páginas encontradas.

## Scraping

O scraping implementado segue as seguintes diretrizes:
    * Verifica a profundidade atual. Caso for 0, commita no banco de dados e retorna o método;
    * Checa se a url entrada faz parte de um domínio válido;
    * Verifica se o domínio da url foi recentemente visitado. Caso sim, espera um pouco.
    * Verifica se a url já foi visitada;
    * Faz a requisição da resposta da url;
    * Pega todos os links internos e externos do texto da resposta;
    * Verifica se a página possui alguns elementos e a como a palavra-chave é encontrado na página;
    * Caso a palavra-chave for encontrada, guardar algum exemplo que contenha a palavra;
    * Inserir conteúdo da página em um banco de dados;

## Rankeamento

O critério de rankeamento das páginas envolveu os seguintes aspectos:
    * log10 da quantidade de matches da palavra buscada no texto da tag body da página;
    * A probabilidade, de 0 a 1, da página ser considerada "relevante" a partir de um classificador;
    * Com os valores acima somados, os scores foram padronizados para que sempre o maior fosse 100 e os demais seguissem a proporção do primeiro.

## Observações

Os scripts que interessam ao objetivo do trabalho estão no notebook Rankrawler.ipynb
O banco de dados utilizado foi o MySQL.