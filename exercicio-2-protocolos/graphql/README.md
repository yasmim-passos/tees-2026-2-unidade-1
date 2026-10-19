# Rede Social — GraphQL

API GraphQL em **Python + Strawberry + FastAPI**. Os dados ficam em memória (ao reiniciar o servidor, tudo é apagado).

> **O que o GraphQL faz melhor que o REST neste domínio:** o cliente monta o feed com exatamente os campos que precisa (texto, nome do autor, curtidas, comentários com autor, posts de quem ele segue…) em **uma única requisição**, enquanto no REST cada rota devolve um formato fixo e dados relacionados exigem várias chamadas.

## Como executar (do zero)

Pré-requisito: Python 3.10 ou mais novo.

```bash
cd graphql
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Existe um único endpoint: `POST http://localhost:8001/graphql`.

**Jeito mais fácil de testar:** abra **http://localhost:8001/graphql** no navegador. Aparece o GraphiQL: cole a consulta do bloco `graphql` de cada operação e clique em ▶. Para a linha de comando, cada operação também tem o `curl` equivalente (Linux, macOS ou Git Bash no Windows).

Execute os exemplos **na ordem**, porque os IDs são gerados em sequência. Os nomes ficam em camelCase (`criar_usuario` vira `criarUsuario`), que é a convenção do GraphQL.

## Operações

| Operação | Tipo | Campo no schema |
|---|---|---|
| criar_usuario | mutation | `criarUsuario(nome, email)` |
| criar_post | mutation | `criarPost(usuarioId, texto)` |
| comentar | mutation | `comentar(usuarioId, postId, texto)` |
| curtir | mutation | `curtir(usuarioId, postId)` |
| seguir | mutation | `seguir(usuarioId, alvoId)` |
| buscar_usuario | query | `buscarUsuario(id)` |
| posts_do_usuario | query | `postsDoUsuario(usuarioId)` |
| buscar_post | query | `buscarPost(id)` |
| seguidores_de / seguindo_de | query | `seguidoresDe(id)` e `seguindoDe(id)` |
| feed_do_usuario | query | `feedDoUsuario(usuarioId)` |

## Comandos (mutations)

### criar_usuario

```graphql
mutation {
  criarUsuario(nome: "Ana", email: "ana@email.com") { id nome email perfil { bio } }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "mutation { criarUsuario(nome: \"Ana\", email: \"ana@email.com\") { id nome email perfil { bio } } }"}'
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "mutation { criarUsuario(nome: \"Bruno\", email: \"bruno@email.com\") { id nome email } }"}'
```

Resposta, primeira requisição:

```json
{"data": {"criarUsuario": {"id": 1, "nome": "Ana", "email": "ana@email.com", "perfil": {"bio": ""}}}}
```

O perfil (1:1) é criado junto com o usuário.

### criar_post

```graphql
mutation {
  criarPost(usuarioId: 2, texto: "Meu primeiro post!") { id texto criadoEm autor { nome } }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "mutation { criarPost(usuarioId: 2, texto: \"Meu primeiro post!\") { id texto criadoEm autor { nome } } }"}'
```

Resposta:

```json
{"data": {"criarPost": {"id": 1, "texto": "Meu primeiro post!", "criadoEm": "2026-10-18T20:30:55", "autor": {"nome": "Bruno"}}}}
```

### comentar

```graphql
mutation {
  comentar(usuarioId: 1, postId: 1, texto: "Bem-vindo!") { id texto autor { nome } }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "mutation { comentar(usuarioId: 1, postId: 1, texto: \"Bem-vindo!\") { id texto autor { nome } } }"}'
```

Resposta:

```json
{"data": {"comentar": {"id": 1, "texto": "Bem-vindo!", "autor": {"nome": "Ana"}}}}
```

### curtir

```graphql
mutation {
  curtir(usuarioId: 1, postId: 1) { usuario { nome } post { id totalCurtidas } }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "mutation { curtir(usuarioId: 1, postId: 1) { usuario { nome } post { id totalCurtidas } } }"}'
```

Resposta:

```json
{"data": {"curtir": {"usuario": {"nome": "Ana"}, "post": {"id": 1, "totalCurtidas": 1}}}}
```

Curtir de novo o mesmo post devolve um erro no campo `errors` (o HTTP continua 200, como é padrão no GraphQL):

```json
{"data": null, "errors": [{"message": "Usuário já curtiu este post", "locations": [{"line": 1, "column": 12}], "path": ["curtir"]}]}
```

### seguir

A usuária 1 (Ana) passa a seguir o usuário 2 (Bruno):

```graphql
mutation {
  seguir(usuarioId: 1, alvoId: 2) { usuario { nome } alvo { nome } }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "mutation { seguir(usuarioId: 1, alvoId: 2) { usuario { nome } alvo { nome } } }"}'
```

Resposta:

```json
{"data": {"seguir": {"usuario": {"nome": "Ana"}, "alvo": {"nome": "Bruno"}}}}
```

## Consultas (queries)

### buscar_usuario

```graphql
{
  buscarUsuario(id: 1) { id nome email perfil { bio } }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "{ buscarUsuario(id: 1) { id nome email perfil { bio } } }"}'
```

Resposta:

```json
{"data": {"buscarUsuario": {"id": 1, "nome": "Ana", "email": "ana@email.com", "perfil": {"bio": ""}}}}
```

Um ID inexistente devolve `{"data": {"buscarUsuario": null}}`.

### posts_do_usuario

```graphql
{
  postsDoUsuario(usuarioId: 2) { id texto criadoEm }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "{ postsDoUsuario(usuarioId: 2) { id texto criadoEm } }"}'
```

Resposta:

```json
{"data": {"postsDoUsuario": [{"id": 1, "texto": "Meu primeiro post!", "criadoEm": "2026-10-18T20:30:55"}]}}
```

### buscar_post

```graphql
{
  buscarPost(id: 1) {
    id texto
    autor { nome }
    totalCurtidas
    comentarios { texto autor { nome } }
  }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "{ buscarPost(id: 1) { id texto autor { nome } totalCurtidas comentarios { texto autor { nome } } } }"}'
```

Resposta:

```json
{"data": {"buscarPost": {"id": 1, "texto": "Meu primeiro post!", "autor": {"nome": "Bruno"}, "totalCurtidas": 1, "comentarios": [{"texto": "Bem-vindo!", "autor": {"nome": "Ana"}}]}}}
```

### seguidores_de / seguindo_de

As duas consultas podem ir na mesma requisição:

```graphql
{
  seguidoresDe(id: 2) { id nome }
  seguindoDe(id: 1) { id nome }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "{ seguidoresDe(id: 2) { id nome } seguindoDe(id: 1) { id nome } }"}'
```

Resposta:

```json
{"data": {"seguidoresDe": [{"id": 1, "nome": "Ana"}], "seguindoDe": [{"id": 2, "nome": "Bruno"}]}}
```

### feed_do_usuario

Posts de quem o usuário segue, do mais novo para o mais antigo:

```graphql
{
  feedDoUsuario(usuarioId: 1) { id texto autor { nome } totalCurtidas }
}
```

```bash
curl -X POST http://localhost:8001/graphql -H "Content-Type: application/json" -d '{"query": "{ feedDoUsuario(usuarioId: 1) { id texto autor { nome } totalCurtidas } }"}'
```

Resposta:

```json
{"data": {"feedDoUsuario": [{"id": 1, "texto": "Meu primeiro post!", "autor": {"nome": "Bruno"}, "totalCurtidas": 1}]}}
```

## Bônus: navegando pelas relações

Como os tipos se ligam no schema, dá para atravessar o grafo numa consulta só, por exemplo "quem a Ana segue e o que essas pessoas postaram":

```graphql
{
  buscarUsuario(id: 1) { nome seguindo { nome posts { texto } } }
}
```

```json
{"data": {"buscarUsuario": {"nome": "Ana", "seguindo": [{"nome": "Bruno", "posts": [{"texto": "Meu primeiro post!"}]}]}}}
```
