# Rede Social — REST (JSON)

API REST em **Python + FastAPI**. Os dados ficam em memória (ao reiniciar o servidor, tudo é apagado).

> **O que o REST faz melhor que o GraphQL neste domínio:** cada operação é uma URL + um verbo HTTP, com códigos de status claros (201, 404, 409), então dá para testar cada uma com um simples `curl` ou pelo navegador, e as consultas `GET` podem ser cacheadas pelo próprio HTTP.

## Como executar (do zero)

Pré-requisito: Python 3.10 ou mais novo.

```bash
cd rest-json
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

A API fica em `http://localhost:8000`. A documentação interativa (Swagger) fica em **http://localhost:8000/docs**, onde dá para testar todas as rotas pelo navegador.

Os exemplos abaixo usam `curl` (Linux, macOS ou Git Bash no Windows) e devem ser executados **na ordem**, porque os IDs são gerados em sequência.

## Rotas

| Operação | Método e rota |
|---|---|
| criar_usuario | `POST /usuarios` |
| criar_post | `POST /posts` |
| comentar | `POST /posts/{post_id}/comentarios` |
| curtir | `POST /posts/{post_id}/curtidas` |
| seguir | `POST /usuarios/{id}/seguindo` |
| buscar_usuario | `GET /usuarios/{id}` |
| posts_do_usuario | `GET /usuarios/{id}/posts` |
| buscar_post | `GET /posts/{id}` |
| seguidores_de / seguindo_de | `GET /usuarios/{id}/seguidores` e `GET /usuarios/{id}/seguindo` |
| feed_do_usuario | `GET /usuarios/{id}/feed` |

## Comandos

### criar_usuario

```bash
curl -X POST http://localhost:8000/usuarios -H "Content-Type: application/json" -d '{"nome": "Ana", "email": "ana@email.com"}'
curl -X POST http://localhost:8000/usuarios -H "Content-Type: application/json" -d '{"nome": "Bruno", "email": "bruno@email.com"}'
```

Resposta (201), primeira requisição:

```json
{"id": 1, "nome": "Ana", "email": "ana@email.com", "perfil": {"bio": ""}}
```

O perfil (1:1) é criado junto com o usuário.

### criar_post

```bash
curl -X POST http://localhost:8000/posts -H "Content-Type: application/json" -d '{"usuario_id": 2, "texto": "Meu primeiro post!"}'
```

Resposta (201):

```json
{"id": 1, "autor_id": 2, "texto": "Meu primeiro post!", "criado_em": "2026-10-18T20:30:46"}
```

### comentar

```bash
curl -X POST http://localhost:8000/posts/1/comentarios -H "Content-Type: application/json" -d '{"usuario_id": 1, "texto": "Bem-vindo!"}'
```

Resposta (201):

```json
{"id": 1, "usuario_id": 1, "post_id": 1, "texto": "Bem-vindo!", "criado_em": "2026-10-18T20:30:46"}
```

### curtir

```bash
curl -X POST http://localhost:8000/posts/1/curtidas -H "Content-Type: application/json" -d '{"usuario_id": 1}'
```

Resposta (201):

```json
{"usuario_id": 1, "post_id": 1}
```

Curtir de novo o mesmo post retorna `409 {"detail": "Usuário já curtiu este post"}`.

### seguir

A usuária 1 (Ana) passa a seguir o usuário 2 (Bruno):

```bash
curl -X POST http://localhost:8000/usuarios/1/seguindo -H "Content-Type: application/json" -d '{"alvo_id": 2}'
```

Resposta (201):

```json
{"usuario_id": 1, "alvo_id": 2}
```

Seguir a si mesmo retorna `400`, e seguir alguém que já segue retorna `409`.

## Consultas

### buscar_usuario

```bash
curl http://localhost:8000/usuarios/1
```

Resposta (200):

```json
{"id": 1, "nome": "Ana", "email": "ana@email.com", "perfil": {"bio": ""}}
```

Um ID inexistente retorna `404 {"detail": "Usuário 99 não encontrado"}`.

### posts_do_usuario

```bash
curl http://localhost:8000/usuarios/2/posts
```

Resposta (200):

```json
[{"id": 1, "autor_id": 2, "texto": "Meu primeiro post!", "criado_em": "2026-10-18T20:30:46"}]
```

### buscar_post

```bash
curl http://localhost:8000/posts/1
```

Resposta (200):

```json
{
  "id": 1,
  "autor_id": 2,
  "texto": "Meu primeiro post!",
  "criado_em": "2026-10-18T20:30:46",
  "autor": "Bruno",
  "total_curtidas": 1,
  "comentarios": [
    {"id": 1, "usuario_id": 1, "post_id": 1, "texto": "Bem-vindo!", "criado_em": "2026-10-18T20:30:46"}
  ]
}
```

### seguidores_de / seguindo_de

```bash
curl http://localhost:8000/usuarios/2/seguidores
curl http://localhost:8000/usuarios/1/seguindo
```

Respostas (200):

```json
[{"id": 1, "nome": "Ana", "email": "ana@email.com"}]
```

```json
[{"id": 2, "nome": "Bruno", "email": "bruno@email.com"}]
```

### feed_do_usuario

Posts de quem o usuário segue, do mais novo para o mais antigo:

```bash
curl http://localhost:8000/usuarios/1/feed
```

Resposta (200):

```json
[
  {
    "id": 1,
    "autor_id": 2,
    "texto": "Meu primeiro post!",
    "criado_em": "2026-10-18T20:30:46",
    "autor": "Bruno",
    "total_curtidas": 1,
    "comentarios": [
      {"id": 1, "usuario_id": 1, "post_id": 1, "texto": "Bem-vindo!", "criado_em": "2026-10-18T20:30:46"}
    ]
  }
]
```
