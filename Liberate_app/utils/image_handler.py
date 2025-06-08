#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import uuid
from PIL import Image, ImageTk
from typing import Optional, Tuple
import tkinter as tk

class ImageHandler:
    def __init__(self, base_path: str = "images"):
        self.base_path = base_path
        self.posts_path = os.path.join(base_path, "posts")
        self.profiles_path = os.path.join(base_path, "profiles")
        self.thumbnails_path = os.path.join(base_path, "thumbnails")
        
        # Crear directorios si no existen
        self.create_directories()
        
        # Formatos soportados
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # Tamaños máximos
        self.max_post_size = (800, 600)
        self.max_profile_size = (200, 200)
        self.thumbnail_size = (150, 150)
    
    def create_directories(self):
        """Crear directorios necesarios"""
        for path in [self.base_path, self.posts_path, self.profiles_path, self.thumbnails_path]:
            os.makedirs(path, exist_ok=True)
    
    def is_valid_image(self, file_path: str) -> bool:
        """Verificar si el archivo es una imagen válida"""
        if not os.path.exists(file_path):
            return False
        
        # Verificar extensión
        _, ext = os.path.splitext(file_path.lower())
        if ext not in self.supported_formats:
            return False
        
        # Verificar que se puede abrir como imagen
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    def resize_image(self, image_path: str, max_size: Tuple[int, int]) -> Image.Image:
        """Redimensionar imagen manteniendo proporción"""
        with Image.open(image_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar manteniendo proporción
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            return img.copy()
    
    def save_post_image(self, source_path: str) -> Optional[str]:
        """
        Guardar imagen para post
        Returns: ruta relativa de la imagen guardada o None si hay error
        """
        if not self.is_valid_image(source_path):
            return None
        
        try:
            # Generar nombre único
            file_ext = os.path.splitext(source_path)[1].lower()
            filename = f"post_{uuid.uuid4()}{file_ext}"
            dest_path = os.path.join(self.posts_path, filename)
            
            # Redimensionar y guardar
            resized_img = self.resize_image(source_path, self.max_post_size)
            resized_img.save(dest_path, quality=85, optimize=True)
            
            # Crear thumbnail
            self.create_thumbnail(dest_path, filename)
            
            return os.path.join("posts", filename)
        
        except Exception as e:
            print(f"Error guardando imagen de post: {e}")
            return None
    
    def save_profile_image(self, source_path: str, user_id: str) -> Optional[str]:
        """
        Guardar imagen de perfil
        Returns: ruta relativa de la imagen guardada o None si hay error
        """
        if not self.is_valid_image(source_path):
            return None
        
        try:
            # Generar nombre único
            file_ext = os.path.splitext(source_path)[1].lower()
            filename = f"profile_{user_id}{file_ext}"
            dest_path = os.path.join(self.profiles_path, filename)
            
            # Redimensionar y guardar
            resized_img = self.resize_image(source_path, self.max_profile_size)
            # Hacer cuadrada
            size = min(resized_img.size)
            resized_img = resized_img.crop((
                (resized_img.size[0] - size) // 2,
                (resized_img.size[1] - size) // 2,
                (resized_img.size[0] + size) // 2,
                (resized_img.size[1] + size) // 2
            ))
            resized_img = resized_img.resize(self.max_profile_size, Image.Resampling.LANCZOS)
            resized_img.save(dest_path, quality=85, optimize=True)
            
            return os.path.join("profiles", filename)
        
        except Exception as e:
            print(f"Error guardando imagen de perfil: {e}")
            return None
    
    def create_thumbnail(self, image_path: str, filename: str):
        """Crear thumbnail de una imagen"""
        try:
            thumb_filename = f"thumb_{filename}"
            thumb_path = os.path.join(self.thumbnails_path, thumb_filename)
            
            thumbnail = self.resize_image(image_path, self.thumbnail_size)
            thumbnail.save(thumb_path, quality=75, optimize=True)
        
        except Exception as e:
            print(f"Error creando thumbnail: {e}")
    
    def get_image_for_display(self, relative_path: str, size: Optional[Tuple[int, int]] = None) -> Optional[ImageTk.PhotoImage]:
        """
        Obtener imagen para mostrar en Tkinter
        Args:
            relative_path: ruta relativa desde base_path
            size: tamaño deseado (ancho, alto) o None para tamaño original
        """
        if not relative_path:
            return None
        
        full_path = os.path.join(self.base_path, relative_path)
        
        if not os.path.exists(full_path):
            return None
        
        try:
            with Image.open(full_path) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                if size:
                    img = img.copy()
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                
                return ImageTk.PhotoImage(img)
        
        except Exception as e:
            print(f"Error cargando imagen para display: {e}")
            return None
    
    def get_thumbnail_path(self, image_path: str) -> str:
        """Obtener ruta del thumbnail"""
        filename = os.path.basename(image_path)
        return os.path.join("thumbnails", f"thumb_{filename}")
    
    def delete_image(self, relative_path: str) -> bool:
        """Eliminar imagen y su thumbnail"""
        if not relative_path:
            return False
        
        try:
            # Eliminar imagen principal
            full_path = os.path.join(self.base_path, relative_path)
            if os.path.exists(full_path):
                os.remove(full_path)
            
            # Eliminar thumbnail
            thumb_path = os.path.join(self.base_path, self.get_thumbnail_path(relative_path))
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            
            return True
        
        except Exception as e:
            print(f"Error eliminando imagen: {e}")
            return False
    
    def get_image_info(self, relative_path: str) -> Optional[dict]:
        """Obtener información de la imagen"""
        if not relative_path:
            return None
        
        full_path = os.path.join(self.base_path, relative_path)
        
        if not os.path.exists(full_path):
            return None
        
        try:
            with Image.open(full_path) as img:
                return {
                    'size': img.size,
                    'format': img.format,
                    'mode': img.mode,
                    'file_size': os.path.getsize(full_path)
                }
        except Exception:
            return None