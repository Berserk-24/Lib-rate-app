#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List

from models.user import User
from models.post import Post
from services.post_service import PostService
from services.scroll_service import ScrollLimitService
from ui.reactive_ui import ReactiveUI
from utils.image_handler import ImageHandler

class MainWindow:
    def __init__(self, root, user: User, post_service: PostService, 
                 scroll_service: ScrollLimitService, reactive_ui: ReactiveUI,
                 image_handler: ImageHandler, user_repo, message_repo):
        
        self.root = root
        self.current_user = user
        self.post_service = post_service
        self.scroll_service = scroll_service
        self.reactive_ui = reactive_ui
        self.reactive_ui.subscribe("user_updated", self.on_user_updated)#cambio
        self.user_repo = user_repo

        self.image_handler = image_handler
        self.message_repo = message_repo

        # Estado
        self.scroll_start_time = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.selected_image_path = None
        
        # Configurar ventana
        self.setup_window()
        
        # Configurar UI reactiva
        self.setup_reactive_callbacks()
        
        # Crear interfaz
        self.setup_ui()
        
        # Cargar datos iniciales
        self.refresh_posts()

    def on_user_updated(self, user): #
        self.current_user = user
        self.current_user.daily_posts = user.daily_posts#
        self.current_user.last_post_date = user.last_post_date#
        self.update_posts_counter() #cambio
        self.update_stats()
    
    def setup_window(self):
        """Configurar ventana principal"""
        self.root.title(f"Liberate App - {self.current_user.username}")
        self.root.geometry("900x700")
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Post.TFrame', relief='raised', borderwidth=1)
        style.configure('Liked.TButton', foreground='red')

    def setup_reactive_callbacks(self):
        """Configurar callbacks reactivos"""
        self.reactive_ui.subscribe("post_created", self.on_post_created)
        self.reactive_ui.subscribe("scroll_limit_reached", self.on_scroll_limit_reached)
    
    def on_post_created(self, data):
        """Callback reactivo para nuevos posts"""
        self.root.after(0, self.refresh_posts)
        self.root.after(0, self.update_posts_counter)
    
    def on_scroll_limit_reached(self, data):
        """Callback reactivo para límite de scroll alcanzado"""
        self.root.after(0, lambda: messagebox.showwarning(
            "Límite Alcanzado", 
            "Has alcanzado tu límite de scroll diario (30 minutos). ¡Toma un descanso!"
        ))
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Frame superior con información del usuario
        self.setup_header()
        
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Pestañas
        self.setup_feed_tab()
        self.setup_create_tab()
        self.setup_profile_tab()
        self.setup_chat_tab()
        
        # Configurar tracking de scroll
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def setup_header(self):
        """Configurar header con información del usuario"""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Información del usuario
        user_info = ttk.Label(header_frame, 
                             text=f"Bienvenido, {self.current_user.username}", 
                             style='Header.TLabel')
        user_info.pack(side="left")
        
        # Contador de posts
        self.posts_label = ttk.Label(header_frame, text="")
        self.posts_label.pack(side="right")
        self.update_posts_counter()
        
        # Separador
        ttk.Separator(self.root, orient='horizontal').pack(fill="x", padx=10)
    
    def setup_feed_tab(self):
        """Configurar pestaña de feed"""
        self.feed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.feed_frame, text="🏠 Feed")
        
        # Frame para controles
        controls_frame = ttk.Frame(self.feed_frame)
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(controls_frame, text="🔄 Refrescar", 
                  command=self.refresh_posts).pack(side="left")
        
        # Frame scrollable para posts
        self.setup_scrollable_posts_area()
    
    def setup_scrollable_posts_area(self):
        """Configurar área scrollable para posts"""
        # Canvas y scrollbar
        canvas_frame = ttk.Frame(self.feed_frame)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.posts_canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.posts_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.posts_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.posts_canvas.configure(scrollregion=self.posts_canvas.bbox("all"))
        )

        # Crea la ventana en (0,0) y guarda el id
        self._posts_window = self.posts_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="n")
        self.posts_canvas.configure(yscrollcommand=scrollbar.set)

        self.posts_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Vincula el evento de cambio de tamaño para centrar el frame
        self.posts_canvas.bind("<Configure>", self._center_scrollable_frame)

    def _center_scrollable_frame(self, event):
        canvas_width = event.width
        # Centra el frame ajustando su ancho al del canvas
        self.posts_canvas.itemconfig(self._posts_window, width=canvas_width)

    def _on_mousewheel(self, event):
        """Manejar scroll del mouse"""
        self.posts_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def setup_create_tab(self):
        self.create_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.create_frame, text="✏️ Crear Post")

        canvas = tk.Canvas(self.create_frame)
        scrollbar = ttk.Scrollbar(self.create_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Crea la ventana en (0,0) y guarda el id
        self._create_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Centrar el formulario al cambiar el tamaño
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self._create_window, width=e.width))

        # Contenido del formulario
        self.setup_create_form(scrollable_frame)
    
    def setup_create_form(self, parent):
        """Configurar formulario de creación de posts"""
        form_frame = ttk.Frame(parent, padding="10")
        form_frame.pack(expand=True)
        
        # Contenido del post
        ttk.Label(form_frame, text="Contenido del post:", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        self.content_text = scrolledtext.ScrolledText(form_frame, height=6, wrap="word")
        self.content_text.pack(fill="x", pady=(0, 10))
        
        # Propósito
        ttk.Label(form_frame, text="¿Por qué compartes esto? (Propósito):", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        self.purpose_text = scrolledtext.ScrolledText(form_frame, height=4, wrap="word")
        self.purpose_text.pack(fill="x", pady=(0, 10))
        
        # Fuente
        ttk.Label(form_frame, text="Fuente (si es noticia):", font=('Arial', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        self.source_entry = ttk.Entry(form_frame, font=('Arial', 10))
        self.source_entry.pack(fill="x", pady=(0, 10))
        
        # Sección de imagen
        image_frame = ttk.LabelFrame(form_frame, text="Imagen (opcional)", padding="10")
        image_frame.pack(fill="x", pady=(0, 10))
        
        # Botones de imagen
        img_buttons_frame = ttk.Frame(image_frame)
        img_buttons_frame.pack(fill="x")
        
        ttk.Button(img_buttons_frame, text="📷 Seleccionar Imagen", 
                  command=self.select_image).pack(side="left", padx=(0, 5))
        ttk.Button(img_buttons_frame, text="❌ Quitar Imagen", 
                  command=self.remove_image).pack(side="left")
        
        # Preview de imagen
        self.image_preview_frame = ttk.Frame(image_frame)
        self.image_preview_frame.pack(fill="x", pady=(10, 0))
        
        self.image_preview_label = ttk.Label(self.image_preview_frame, text="No hay imagen seleccionada")
        self.image_preview_label.pack()
        
        # Botón publicar
        publish_frame = ttk.Frame(form_frame)
        publish_frame.pack(fill="x", pady=(20, 0))
        
        ttk.Button(publish_frame, text="📝 Publicar Post", 
                  command=self.create_post).pack(side="right")
    
    def setup_profile_tab(self):
        """Configurar pestaña de perfil"""
        self.profile_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.profile_frame, text="👤 Perfil")
        
        profile_content = ttk.Frame(self.profile_frame, padding="20")
        profile_content.pack(fill="both", expand=True)
        
        # Información del usuario
        ttk.Label(profile_content, text=f"Usuario: {self.current_user.username}", 
                 font=('Arial', 14, 'bold')).pack(anchor="w", pady=(0, 10))
        ttk.Label(profile_content, text=f"Email: {self.current_user.email}").pack(anchor="w", pady=(0, 5))
        ttk.Label(profile_content, text=f"Miembro desde: {self.current_user.created_at.strftime('%Y-%m-%d')}").pack(anchor="w", pady=(0, 10))
        
        # Estadísticas de uso
        stats_frame = ttk.LabelFrame(profile_content, text="Estadísticas de Uso", padding="10")
        stats_frame.pack(fill="x", pady=(0, 10))
        
        self.stats_posts_label = ttk.Label(stats_frame, text="")
        self.stats_posts_label.pack(anchor="w")
        
        self.stats_scroll_label = ttk.Label(stats_frame, text="")
        self.stats_scroll_label.pack(anchor="w")
        
        self.update_stats()
        
        # Botón de logout
        ttk.Button(profile_content, text="🚪 Cerrar Sesión", 
                  command=self.logout).pack(anchor="w", pady=(20, 0))
    
    def select_image(self):
        """Seleccionar imagen para el post"""
        file_types = [
            ("Imágenes", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("GIF", "*.gif"),
            ("Todos los archivos", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=file_types
        )
        
        if file_path:
            if self.image_handler.is_valid_image(file_path):
                self.selected_image_path = file_path
                self.update_image_preview()
            else:
                messagebox.showerror("Error", "El archivo seleccionado no es una imagen válida")
    
    def remove_image(self):
        """Quitar imagen seleccionada"""
        self.selected_image_path = None
        self.update_image_preview()
    
    def update_image_preview(self):
        """Actualizar preview de la imagen"""
        if self.selected_image_path:
            try:
                # Mostrar thumbnail
                img = self.image_handler.get_image_for_display(
                    self.selected_image_path, (100, 100)
                )
                if img:
                    self.image_preview_label.config(image=img, text="")
                    self.image_preview_label.image = img  # Mantener referencia
                else:
                    self.image_preview_label.config(image="", text="Error cargando imagen")
            except Exception as e:
                self.image_preview_label.config(image="", text=f"Error: {str(e)}")
        else:
            self.image_preview_label.config(image="", text="No hay imagen seleccionada")
            self.image_preview_label.image = None
    
    def on_tab_changed(self, event):
        """Manejar cambio de pestañas para tracking de scroll"""
        selected_tab = event.widget.tab('current')['text']
        
        if "Feed" in selected_tab:
            if not self.scroll_service.check_scroll_limit(self.current_user):
                messagebox.showwarning("Límite Alcanzado", "Has alcanzado tu límite de scroll diario")
                # Cambiar a otra pestaña
                self.notebook.select(1)
                return
            self.scroll_start_time = time.time()
        else:
            if self.scroll_start_time and "Feed" not in selected_tab:
                scroll_time = int(time.time() - self.scroll_start_time)
                self.scroll_service.add_scroll_time(self.current_user, scroll_time)
                self.scroll_start_time = None
    
    def create_post(self):
        """Crear nuevo post"""
        content = self.content_text.get("1.0", "end-1c").strip()
        purpose = self.purpose_text.get("1.0", "end-1c").strip()
        source = self.source_entry.get().strip()
        
        if not content:
            messagebox.showerror("Error", "El contenido no puede estar vacío")
            return
        
        try:
            # Guardar imagen si está seleccionada
            image_path = None
            if self.selected_image_path:
                image_path = self.image_handler.save_post_image(self.selected_image_path)
                if not image_path:
                    messagebox.showerror("Error", "No se pudo guardar la imagen")
                    return
            
            success = self.post_service.create_post(
                self.current_user, content, purpose, source, image_path
            )
            
            if success:
                messagebox.showinfo("Éxito", "Post creado exitosamente")
                # Limpiar formulario
                self.content_text.delete("1.0", "end")
                self.purpose_text.delete("1.0", "end")
                self.source_entry.delete(0, "end")
                self.remove_image()
                # Cambiar a feed
                self.notebook.select(0)
            else:
                messagebox.showerror("Error", "No se pudo crear el post")
        
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def refresh_posts(self):
        """Refrescar lista de posts"""
        def load_posts():
            posts = self.post_service.get_posts()
            self.root.after(0, lambda: self.display_posts(posts))
        
        self.executor.submit(load_posts)
    
    def display_posts(self, posts: List[Post]):
        """Mostrar posts en el feed"""
        # Limpiar posts existentes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not posts:
            no_posts_label = ttk.Label(self.scrollable_frame, 
                                     text="No hay posts aún. ¡Sé el primero en publicar!",
                                     font=('Arial', 12))
            no_posts_label.pack(pady=50)
            return
        
        for post in posts:
            self.create_post_widget(post)
    
    def create_post_widget(self, post: Post):
        """Crear widget para un post"""
        post_frame = ttk.Frame(self.scrollable_frame, style='Post.TFrame', padding="10")
        post_frame.pack(fill="x", pady=5, padx=5)
        
        # Header del post
        header_frame = ttk.Frame(post_frame)
        header_frame.pack(fill="x", pady=(0, 5))
        
        # Usuario y fecha
        user_label = ttk.Label(header_frame, text=f"@{post.username}", 
                              font=('Arial', 10, 'bold'))
        user_label.pack(side="left")
        
        date_label = ttk.Label(header_frame, 
                              text=post.timestamp.strftime("%Y-%m-%d %H:%M"),
                              foreground="gray")
        date_label.pack(side="right")
        
        # Contenido del post
        content_label = ttk.Label(post_frame, text=post.content, 
                                 wraplength=800, justify="left")
        content_label.pack(fill="x", pady=(0, 5))
        
        # Propósito si existe
        if post.purpose:
            purpose_frame = ttk.Frame(post_frame)
            purpose_frame.pack(fill="x", pady=(0, 5))
            
            ttk.Label(purpose_frame, text="💭 Propósito: ", 
                     font=('Arial', 9, 'italic')).pack(side="left")
            ttk.Label(purpose_frame, text=post.purpose, 
                     font=('Arial', 9, 'italic'), 
                     wraplength=700).pack(side="left", fill="x", expand=True)
        
        # Imagen si existe
        if post.image_path:
            self.add_image_to_post(post_frame, post.image_path)
        
        # Fuente si existe
        if post.source:
            source_frame = ttk.Frame(post_frame)
            source_frame.pack(fill="x", pady=(0, 5))
            
            ttk.Label(source_frame, text="🔗 Fuente: ", 
                     font=('Arial', 9)).pack(side="left")
            ttk.Label(source_frame, text=post.source, 
                     font=('Arial', 9, 'underline'), 
                     foreground="blue").pack(side="left")
        
        # Botones de interacción
        self.add_interaction_buttons(post_frame, post)
        
        # Separador
        ttk.Separator(post_frame, orient='horizontal').pack(fill="x", pady=(10, 0))
    
    def add_image_to_post(self, parent_frame, image_path):
        """Agregar imagen al post"""
        try:
            img = self.image_handler.get_image_for_display(image_path, (400, 300))
            if img:
                img_label = ttk.Label(parent_frame, image=img)
                img_label.image = img  # Mantener referencia
                img_label.pack(pady=5)
        except Exception as e:
            print(f"Error mostrando imagen: {e}")
    
    def add_interaction_buttons(self, parent_frame, post):
        """Agregar botones de interacción al post"""
        buttons_frame = ttk.Frame(parent_frame)
        buttons_frame.pack(fill="x", pady=(5, 0))
        
        # Like button
        like_btn = tk.Button(
            buttons_frame,
            text="💖" if post.has_liked(self.current_user.user_id) else "🤍",
            fg="red" if post.has_liked(self.current_user.user_id) else "black",
            command=lambda: self.toggle_like(post, like_btn),
            relief=tk.FLAT,
            font=("Arial", 14)
        )
        like_btn.pack(side="left", padx=(0, 5))
        
        # Share button
        share_btn = ttk.Button(buttons_frame, 
                              text=f"🔄 {post.shares}",
                              command=lambda: self.share_post(post))
        share_btn.pack(side="left", padx=(0, 5))
        
        # Comment button
        comment_btn = ttk.Button(buttons_frame, 
                                text=f"💬 {len(post.comments)}",
                                command=lambda: self.show_comments(post))
        comment_btn.pack(side="left")
    
    def toggle_like(self, post, like_btn):
        """Toggle like en un post"""
        success = self.post_service.toggle_like(post.post_id, self.current_user.user_id)
        if success:
            self.refresh_posts()
            user_id = self.current_user.user_id

        if post.has_liked(user_id):
            post.remove_like(user_id)
        else:
            post.add_like(user_id)

        # Actualiza el texto y color del botón
        like_btn.config(
            text="❤️" if post.has_liked(user_id) else "🤍",
            fg="red" if post.has_liked(user_id) else "black"
        )
    
    def share_post(self, post):
        """Compartir post"""
        success = self.post_service.share_post(post.post_id)
        if success:
            messagebox.showinfo("Éxito", "Post compartido")
            self.refresh_posts()
    
    def show_comments(self, post):
        """Mostrar comentarios del post"""
        # Crear ventana de comentarios
        comments_window = tk.Toplevel(self.root)
        comments_window.title(f"Comentarios - Post de @{post.username}")
        comments_window.geometry("500x400")
        
        # Lista de comentarios
        comments_frame = ttk.Frame(comments_window)
        comments_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Mostrar comentarios existentes
        for comment in post.comments:
            comment_widget = ttk.Frame(comments_frame)
            comment_widget.pack(fill="x", pady=2)
            
            ttk.Label(comment_widget, text=f"@{comment.username}: {comment.content}",
                     wraplength=450).pack(fill="x")
        
        # Campo para nuevo comentario
        new_comment_frame = ttk.Frame(comments_window)
        new_comment_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        comment_entry = ttk.Entry(new_comment_frame)
        comment_entry.pack(side="left", fill="x", expand=True)
        
        def add_comment():
            content = comment_entry.get().strip()
            if content:
                success = self.post_service.add_comment(
                    post.post_id, self.current_user.user_id, 
                    self.current_user.username, content
                )
                if success:
                    comments_window.destroy()
                    self.refresh_posts()
                elif success is False:
                    messagebox.showerror("Error", "No se pudo agregar el comentario. Límite alcanzado.")
        
        ttk.Button(new_comment_frame, text="Comentar", 
                  command=add_comment).pack(side="right", padx=(5, 0))
        
        comment_entry.bind("<Return>", lambda e: add_comment())
        comment_entry.focus()
    
    def update_posts_counter(self):
        """Actualizar contador de posts diarios"""
        remaining = max(0, 3 - self.current_user.daily_posts)
        self.posts_label.config(text=f"Posts restantes hoy: {remaining}")
    
    def update_stats(self):
        """Actualizar estadísticas del usuario"""
        self.stats_posts_label.config(text=f"Posts publicados hoy: {self.current_user.daily_posts}/3")
        
        scroll_minutes = self.current_user.scroll_time_today // 60
        scroll_remaining = max(0, 30 - scroll_minutes)
        self.stats_scroll_label.config(text=f"Tiempo de scroll: {scroll_minutes} min (quedan {scroll_remaining} min)")
    
    def logout(self):
        """Cerrar sesión"""
        result = messagebox.askyesno("Cerrar Sesión", "¿Estás seguro de que quieres cerrar sesión?")
        if result:
            self.root.quit()
    
    def cleanup(self):
        """Limpiar recursos"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

    def setup_chat_tab(self):
        """Configurar pestaña de chat"""
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="💬 Chat")

        # Lista de usuarios
        users = self.user_repo.get_all_users()  # Debes tener este método en tu UserRepository
        usernames = [u.username for u in users if u.user_id != self.current_user.user_id]

        self.user_listbox = tk.Listbox(self.chat_frame, height=10)
        for username in usernames:
            self.user_listbox.insert(tk.END, username)
        self.user_listbox.pack(pady=10)

        chat_btn = ttk.Button(self.chat_frame, text="Iniciar chat", command=self.open_selected_chat)
        chat_btn.pack(pady=10)

    def open_selected_chat(self):
        """Abrir chat con el usuario seleccionado en la lista"""
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showinfo("Selecciona un usuario", "Por favor selecciona un usuario para chatear.")
            return
        username = self.user_listbox.get(selection[0])
        user = self.user_repo.get_by_username(username)
        from ui.chat_window import ChatWindow
        ChatWindow(self.root, self.current_user, user, self.message_repo)