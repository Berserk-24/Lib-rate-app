#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional
from datetime import datetime, date
import uuid
from models.user import User
from models.post import Post, Comment
from database.db_manager import DatabaseManager
from utils.security import SecurityValidator
from ui.reactive_ui import ReactiveUI  # cambio


class PostService:
    def __init__(self, db_manager: DatabaseManager, reactive_ui: ReactiveUI):
        self.db_manager = db_manager
        self.posts_collection = db_manager.db.posts
        self.users_collection = db_manager.db.users
        self.reactive_ui = reactive_ui # cambio
        self._observers = []  # cambio

    def attach(self, observer):#
        """Agregar un observador para notificaciones de cambios"""
        if observer not in self._observers:
            self._observers.append(observer)#cambio

    
    def create_post(self, user: User, content: str, purpose: str = "", source: str = "", image_path: str = None) -> bool:
        """Crear un nuevo post"""
        try:
            # Verificar límite diario de posts
            if user.daily_posts >= 3:
                raise ValueError("Has alcanzado el límite diario de 3 posts")
            
            # Sanitizar contenido
            clean_content = SecurityValidator.sanitize_input(content)
            clean_purpose = SecurityValidator.sanitize_input(purpose) if purpose else ""
            clean_source = SecurityValidator.sanitize_input(source) if source else ""
            
            if not clean_content.strip():
                raise ValueError("El contenido no puede estar vacío")
            
            # Crear el post
            post = Post(
                post_id=str(uuid.uuid4()),
                user_id=user.user_id,
                username=user.username,
                content=clean_content,
                purpose=clean_purpose,
                source=clean_source,
                image_path=image_path
            )
            
            # Guardar en base de datos
            post_doc = post.to_dict()
            self.posts_collection.insert_one(post_doc)
            
            # Actualizar contador de posts del usuario
            today = datetime.now().date()
            if user.last_post_date != today:
                user.daily_posts = 1
                user.last_post_date = today
            else:
                user.daily_posts += 1
            
            # Actualizar usuario en base de datos
            self.users_collection.update_one(
                {"_id": user.user_id},
                {
                    "$set": {
                        "daily_posts": user.daily_posts,
                        "last_post_date": user.last_post_date.isoformat()
                    }
                }
            )
            self.reactive_ui.emit("user_updated", user)# cambio

            return True
            
        except Exception as e:
            print(f"Error creando post: {e}")
            return False
    
    def get_posts(self, limit: int = 50) -> List[Post]:
        """Obtener lista de posts ordenados por fecha"""
        try:
            posts_data = self.posts_collection.find().sort("timestamp", -1).limit(limit)
            posts = []
            
            for post_doc in posts_data:
                post = Post.from_dict(post_doc)
                posts.append(post)
            
            return posts
            
        except Exception as e:
            print(f"Error obteniendo posts: {e}")
            return []
    
    def get_user_posts(self, user_id: str, limit: int = 20) -> List[Post]:
        """Obtener posts de un usuario específico"""
        try:
            posts_data = self.posts_collection.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit)
            
            posts = []
            for post_doc in posts_data:
                post = Post.from_dict(post_doc)
                posts.append(post)
            
            return posts
            
        except Exception as e:
            print(f"Error obteniendo posts del usuario: {e}")
            return []
    
    def toggle_like(self, post_id: str, user_id: str) -> bool:
        """Alternar like en un post"""
        try:
            post_doc = self.posts_collection.find_one({"_id": post_id})
            if not post_doc:
                return False
            
            likes = post_doc.get("likes_list", [])
            
            if user_id in likes:
                # Quitar like
                self.posts_collection.update_one(
                    {"_id": post_id},
                    {
                        "$pull": {"likes_list": user_id},
                        "$inc": {"likes": -1}
                    }
                )
            else:
                # Agregar like
                self.posts_collection.update_one(
                    {"_id": post_id},
                    {
                        "$push": {"likes_list": user_id},
                        "$inc": {"likes": 1}
                    }
                )
            
            return True
            
        except Exception as e:
            print(f"Error toggling like: {e}")
            return False
    
    def share_post(self, post_id: str) -> bool:
        """Compartir un post (incrementar contador)"""
        try:
            result = self.posts_collection.update_one(
                {"_id": post_id},
                {"$inc": {"shares": 1}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error compartiendo post: {e}")
            return False
    
    def add_comment(self, post_id: str, user_id: str, username: str, content: str) -> bool:
        """Agregar comentario a un post (máx 3 por usuario por post)"""
        try:
            # Obtener el post actual
            post_doc = self.posts_collection.find_one({"_id": post_id})
            if not post_doc:
                return False

            # Contar comentarios de este usuario en el post
            user_comments = [c for c in post_doc.get("comments", []) if c.get("user_id") == user_id]
            if len(user_comments) >= 3:
                print("Límite de 3 comentarios por usuario alcanzado para este post.")
                return False

            clean_content = SecurityValidator.sanitize_input(content)
            if not clean_content.strip():
                return False

            comment = Comment(
                comment_id=str(uuid.uuid4()),
                post_id=post_id,
                user_id=user_id,
                username=username,
                content=clean_content
            )

            result = self.posts_collection.update_one(
                {"_id": post_id},
                {"$push": {"comments": comment.to_dict()}}
            )

            return result.modified_count > 0

        except Exception as e:
            print(f"Error agregando comentario: {e}")
            return False
    
    def delete_post(self, post_id: str, user_id: str) -> bool:
        """Eliminar un post (solo el autor puede eliminarlo)"""
        try:
            result = self.posts_collection.delete_one({
                "_id": post_id,
                "user_id": user_id
            })
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"Error eliminando post: {e}")
            return False
    
    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        """Obtener un post específico por ID"""
        try:
            post_doc = self.posts_collection.find_one({"_id": post_id})
            if post_doc:
                return Post.from_dict(post_doc)
            return None
            
        except Exception as e:
            print(f"Error obteniendo post por ID: {e}")
            return None
    
    def search_posts(self, query: str, limit: int = 20) -> List[Post]:
        """Buscar posts por contenido"""
        try:
            clean_query = SecurityValidator.sanitize_input(query)
            if not clean_query.strip():
                return []
            
            posts_data = self.posts_collection.find({
                "$or": [
                    {"content": {"$regex": clean_query, "$options": "i"}},
                    {"purpose": {"$regex": clean_query, "$options": "i"}},
                    {"source": {"$regex": clean_query, "$options": "i"}}
                ]
            }).sort("timestamp", -1).limit(limit)
            
            posts = []
            for post_doc in posts_data:
                post = Post.from_dict(post_doc)
                posts.append(post)
            
            return posts
            
        except Exception as e:
            print(f"Error buscando posts: {e}")
            return []