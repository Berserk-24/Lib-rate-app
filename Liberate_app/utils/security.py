#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import html
from typing import Optional, List, Dict, Any
import hashlib
import secrets
import string
from datetime import datetime, timedelta
import bleach
from urllib.parse import urlparse


class SecurityValidator:
    """Validador de seguridad para entrada de datos y contenido"""
    
    # Patrones peligrosos comunes
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Scripts
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'<iframe[^>]*>.*?</iframe>',  # iframes
        r'<object[^>]*>.*?</object>',  # Objects
        r'<embed[^>]*>.*?</embed>',  # Embeds
        r'<link[^>]*>',  # Links (pueden cargar CSS malicioso)
        r'<meta[^>]*>',  # Meta tags
        r'expression\s*\(',  # CSS expressions
        r'url\s*\(',  # CSS URLs
        r'@import',  # CSS imports
    ]
    
    # Tags HTML permitidos para contenido básico
    ALLOWED_HTML_TAGS = [
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 
        'ul', 'ol', 'li', 'blockquote', 'h1', 'h2', 'h3'
    ]
    
    # Atributos HTML permitidos
    ALLOWED_HTML_ATTRIBUTES = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height']
    }
    
    @classmethod
    def sanitize_input(cls, input_text: str, allow_html: bool = False) -> str:
        """
        Sanitizar entrada de texto del usuario
        
        Args:
            input_text: Texto a sanitizar
            allow_html: Si permite HTML básico y seguro
            
        Returns:
            Texto sanitizado
        """
        if not input_text or not isinstance(input_text, str):
            return ""
        
        # Normalizar espacios en blanco
        sanitized = cls._normalize_whitespace(input_text)
        
        if allow_html:
            # Permitir HTML básico pero sanitizado
            sanitized = cls._sanitize_html(sanitized)
        else:
            # Escapar todo el HTML
            sanitized = html.escape(sanitized, quote=True)
        
        # Remover patrones peligrosos
        sanitized = cls._remove_dangerous_patterns(sanitized)
        
        # Limitar longitud
        sanitized = cls._limit_length(sanitized, 10000)
        
        return sanitized.strip()
    
    @classmethod
    def _normalize_whitespace(cls, text: str) -> str:
        """Normalizar espacios en blanco y saltos de línea"""
        # Reemplazar múltiples espacios con uno solo
        text = re.sub(r' +', ' ', text)
        
        # Limitar saltos de línea consecutivos
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remover espacios al inicio y final de líneas
        lines = [line.strip() for line in text.split('\n')]
        
        return '\n'.join(lines)
    
    @classmethod
    def _sanitize_html(cls, html_content: str) -> str:
        """Sanitizar contenido HTML permitiendo solo tags seguros"""
        try:
            return bleach.clean(
                html_content,
                tags=cls.ALLOWED_HTML_TAGS,
                attributes=cls.ALLOWED_HTML_ATTRIBUTES,
                strip=True
            )
        except:
            # Si bleach no está disponible, usar escape básico
            return html.escape(html_content, quote=True)
    
    @classmethod
    def _remove_dangerous_patterns(cls, text: str) -> str:
        """Remover patrones peligrosos del texto"""
        for pattern in cls.DANGEROUS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text
    
    @classmethod
    def _limit_length(cls, text: str, max_length: int) -> str:
        """Limitar la longitud del texto"""
        if len(text) > max_length:
            return text[:max_length]
        return text
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Validar formato de email
        
        Args:
            email: Email a validar
            
        Returns:
            True si el email es válido
        """
        if not email or not isinstance(email, str):
            return False
        
        # Patrón básico de validación de email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        return re.match(pattern, email.strip()) is not None
    
    @classmethod
    def validate_username(cls, username: str) -> Dict[str, Any]:
        """
        Validar nombre de usuario
        
        Args:
            username: Username a validar
            
        Returns:
            Dict con resultado de validación
        """
        result = {
            'valid': False,
            'errors': []
        }
        
        if not username or not isinstance(username, str):
            result['errors'].append("El nombre de usuario no puede estar vacío")
            return result
        
        username = username.strip()
        
        # Longitud
        if len(username) < 3:
            result['errors'].append("El nombre de usuario debe tener al menos 3 caracteres")
        elif len(username) > 20:
            result['errors'].append("El nombre de usuario no puede tener más de 20 caracteres")
        
        # Caracteres permitidos
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            result['errors'].append("El nombre de usuario solo puede contener letras, números, guiones y puntos")
        
        # No puede empezar o terminar con caracteres especiales
        if re.match(r'^[._-]|[._-]$', username):
            result['errors'].append("El nombre de usuario no puede empezar o terminar con puntos, guiones o guiones bajos")
        
        # No puede tener caracteres especiales consecutivos
        if re.search(r'[._-]{2,}', username):
            result['errors'].append("El nombre de usuario no puede tener caracteres especiales consecutivos")
        
        result['valid'] = len(result['errors']) == 0
        return result
    
    @classmethod
    def validate_password(cls, password: str) -> Dict[str, Any]:
        """
        Validar fortaleza de contraseña
        
        Args:
            password: Contraseña a validar
            
        Returns:
            Dict con resultado de validación
        """
        result = {
            'valid': False,
            'strength': 'weak',
            'errors': [],
            'suggestions': []
        }
        
        if not password or not isinstance(password, str):
            result['errors'].append("La contraseña no puede estar vacía")
            return result
        
        # Longitud mínima
        if len(password) < 8:
            result['errors'].append("La contraseña debe tener al menos 8 caracteres")
        
        # Verificaciones de fortaleza
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        strength_score = sum([has_lower, has_upper, has_digit, has_special])
        
        if not has_lower:
            result['suggestions'].append("Incluye al menos una letra minúscula")
        if not has_upper:
            result['suggestions'].append("Incluye al menos una letra mayúscula")
        if not has_digit:
            result['suggestions'].append("Incluye al menos un número")
        if not has_special:
            result['suggestions'].append("Incluye al menos un carácter especial")
        
        # Determinar fortaleza
        if len(password) >= 8 and strength_score >= 3:
            result['strength'] = 'strong'
        elif len(password) >= 6 and strength_score >= 2:
            result['strength'] = 'medium'
        else:
            result['strength'] = 'weak'
        
        # Verificar patrones comunes débiles
        weak_patterns = [
            r'123456',
            r'password',
            r'qwerty',
            r'abc123',
            r'admin',
            r'(\w)\1{3,}'  # Caracteres repetidos
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                result['errors'].append("La contraseña contiene patrones comunes inseguros")
                result['strength'] = 'weak'
                break
        
        result['valid'] = len(result['errors']) == 0 and result['strength'] != 'weak'
        return result
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """
        Validar URL
        
        Args:
            url: URL a validar
            
        Returns:
            True si la URL es válida
        """
        if not url or not isinstance(url, str):
            return False
        
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc]) and parsed.scheme in ['http', 'https']
        except:
            return False
    
    @classmethod
    def generate_csrf_token(cls) -> str:
        """
        Generar token CSRF
        
        Returns:
            Token CSRF único
        """
        return secrets.token_urlsafe(32)
    
    @classmethod
    def validate_csrf_token(cls, token: str, stored_token: str) -> bool:
        """
        Validar token CSRF
        
        Args:
            token: Token recibido
            stored_token: Token almacenado
            
        Returns:
            True si el token es válido
        """
        if not token or not stored_token:
            return False
        
        return secrets.compare_digest(token, stored_token)
    
    @classmethod
    def hash_password(cls, password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """
        Hash de contraseña con salt
        
        Args:
            password: Contraseña a hashear
            salt: Salt opcional (se genera si no se proporciona)
            
        Returns:
            Dict con hash y salt
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Usar PBKDF2 para el hash
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100,000 iteraciones
        )
        
        return {
            'hash': password_hash.hex(),
            'salt': salt
        }
    
    @classmethod
    def verify_password(cls, password: str, stored_hash: str, salt: str) -> bool:
        """
        Verificar contraseña contra hash almacenado
        
        Args:
            password: Contraseña a verificar
            stored_hash: Hash almacenado
            salt: Salt usado
            
        Returns:
            True si la contraseña es correcta
        """
        try:
            result = cls.hash_password(password, salt)
            return secrets.compare_digest(result['hash'], stored_hash)
        except:
            return False
    
    @classmethod
    def rate_limit_check(cls, user_id: str, action: str, 
                        max_attempts: int = 5, 
                        time_window: int = 300) -> Dict[str, Any]:
        """
        Verificar límite de velocidad para acciones
        
        Args:
            user_id: ID del usuario
            action: Acción a verificar
            max_attempts: Máximo número de intentos
            time_window: Ventana de tiempo en segundos
            
        Returns:
            Dict con resultado de verificación
        """
        # Esta es una implementación básica que requeriría 
        # un sistema de cache/base de datos para funcionar en producción
        
        current_time = datetime.now()
        
        # En una implementación real, esto se almacenaría en caché/BD
        attempts_key = f"rate_limit:{user_id}:{action}"
        
        return {
            'allowed': True,  # Placeholder - requiere implementación con storage
            'attempts_remaining': max_attempts,
            'reset_time': current_time + timedelta(seconds=time_window),
            'message': "Rate limiting no implementado completamente - requiere storage"
        }
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitizar nombre de archivo
        
        Args:
            filename: Nombre de archivo a sanitizar
            
        Returns:
            Nombre de archivo sanitizado
        """
        if not filename:
            return ""
        
        # Remover caracteres peligrosos
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Remover nombres reservados de Windows
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
        if name_without_ext.upper() in reserved_names:
            filename = f"file_{filename}"
        
        # Limitar longitud
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_length = 255 - len(ext) - 1 if ext else 255
            filename = name[:max_name_length] + ('.' + ext if ext else '')
        
        return filename.strip()
    
    @classmethod
    def is_safe_redirect_url(cls, url: str, allowed_hosts: List[str]) -> bool:
        """
        Verificar si una URL de redirección es segura
        
        Args:
            url: URL a verificar
            allowed_hosts: Lista de hosts permitidos
            
        Returns:
            True si la URL es segura para redirección
        """
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # Solo URLs relativas o de hosts permitidos
            if not parsed.netloc:  # URL relativa
                return True
            
            return parsed.netloc.lower() in [host.lower() for host in allowed_hosts]
        except:
            return False