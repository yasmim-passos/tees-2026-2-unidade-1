# Atividade 02 — APIs e protocolos

Tópicos Especiais em Engenharia de Software · 2026.2 · Unidade 1

O mesmo domínio (uma rede social simplificada) exposto em dois protocolos: **REST (JSON)** e **GraphQL**. Os dois projetos são separados, escritos em **Python**, e guardam os dados em memória para manter tudo simples.

```
exercicio-2-protocolos/
├── README.md        visão geral + comparação final (este arquivo)
├── rest-json/       API REST com FastAPI (porta 8000)
└── graphql/         API GraphQL com Strawberry + FastAPI (porta 8001)
```

Cada pasta tem o próprio README com as instruções para executar do zero e um exemplo copiável de requisição e resposta para cada operação.

## Domínio

| Entidade | Relação | Como foi modelada |
|---|---|---|
| Usuario | — | id, nome, email |
| Perfil | 1:1 com Usuario | criado junto com o usuário (bio) |
| Post | 1:N (um usuário é autor de vários posts) | id, autor, texto, data |
| Comentario | N:M entre Usuario e Post, com atributo | usuário + post + texto + data |
| Curtida | N:M puro entre Usuario e Post | par (usuário, post), sem repetição |
| Seguidor | N:M de Usuario com ele mesmo | par (seguidor, alvo), sem repetição e sem seguir a si mesmo |

O **feed** de um usuário são os posts de quem ele segue, do mais novo para o mais antigo.

## Execução rápida

Precisa de Python 3.10+. Em dois terminais:

```bash
# Terminal 1 — REST
cd rest-json
python -m venv .venv && source .venv/bin/activate   # no Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# testar no navegador: http://localhost:8000/docs
```

```bash
# Terminal 2 — GraphQL
cd graphql
python -m venv .venv && source .venv/bin/activate   # no Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
# testar no navegador: http://localhost:8001/graphql
```

## Mesmas operações nos dois protocolos

| Operação | REST | GraphQL |
|---|---|---|
| criar_usuario | `POST /usuarios` | `mutation criarUsuario` |
| criar_post | `POST /posts` | `mutation criarPost` |
| comentar | `POST /posts/{id}/comentarios` | `mutation comentar` |
| curtir | `POST /posts/{id}/curtidas` | `mutation curtir` |
| seguir | `POST /usuarios/{id}/seguindo` | `mutation seguir` |
| buscar_usuario | `GET /usuarios/{id}` | `query buscarUsuario` |
| posts_do_usuario | `GET /usuarios/{id}/posts` | `query postsDoUsuario` |
| buscar_post | `GET /posts/{id}` | `query buscarPost` |
| seguidores_de / seguindo_de | `GET /usuarios/{id}/seguidores` e `/seguindo` | `query seguidoresDe` e `seguindoDe` |
| feed_do_usuario | `GET /usuarios/{id}/feed` | `query feedDoUsuario` |

## Comparação final

| Aspecto | REST | GraphQL |
|---|---|---|
| Endpoints | Vários, um por recurso (`/usuarios`, `/posts/1/curtidas`…) | Um só (`/graphql`) |
| Quem decide o formato da resposta | O servidor, fixo por rota | O cliente, campo por campo |
| Dados relacionados | Várias requisições ou rotas "engordadas" (o `GET /posts/1` já traz comentários e curtidas, quer o cliente queira ou não) | Uma consulta atravessa as relações (post → autor → comentários → autor) |
| Erros | Códigos HTTP (201, 400, 404, 409) | HTTP 200 com o campo `errors` no corpo |
| Cache | Natural nos `GET`, pelo próprio HTTP | Mais difícil, tudo é `POST` no mesmo endpoint |
| Contrato | Documentado à parte (aqui, o Swagger gerado pelo FastAPI) | O schema tipado é o contrato e pode ser explorado no GraphiQL |
| Testar à mão | Muito simples (`curl` ou navegador) | Precisa montar a consulta, mas o GraphiQL ajuda bastante |

**Em uma linha:** neste domínio, o **REST** é melhor para operações simples e diretas, com status HTTP claros e cache nas consultas, enquanto o **GraphQL** é melhor para telas como o feed e o post detalhado, que juntam dados de várias entidades, porque o cliente busca tudo o que precisa, e só o que precisa, numa requisição.
