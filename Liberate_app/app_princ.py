#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import threading
from datetime import datetime
import uuid

# Importar módulos locales
from models.user import User
from models.post import Post
from services.auth_service import AuthService
from services.post_service import PostService
from services.scroll_service import ScrollLimitService
from database.db_manager import DatabaseManager
from ui.reactive_ui import ReactiveUI
from database.repositories import UserRepository, PostRepository
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from utils.image_handler import ImageHandler
from database.repositories import UserRepository, PostRepository, MessageRepository

class SocialApp:
    def __init__(self):
        self.root = tk.Tk()
        
        # Inicializar componentes
        self.db_manager = DatabaseManager()
        self.db_manager.connect() # cambio

        self.user_repo = UserRepository(self.db_manager)
        self.post_repo = PostRepository(self.db_manager) # cambio
        
        self.reactive_ui = ReactiveUI()  # UI reactiva

        # Servicios
        self.auth_service = AuthService(self.user_repo)
        self.post_service = PostService(self.db_manager, self.reactive_ui)# cambio
        self.scroll_service = ScrollLimitService(self.db_manager) #cambio
        
        # UI reactiva
        self.post_service.attach(self.reactive_ui)
        self.scroll_service.attach(self.reactive_ui)
        
        # Estado
        self.current_user = None
        self.main_window = None
        
        # Manejador de imágenes
        self.image_handler = ImageHandler()
        
        self.message_repo = MessageRepository(self.db_manager)

        # Mostrar login
        self.show_login()
    
    def show_login(self):
        #Mostrar ventana de login
        self.login_window = LoginWindow(self.root, self.auth_service, self.on_login_success)
    
    def on_login_success(self, user: User):
        #Callback cuando el login es exitoso
        self.current_user = user
        if hasattr(self, 'login_window') and self.login_window:
            self.login_window.window.destroy() 
        self.show_main_window()
    
    def show_main_window(self):
        #Mostrar ventana principal después del login
        self.reactive_ui = ReactiveUI()
        self.post_service = PostService(self.db_manager, self.reactive_ui)

        self.root.deiconify()  # Mostrar ventana principal

        self.main_window = MainWindow(
            self.root,
            self.current_user,
            self.post_service,
            self.scroll_service,
            self.reactive_ui,
            self.image_handler,
            self.user_repo,
            self.message_repo
        )
    
    def run(self):
        #Ejecutar 
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window.cleanup()

if __name__ == "__main__":
    try:
    
        app = SocialApp()
        app.run()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()