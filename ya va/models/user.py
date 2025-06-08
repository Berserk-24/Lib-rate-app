#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from utils.security import SecurityValidator

class User:
    def __init__(self, user_id: str, username: str, email: str, password_hash: str = ""):
        self.user_id = user_id
        self.username = SecurityValidator.sanitize_input(username)
        self.email = email
        self.password_hash = password_hash
        self.daily_posts = 0
        
        self.last_post_date = today = datetime.now().date()  # Fecha del último post
        if not self.last_post_date:
            self.last_post_date = today #cambio

        self.scroll_time_today = 0
        self.last_scroll_reset = datetime.now().date()
        self.profile_image = None  # Ruta a imagen de perfil
        self.created_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convertir usuario a diccionario para MongoDB"""
        return {
            "_id": self.user_id,
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "daily_posts": self.daily_posts,
            "last_post_date": self.last_post_date.isoformat() if self.last_post_date else None,
            "scroll_time_today": self.scroll_time_today,
            "last_scroll_reset": self.last_scroll_reset.isoformat(),
            "profile_image": self.profile_image,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Crear usuario desde diccionario de MongoDB"""
        user = cls(
            data["user_id"],
            data["username"],
            data["email"],
            data.get("password_hash", "")
        )
        user.daily_posts = data.get("daily_posts", 0)
        user.last_post_date = datetime.fromisoformat(data["last_post_date"]).date() if data.get("last_post_date") else None
        user.scroll_time_today = data.get("scroll_time_today", 0)
        user.last_scroll_reset = datetime.fromisoformat(data["last_scroll_reset"]).date() if data.get("last_scroll_reset") else datetime.now().date()
        user.profile_image = data.get("profile_image")
        user.created_at = data.get("created_at", datetime.now())
        return user
    
    def reset_daily_limits(self):
        """Resetear límites diarios"""
        today = datetime.now().date()
        if self.last_post_date != today:
            self.daily_posts = 0
        if self.last_scroll_reset != today:
            self.scroll_time_today = 0
            self.last_scroll_reset = today