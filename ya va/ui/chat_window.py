import tkinter as tk
from tkinter import ttk, scrolledtext
import uuid
from models.message import Message


class ChatWindow:
    def __init__(self, parent, current_user, other_user, message_repo):
        self.current_user = current_user
        self.other_user = other_user
        self.message_repo = message_repo

        self.window = tk.Toplevel(parent)
        self.window.title(f"Chat con {other_user.username}")
        self.window.geometry("400x600")

        self.messages_area = scrolledtext.ScrolledText(self.window, state='disabled')
        self.messages_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.entry = ttk.Entry(self.window)
        self.entry.pack(fill="x", padx=10, pady=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send_message())

        send_btn = ttk.Button(self.window, text="Enviar", command=self.send_message)
        send_btn.pack(pady=(0, 10))

        location_btn = ttk.Button(self.window, text="Planear encuentro", command=self.share_location)
        location_btn.pack(pady=(0, 10))

        self.load_messages()  

        # Aquí puedes cargar mensajes previos y mostrar en messages_area

    def send_message(self):
        content = self.entry.get().strip()
        if not content:
            return

        # Suponiendo que tienes self.current_user y self.other_user definidos
        msg = Message(
            message_id=str(uuid.uuid4()),
            sender_id=self.current_user.user_id,
            receiver_id=self.other_user.user_id,
            content=content
        )
        self.message_repo.save_message(msg)
        self.entry.delete(0, tk.END)
        self.load_messages()  # Recarga el área de mensajes

    def load_messages(self):

        self.messages_area.config(state='normal')
        self.messages_area.delete(1.0, tk.END)
        messages = self.message_repo.get_messages_between(self.current_user.user_id, self.other_user.user_id)
        for msg in messages:
            sender = "Tú" if msg["sender_id"] == self.current_user.user_id else self.other_user.username
            self.messages_area.insert(tk.END, f"{sender}: {msg['content']}\n")
        self.messages_area.config(state='disabled')

    def share_location(self):
        # Pide la ubicación al usuario (ejemplo simple con un input dialog)
        from tkinter.simpledialog import askstring
        location = askstring("Compartir ubicación", "Ingresa tu ubicación (ej: Parque Central, 10.123, -74.123):")
        if not location:
            return
        
        msg = Message(
            message_id=str(uuid.uuid4()),
            sender_id=self.current_user.user_id,
            receiver_id=self.other_user.user_id,
            content=f"[Ubicación compartida]: {location}",
            location=location
        )
        self.message_repo.save_message(msg)
        self.load_messages()

    def plan_meeting(self):
    # Localización simulada (puedes personalizar el texto)
        simulated_location = "Café Central, Calle 123, 10.123, -74.123"
        msg = Message(
            message_id=str(uuid.uuid4()),
            sender_id=self.current_user.user_id,
            receiver_id=self.other_user.user_id,
            content=f"[Encuentro planeado]: {simulated_location}",
            location=simulated_location
        )
        self.message_repo.save_message(msg)
        self.load_messages()
