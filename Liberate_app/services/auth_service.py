#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import uuid
from typing import Optional
from models.user import User
from database.repositories import UserRepository
from utils.security import SecurityValidator

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def hash_password(self, password: str) -> str:
        #Hash de la contraseña usando SHA-256
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, email: str, password: str) -> tuple[bool, str]:
        """
        Registrar nuevo usuario
        Returns: (success, message)
        """
        # Validar entrada
        username = SecurityValidator.sanitize_input(username)
        email = SecurityValidator.sanitize_input(email)
        
        if not username or len(username) < 3:
            return False, "El nombre de usuario debe tener al menos 3 caracteres"
        
        if not email or '@' not in email:
            return False, "Email inválido"
        
        if not password or len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"
        
        # Verificar si el usuario ya existe
        if self.user_repo.get_by_username(username):
            return False, "El nombre de usuario ya existe"
        
        if self.user_repo.get_by_email(email):
            return False, "El email ya está registrado"
        
        # Crear usuario
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)
        user = User(user_id, username, email, password_hash)
        
        if self.user_repo.create(user):
            return True, "Usuario registrado exitosamente"
        else:
            return False, "Error al registrar usuario"
    
    def login_user(self, username: str, password: str) -> tuple[bool, Optional[User], str]:
        """
        Iniciar sesión
        Returns: (success, user, message)
        """
        username = SecurityValidator.sanitize_input(username)
        
        if not username or not password:
            return False, None, "Usuario y contraseña son requeridos"
        
        user = self.user_repo.get_by_username(username)
        if not user:
            return False, None, "Usuario no encontrado"
        
        password_hash = self.hash_password(password)
        if user.password_hash != password_hash:
            return False, None, "Contraseña incorrecta"
        
        return True, user, "Login exitoso"
    
    def get_all_users(self) -> list[User]:
        #Obtener lista de todos los usuarios (para demo)
        return self.user_repo.get_all()