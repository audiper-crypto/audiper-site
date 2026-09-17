# Retaguarda contábil — carteira Consult

Fichas de fechamento das oito empresas cuja escrituração fazemos. Competência
de referência: **07/2026**.

## Não é material público

Este diretório está bloqueado no servidor:

- `.htaccess` — `RedirectMatch 404 ^/retaguarda/`
- `robots.txt` — `Disallow: /retaguarda/`
- cada página traz `<meta name="robots" content="noindex, nofollow">`

Devolve 404 e não 403 de propósito: 403 confirmaria que o arquivo existe. Para
usar, abra o arquivo local no navegador ou remova a linha do `.htaccess` pelo
tempo do acesso — e recoloque depois.

O motivo é o conteúdo: CNPJ, saldos bancários conta a conta, nomes de sócios,
distribuição de lucros e passivo tributário de clientes. Não linkar a partir de
página pública, não mandar por canal aberto.

## Separação de linhas

Nenhuma página aqui menciona a AUDIPER, e isso é regra, não descuido: **a
AUDIPER não pode auditar o que a AUDIPER escritura.** As oito empresas desta
carteira estão barradas para trabalho de auditoria. A identidade visual é
neutra por decisão — sem o claret e sem o dourado da marca.

## Arquivos

| arquivo | o que é |
|---|---|
| `index.html` | hub: as oito lado a lado, com o indicador de cada uma |
| `ficha.html` | ficha completa, com seletor de empresa. `ficha.html#7184` abre direto na Andrade |
| `retaguarda.css` | tokens e componentes compartilhados pelas duas páginas |

Códigos aceitos no hash: `7184` `7282` `763` `18` `311` `310` `5009` `5033`.

## O que a ficha mostra

1. **Trilha de 12 meses** — estado de cada competência do exercício.
2. **Mapa do fechamento** — todo item rastreado, agrupado por seção, com o
   verbo da ação (lançar, cadastrar, conferir, parar). O botão *Ver como fica
   quando fechar* mostra o estado-alvo: todos os cartões verdes.
3. **O caminho do documento** — cinco etapas, da nota que chega ao balancete
   que soma, com a etapa que quebrou marcada.
4. **Vínculos** — as identidades que a escrituração precisa satisfazer, cada
   uma com resposta numérica.
5. **As peças** — Balancete, DRE, Balanço, Fiscal e Folha da competência.
6. **A ponte da DRE** — a demonstração linha a linha, com o bloco de
   reconciliação: dentro, fora, resultado real, linhas sem conta apontada.
7. **O que falta** — ordenado por dependência, com a etiqueta de quem age.

## Procedência dos números

Conector `COnsult_Dominio`, **somente leitura sobre backup restaurado** — não é
o Domínio ao vivo. Carga de 17/09/2026 08:20 sobre o snapshot de 16/09, 28.167
linhas.

Duas regras que vieram de erro cometido:

- **Confira a carga antes de tratar divergência como achado.** Em 16/09 uma
  diferença de saldo de abertura foi reportada como achado estrutural; era
  defasagem do backup, e a carga do dia seguinte bateu ao centavo.
- **Contagem de lançamento não sai para cliente.** O `ledgerEntries` do conector
  não bate com a contagem do razão. O dinheiro bate, a contagem não. Serve como
  ritmo de escrituração, nunca como fato em peça.

E uma que vem dos dados: **DRE conforme não é fechamento.** Quatro das oito têm
zero conta fora da demonstração; duas delas não estão fechadas de jeito nenhum.
A estrutura está cadastrada, o que falta é escrituração. O hub mostra as duas
coisas em colunas separadas de propósito.

## Escopo contratual

Não confirmado. `00_CONTRATO_ESCOPO/` estava vazia em 11/09/2026. Tudo aqui é
estado **técnico** da escrituração, nunca estado contratual.

## Como atualizar

Os dados são gerados a partir do conector e embutidos no `<script>` de
`ficha.html`. Não há build no servidor: o HTML é o artefato final. Para uma nova
competência, regenere as duas páginas e substitua os arquivos.
