#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import List, Optional
from utils.security import SecurityValidator

class Comment:
    def __init__(self, comment_id: str, post_id: str, user_id: str, username: str, content: str):
        self.comment_id = comment_id
        self.post_id = post_id
        self.user_id = user_id
        self.username = username
        self.content = SecurityValidator.sanitize_input(content)
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "comment_id": self.comment_id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "username": self.username,
            "content": self.content,
            "timestamp": self.timestamp
        }

class Post:
    def __init__(self, 
                 post_id: str, user_id: str, username: str, content: str, 
                 purpose: str = "", source: str = "",  image_path: str = None,
                created_at: datetime = None,
                comments: list = None):
        
        self.post_id = post_id
        self.user_id = user_id
        self.username = username
        self.content = SecurityValidator.sanitize_input(content)
        self.purpose = SecurityValidator.sanitize_input(purpose)
        self.source = SecurityValidator.sanitize_input(source)
        self.timestamp = datetime.now()
        self.comments: List[Comment] = []
        self.shares = 0
        self.likes = 0
        self.created_at = created_at if created_at else datetime.now() #cambio
        self.liked_by: List[str] = []  # Lista de user_ids que dieron like
        self.image_path: Optional[str] = image_path  # Ruta a imagen adjunta
    
    def to_dict(self) -> dict:
        """Convertir post a diccionario para MongoDB"""
        return {
            "_id": self.post_id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "username": self.username,
            "content": self.content,
            "purpose": self.purpose,
            "source": self.source,
            "timestamp": self.timestamp,
            "shares": self.shares,
            "likes": self.likes,
            "liked_by": self.liked_by,
            "image_path": self.image_path,
            "comments": [comment.to_dict() for comment in self.comments]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Post':
        """Crear post desde diccionario de MongoDB"""
        post = cls(
            data["post_id"],
            data["user_id"],
            data.get("username", "Usuario"),
            data["content"],
            data.get("purpose", ""),
            data.get("source", "")
        )
        post.timestamp = data.get("timestamp", datetime.now())
        post.shares = data.get("shares", 0)
        post.likes = data.get("likes", 0)
        post.liked_by = data.get("liked_by", [])
        post.image_path = data.get("image_path")
        
        # Cargar comentarios
        comments_data = data.get("comments", [])
        post.comments = [
            Comment(
                c["comment_id"], c["post_id"], c["user_id"], 
                c.get("username", "Usuario"), c["content"]
            ) for c in comments_data
        ]
        
        return post
    
    def add_like(self, user_id: str) -> bool:
        """Agregar like si el usuario no ha dado like antes"""
        if user_id not in self.liked_by:
            self.liked_by.append(user_id)
            self.likes += 1
            return True
        return False
    
    def remove_like(self, user_id: str) -> bool:
        """Quitar like del usuario"""
        if user_id in self.liked_by:
            self.liked_by.remove(user_id)
            self.likes -= 1
            return True
        return False
    
    def has_liked(self, user_id: str) -> bool:
        """Verificar si el usuario ya dio like"""
        return user_id in self.liked_by
    
    def add_comment(self, comment: Comment):
        """Agregar comentario al post"""
        self.comments.append(comment)
        