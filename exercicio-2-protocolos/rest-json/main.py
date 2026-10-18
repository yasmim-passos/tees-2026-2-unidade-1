"""
Rede social simplificada exposta em REST (JSON) com FastAPI.
Os dados ficam em memória: ao reiniciar o servidor, tudo é apagado.
"""
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Rede Social - REST")

# ---------------- "Banco" em memória ----------------
usuarios = {}      # id -> {id, nome, email}
perfis = {}        # usuario_id -> {bio}            (Perfil 1:1 Usuario)
posts = {}         # id -> {id, autor_id, texto, criado_em}   (Post 1:N Usuario)
comentarios = []   # {id, usuario_id, post_id, texto, criado_em}  (N:M com atributo)
curtidas = []      # (usuario_id, post_id)          (N:M puro)
seguindo = []      # (seguidor_id, alvo_id)         (N:M auto-relacionamento)
contador = {"usuario": 0, "post": 0, "comentario": 0}


def proximo_id(tipo):
    contador[tipo] += 1
    return contador[tipo]


def agora():
    return datetime.now().isoformat(timespec="seconds")


def pegar_usuario(usuario_id):
    if usuario_id not in usuarios:
        raise HTTPException(404, f"Usuário {usuario_id} não encontrado")
    return usuarios[usuario_id]


def pegar_post(post_id):
    if post_id not in posts:
        raise HTTPException(404, f"Post {post_id} não encontrado")
    return posts[post_id]


def usuario_completo(u):
    return {**u, "perfil": perfis[u["id"]]}


def post_completo(p):
    return {
        **p,
        "autor": usuarios[p["autor_id"]]["nome"],
        "total_curtidas": sum(1 for (_, pid) in curtidas if pid == p["id"]),
        "comentarios": [c for c in comentarios if c["post_id"] == p["id"]],
    }


# ---------------- Corpos das requisições ----------------
class NovoUsuario(BaseModel):
    nome: str
    email: str


class NovoPost(BaseModel):
    usuario_id: int
    texto: str


class NovoComentario(BaseModel):
    usuario_id: int
    texto: str


class NovaCurtida(BaseModel):
    usuario_id: int


class NovoSeguir(BaseModel):
    alvo_id: int


# ---------------- Comandos ----------------
@app.post("/usuarios", status_code=201)
def criar_usuario(dados: NovoUsuario):
    if any(u["email"] == dados.email for u in usuarios.values()):
        raise HTTPException(409, "E-mail já cadastrado")
    uid = proximo_id("usuario")
    usuarios[uid] = {"id": uid, "nome": dados.nome, "email": dados.email}
    perfis[uid] = {"bio": ""}
    return usuario_completo(usuarios[uid])


@app.post("/posts", status_code=201)
def criar_post(dados: NovoPost):
    pegar_usuario(dados.usuario_id)
    pid = proximo_id("post")
    posts[pid] = {"id": pid, "autor_id": dados.usuario_id,
                  "texto": dados.texto, "criado_em": agora()}
    return posts[pid]


@app.post("/posts/{post_id}/comentarios", status_code=201)
def comentar(post_id: int, dados: NovoComentario):
    pegar_post(post_id)
    pegar_usuario(dados.usuario_id)
    comentario = {"id": proximo_id("comentario"), "usuario_id": dados.usuario_id,
                  "post_id": post_id, "texto": dados.texto, "criado_em": agora()}
    comentarios.append(comentario)
    return comentario


@app.post("/posts/{post_id}/curtidas", status_code=201)
def curtir(post_id: int, dados: NovaCurtida):
    pegar_post(post_id)
    pegar_usuario(dados.usuario_id)
    if (dados.usuario_id, post_id) in curtidas:
        raise HTTPException(409, "Usuário já curtiu este post")
    curtidas.append((dados.usuario_id, post_id))
    return {"usuario_id": dados.usuario_id, "post_id": post_id}


@app.post("/usuarios/{usuario_id}/seguindo", status_code=201)
def seguir(usuario_id: int, dados: NovoSeguir):
    pegar_usuario(usuario_id)
    pegar_usuario(dados.alvo_id)
    if usuario_id == dados.alvo_id:
        raise HTTPException(400, "Usuário não pode seguir a si mesmo")
    if (usuario_id, dados.alvo_id) in seguindo:
        raise HTTPException(409, "Usuário já segue o alvo")
    seguindo.append((usuario_id, dados.alvo_id))
    return {"usuario_id": usuario_id, "alvo_id": dados.alvo_id}


# ---------------- Consultas ----------------
@app.get("/usuarios/{usuario_id}")
def buscar_usuario(usuario_id: int):
    return usuario_completo(pegar_usuario(usuario_id))


@app.get("/usuarios/{usuario_id}/posts")
def posts_do_usuario(usuario_id: int):
    pegar_usuario(usuario_id)
    return [p for p in posts.values() if p["autor_id"] == usuario_id]


@app.get("/posts/{post_id}")
def buscar_post(post_id: int):
    return post_completo(pegar_post(post_id))


@app.get("/usuarios/{usuario_id}/seguidores")
def seguidores_de(usuario_id: int):
    pegar_usuario(usuario_id)
    return [usuarios[s] for (s, alvo) in seguindo if alvo == usuario_id]


@app.get("/usuarios/{usuario_id}/seguindo")
def seguindo_de(usuario_id: int):
    pegar_usuario(usuario_id)
    return [usuarios[alvo] for (s, alvo) in seguindo if s == usuario_id]


@app.get("/usuarios/{usuario_id}/feed")
def feed_do_usuario(usuario_id: int):
    """Posts de quem o usuário segue, do mais novo para o mais antigo."""
    pegar_usuario(usuario_id)
    ids_seguidos = {alvo for (s, alvo) in seguindo if s == usuario_id}
    feed = [post_completo(p) for p in posts.values() if p["autor_id"] in ids_seguidos]
    return sorted(feed, key=lambda p: p["id"], reverse=True)
