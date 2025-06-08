#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from models.user import User
from services.auth_service import AuthService

class LoginWindow:
    def __init__(self, parent, auth_service: AuthService, login_callback: Callable[[User], None]):
        self.auth_service = auth_service
        self.login_callback = login_callback
        
        # Crear ventana de login
        self.window = tk.Toplevel(parent)
        self.window.title("Liberate App - Login")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        
        # Centrar ventana
        self.center_window()
        
        # Hacer modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Setup UI
        self.setup_ui()
        
        # Focus en username
        self.username_entry.focus()

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)#cambio

    def on_close(self):
             """Cerrar toda la app si se cierra la ventana de login"""
             print("LoginWindow: on_close llamado")
             self.window.grab_release()
             self.window.destroy()
             self.window.master.destroy()
     
    def center_window(self):
        """Centrar ventana en la pantalla"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (300 // 2)
        self.window.geometry(f"400x300+{x}+{y}")
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Estilo
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="Liberate App", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Notebook para login/registro
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Pestaña de login
        self.login_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.login_frame, text="Iniciar Sesión")
        self.setup_login_tab()
        
        # Pestaña de registro
        self.register_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.register_frame, text="Registrarse")
        self.setup_register_tab()
    
    def setup_login_tab(self):
        """Configurar pestaña de login"""
        # Username
        ttk.Label(self.login_frame, text="Usuario:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(self.login_frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        
        # Password
        ttk.Label(self.login_frame, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(self.login_frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Botón login
        login_btn = ttk.Button(self.login_frame, text="Iniciar Sesión", command=self.login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Usuarios demo
        demo_frame = ttk.LabelFrame(self.login_frame, text="Usuarios Demo", padding="10")
        demo_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Button(demo_frame, text="Admin", 
                  command=lambda: self.quick_login("admin", "admin123")).pack(side=tk.LEFT, padx=5)
        ttk.Button(demo_frame, text="User1", 
                  command=lambda: self.quick_login("user1", "user123")).pack(side=tk.LEFT, padx=5)
        ttk.Button(demo_frame, text="User2", 
                  command=lambda: self.quick_login("user2", "user123")).pack(side=tk.LEFT, padx=5)
    
    def setup_register_tab(self):
        """Configurar pestaña de registro"""
        # Username
        ttk.Label(self.register_frame, text="Usuario:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.reg_username_entry = ttk.Entry(self.register_frame, width=25)
        self.reg_username_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Email
        ttk.Label(self.register_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.reg_email_entry = ttk.Entry(self.register_frame, width=25)
        self.reg_email_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Password
        ttk.Label(self.register_frame, text="Contraseña:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.reg_password_entry = ttk.Entry(self.register_frame, width=25, show="*")
        self.reg_password_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Confirm Password
        ttk.Label(self.register_frame, text="Confirmar:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.reg_confirm_entry = ttk.Entry(self.register_frame, width=25, show="*")
        self.reg_confirm_entry.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        # Botón registro
        register_btn = ttk.Button(self.register_frame, text="Registrarse", command=self.register)
        register_btn.grid(row=4, column=0, columnspan=2, pady=20)
    
    def quick_login(self, username: str, password: str):
        """Login rápido con usuarios demo"""
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, username)
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)
        self.login()
    
    def login(self):
        """Procesar login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Por favor ingresa usuario y contraseña")
            return
        
        success, user, message = self.auth_service.login_user(username, password)
        
        if success:
            self.window.destroy()
            self.login_callback(user)
        else:
            messagebox.showerror("Error de Login", message)
    
    def register(self):
        """Procesar registro"""
        username = self.reg_username_entry.get().strip()
        email = self.reg_email_entry.get().strip()
        password = self.reg_password_entry.get()
        confirm_password = self.reg_confirm_entry.get()
        
        if not all([username, email, password, confirm_password]):
            messagebox.showerror("Error", "Por favor completa todos los campos")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Las contraseñas no coinciden")
            return
        
        success, message = self.auth_service.register_user(username, email, password)
        
        if success:
            messagebox.showinfo("Éxito", message)
            # Cambiar a pestaña de login
            self.notebook.select(0)
            # Limpiar campos de registro
            self.reg_username_entry.delete(0, tk.END)
            self.reg_email_entry.delete(0, tk.END)
            self.reg_password_entry.delete(0, tk.END)
            self.reg_confirm_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error de Registro", message)