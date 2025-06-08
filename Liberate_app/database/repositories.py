#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional
from datetime import datetime
import pymongo
from models.user import User
from models.post import Post
from database.db_manager import DatabaseManager

class UserRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.collection = db_manager.db.users
    
    def get_all_users(self):
        """Devuelve una lista de todos los usuarios"""
        users = []
        for doc in self.collection.find():
            users.append(User(
                user_id=doc.get("user_id"),
                username=doc.get("username"),
                email=doc.get("email"),
                password_hash=doc.get("password_hash", "")
            ))
        return users

    def create(self, user: User) -> bool:
        """Crear nuevo usuario"""
        try:
            user_doc = user.to_dict()
            self.collection.insert_one(user_doc)
            return True
        except pymongo.errors.DuplicateKeyError:
            return False
        except Exception as e:
            print(f"Error creando usuario: {e}")
            return False
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Obtener usuario por nombre de usuario"""
        try:
            user_doc = self.collection.find_one({"username": username})
            if user_doc:
                return User.from_dict(user_doc)
            return None
        except Exception as e:
            print(f"Error obteniendo usuario por username: {e}")
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        try:
            user_doc = self.collection.find_one({"email": email})
            if user_doc:
                return User.from_dict(user_doc)
            return None
        except Exception as e:
            print(f"Error obteniendo usuario por email: {e}")
            return None
        
class PostRepository: #agregado
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.collection = db_manager.db.posts

    def create(self, post: Post) -> bool:
        """Crear nuevo post"""
        try:
            post_doc = post.to_dict()
            self.collection.insert_one(post_doc)
            return True
        except Exception as e:
            print(f"Error creando post: {e}")
            return False

    def get_all(self) -> List[Post]:
        """Obtener todos los posts"""
        try:
            posts_cursor = self.collection.find().sort("created_at", -1)
            return [Post.from_dict(doc) for doc in posts_cursor]
        except Exception as e:
            print(f"Error obteniendo posts: {e}")
            return []

    def get_by_user(self, user_id: str) -> List[Post]:
        """Obtener posts por ID de usuario"""
        try:
            posts_cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
            return [Post.from_dict(doc) for doc in posts_cursor]
        except Exception as e:
            print(f"Error obteniendo posts del usuario: {e}")
            return []

class MessageRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.collection = db_manager.db.messages

    def save_message(self, message):
        self.collection.insert_one(message.to_dict())

    def get_messages_between(self, user1_id, user2_id):
        return list(self.collection.find({
            "$or": [
                {"sender_id": user1_id, "receiver_id": user2_id},
                {"sender_id": user2_id, "receiver_id": user1_id}
            ]
        }).sort("timestamp", 1))
