"""
Rede social simplificada exposta em GraphQL com Strawberry + FastAPI.
Os dados ficam em memória: ao reiniciar o servidor, tudo é apagado.
Endpoint único: POST /graphql (abrindo no navegador aparece o GraphiQL).
"""
from datetime import datetime
from typing import List, Optional

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

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


def exigir_usuario(usuario_id):
    if usuario_id not in usuarios:
        raise ValueError(f"Usuário {usuario_id} não encontrado")


def exigir_post(post_id):
    if post_id not in posts:
        raise ValueError(f"Post {post_id} não encontrado")


# ---------------- Tipos do schema ----------------
@strawberry.type
class Perfil:
    bio: str


@strawberry.type
class Usuario:
    id: int
    nome: str
    email: str

    @strawberry.field
    def perfil(self) -> Perfil:
        return Perfil(**perfis[self.id])

    @strawberry.field
    def posts(self) -> List["Post"]:
        return posts_do_autor(self.id)

    @strawberry.field
    def seguidores(self) -> List["Usuario"]:
        return lista_seguidores(self.id)

    @strawberry.field
    def seguindo(self) -> List["Usuario"]:
        return lista_seguindo(self.id)


@strawberry.type
class Comentario:
    id: int
    texto: str
    criado_em: str
    usuario_id: strawberry.Private[int]

    @strawberry.field
    def autor(self) -> Usuario:
        return para_usuario(self.usuario_id)


@strawberry.type
class Post:
    id: int
    texto: str
    criado_em: str
    autor_id: strawberry.Private[int]

    @strawberry.field
    def autor(self) -> Usuario:
        return para_usuario(self.autor_id)

    @strawberry.field
    def total_curtidas(self) -> int:
        return sum(1 for (_, pid) in curtidas if pid == self.id)

    @strawberry.field
    def comentarios(self) -> List[Comentario]:
        return [para_comentario(c) for c in comentarios if c["post_id"] == self.id]


@strawberry.type
class Curtida:
    usuario: Usuario
    post: Post


@strawberry.type
class Seguir:
    usuario: Usuario
    alvo: Usuario


# ---------------- Conversões dict -> tipo ----------------
def para_usuario(uid):
    return Usuario(**usuarios[uid])


def para_post(p):
    return Post(id=p["id"], texto=p["texto"], criado_em=p["criado_em"], autor_id=p["autor_id"])


def para_comentario(c):
    return Comentario(id=c["id"], texto=c["texto"], criado_em=c["criado_em"],
                      usuario_id=c["usuario_id"])


def posts_do_autor(uid):
    return [para_post(p) for p in posts.values() if p["autor_id"] == uid]


def lista_seguidores(uid):
    return [para_usuario(s) for (s, alvo) in seguindo if alvo == uid]


def lista_seguindo(uid):
    return [para_usuario(alvo) for (s, alvo) in seguindo if s == uid]


# ---------------- Consultas ----------------
@strawberry.type
class Query:
    @strawberry.field
    def buscar_usuario(self, id: int) -> Optional[Usuario]:
        return para_usuario(id) if id in usuarios else None

    @strawberry.field
    def posts_do_usuario(self, usuario_id: int) -> List[Post]:
        exigir_usuario(usuario_id)
        return posts_do_autor(usuario_id)

    @strawberry.field
    def buscar_post(self, id: int) -> Optional[Post]:
        return para_post(posts[id]) if id in posts else None

    @strawberry.field
    def seguidores_de(self, id: int) -> List[Usuario]:
        exigir_usuario(id)
        return lista_seguidores(id)

    @strawberry.field
    def seguindo_de(self, id: int) -> List[Usuario]:
        exigir_usuario(id)
        return lista_seguindo(id)

    @strawberry.field
    def feed_do_usuario(self, usuario_id: int) -> List[Post]:
        """Posts de quem o usuário segue, do mais novo para o mais antigo."""
        exigir_usuario(usuario_id)
        ids_seguidos = {alvo for (s, alvo) in seguindo if s == usuario_id}
        feed = [p for p in posts.values() if p["autor_id"] in ids_seguidos]
        return [para_post(p) for p in sorted(feed, key=lambda p: p["id"], reverse=True)]


# ---------------- Comandos ----------------
@strawberry.type
class Mutation:
    @strawberry.mutation
    def criar_usuario(self, nome: str, email: str) -> Usuario:
        if any(u["email"] == email for u in usuarios.values()):
            raise ValueError("E-mail já cadastrado")
        uid = proximo_id("usuario")
        usuarios[uid] = {"id": uid, "nome": nome, "email": email}
        perfis[uid] = {"bio": ""}
        return para_usuario(uid)

    @strawberry.mutation
    def criar_post(self, usuario_id: int, texto: str) -> Post:
        exigir_usuario(usuario_id)
        pid = proximo_id("post")
        posts[pid] = {"id": pid, "autor_id": usuario_id, "texto": texto, "criado_em": agora()}
        return para_post(posts[pid])

    @strawberry.mutation
    def comentar(self, usuario_id: int, post_id: int, texto: str) -> Comentario:
        exigir_usuario(usuario_id)
        exigir_post(post_id)
        c = {"id": proximo_id("comentario"), "usuario_id": usuario_id,
             "post_id": post_id, "texto": texto, "criado_em": agora()}
        comentarios.append(c)
        return para_comentario(c)

    @strawberry.mutation
    def curtir(self, usuario_id: int, post_id: int) -> Curtida:
        exigir_usuario(usuario_id)
        exigir_post(post_id)
        if (usuario_id, post_id) in curtidas:
            raise ValueError("Usuário já curtiu este post")
        curtidas.append((usuario_id, post_id))
        return Curtida(usuario=para_usuario(usuario_id), post=para_post(posts[post_id]))

    @strawberry.mutation
    def seguir(self, usuario_id: int, alvo_id: int) -> Seguir:
        exigir_usuario(usuario_id)
        exigir_usuario(alvo_id)
        if usuario_id == alvo_id:
            raise ValueError("Usuário não pode seguir a si mesmo")
        if (usuario_id, alvo_id) in seguindo:
            raise ValueError("Usuário já segue o alvo")
        seguindo.append((usuario_id, alvo_id))
        return Seguir(usuario=para_usuario(usuario_id), alvo=para_usuario(alvo_id))


schema = strawberry.Schema(query=Query, mutation=Mutation)

app = FastAPI(title="Rede Social - GraphQL")
app.include_router(GraphQLRouter(schema), prefix="/graphql")
