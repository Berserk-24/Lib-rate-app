#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymongo
from pymongo import MongoClient
from typing import Optional
import os   
from datetime import datetime


class DatabaseManager:
    def __init__(self, connection_string: str = None, database_name: str = "social_app"):
        """
        Inicializar el gestor de base de datos
        
        Args:
            connection_string: String de conexión a MongoDB
            database_name: Nombre de la base de datos
        """
        self.connection_string = connection_string or self._get_default_connection_string()
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.db = None
        self._is_connected = False
    
    def _get_default_connection_string(self) -> str:
        """Obtener string de conexión por defecto"""
        # Primero intentar variables de entorno
        mongo_uri = os.getenv('MONGODB_URI')
        if mongo_uri:
            return mongo_uri
        
        # Configuración local por defecto
        host = os.getenv('MONGODB_HOST', 'localhost')
        port = int(os.getenv('MONGODB_PORT', 27017))
        username = os.getenv('MONGODB_USERNAME')
        password = os.getenv('MONGODB_PASSWORD')
        
        if username and password:
            return f"mongodb://{username}:{password}@{host}:{port}/{self.database_name}"
        else:
            return f"mongodb://{host}:{port}"
    
    def connect(self) -> bool:
        """Conectar a la base de datos"""
        try:
            print(f"Conectando a MongoDB: {self.connection_string.replace(os.getenv('MONGODB_PASSWORD', ''), '***') if os.getenv('MONGODB_PASSWORD') else self.connection_string}")
            
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,  # 5 segundos timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Verificar conexión
            self.client.server_info()
            
            # Seleccionar base de datos
            self.db = self.client[self.database_name]
            
            # Configurar índices
            self._setup_indexes()
            
            self._is_connected = True
            print(f"✅ Conectado exitosamente a MongoDB - Base de datos: {self.database_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a MongoDB: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self):
        """Desconectar de la base de datos"""
        try:
            if self.client:
                self.client.close()
                self._is_connected = False
                print("✅ Desconectado de MongoDB")
        except Exception as e:
            print(f"Error desconectando: {e}")
    
    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        if not self._is_connected or not self.client:
            return False
        
        try:
            # Ping al servidor para verificar conexión activa
            self.client.admin.command('ping')
            return True
        except Exception:
            self._is_connected = False
            return False
    
    def reconnect(self) -> bool:
        """Reconectar a la base de datos"""
        self.disconnect()
        return self.connect()
    
    def _setup_indexes(self):
        """Configurar índices de la base de datos"""
        try:
            # Índices para usuarios
            self.db.users.create_index("username", unique=True)
            self.db.users.create_index("email", unique=True)
            self.db.users.create_index("user_id", unique=True)
            
            # Índices para posts
            self.db.posts.create_index("post_id", unique=True)
            self.db.posts.create_index([("timestamp", pymongo.DESCENDING)])
            self.db.posts.create_index("user_id")
            self.db.posts.create_index([("content", "text"), ("purpose", "text"), ("source", "text")])
            
            # Índices para comentarios (dentro de posts)
            self.db.posts.create_index("comments.comment_id")
            self.db.posts.create_index("comments.user_id")
            
            print("✅ Índices configurados correctamente")
            
        except Exception as e:
            print(f"⚠️ Error configurando índices: {e}")
    
    def get_database_stats(self) -> dict:
        """Obtener estadísticas de la base de datos"""
        try:
            if not self.is_connected():
                return {"error": "No conectado a la base de datos"}
            
            stats = {
                "database_name": self.database_name,
                "collections": {},
                "total_size": 0,
                "connection_status": "connected"
            }
            
            # Estadísticas por colección
            collections = ["users", "posts"]
            for collection_name in collections:
                collection = self.db[collection_name]
                count = collection.count_documents({})
                
                # Obtener tamaño aproximado de la colección
                collection_stats = self.db.command("collStats", collection_name)
                size = collection_stats.get("size", 0)
                
                stats["collections"][collection_name] = {
                    "document_count": count,
                    "size_bytes": size,
                    "size_mb": round(size / (1024 * 1024), 2)
                }
                
                stats["total_size"] += size
            
            stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            return {"error": f"Error obteniendo estadísticas: {e}"}
    
    def backup_collection(self, collection_name: str, backup_path: str = None) -> bool:
        """Crear backup de una colección específica"""
        try:
            if not self.is_connected():
                return False
            
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_{collection_name}_{timestamp}.json"
            
            collection = self.db[collection_name]
            documents = list(collection.find({}))
            
            # Convertir ObjectId a string para serialización JSON
            import json
            from bson import ObjectId
            
            def convert_objectid(obj):
                if isinstance(obj, ObjectId):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_objectid(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_objectid(item) for item in obj]
                return obj
            
            serializable_docs = convert_objectid(documents)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_docs, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Backup de {collection_name} creado: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return False
    
    def restore_collection(self, collection_name: str, backup_path: str) -> bool:
        """Restaurar colección desde backup"""
        try:
            if not self.is_connected():
                return False
            
            if not os.path.exists(backup_path):
                print(f"❌ Archivo de backup no encontrado: {backup_path}")
                return False
            
            import json
            with open(backup_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            if not documents:
                print("⚠️ No hay documentos para restaurar")
                return True
            
            collection = self.db[collection_name]
            
            # Limpiar colección existente (opcional)
            # collection.delete_many({})
            
            # Insertar documentos
            if isinstance(documents, list):
                collection.insert_many(documents)
            else:
                collection.insert_one(documents)
            
            print(f"✅ Colección {collection_name} restaurada desde {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error restaurando backup: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """Limpiar datos antiguos"""
        try:
            if not self.is_connected():
                return False
            
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Limpiar posts antiguos sin interacciones
            posts_deleted = self.db.posts.delete_many({
                "timestamp": {"$lt": cutoff_date},
                "likes": 0,
                "shares": 0,
                "comments": {"$size": 0}
            })
            
            print(f"✅ Limpieza completada. Posts antiguos eliminados: {posts_deleted.deleted_count}")
            return True
            
        except Exception as e:
            print(f"❌ Error en limpieza: {e}")
            return False
    
    def test_connection(self) -> dict:
        """Probar conexión y retornar información detallada"""
        result = {
            "success": False,
            "message": "",
            "details": {}
        }
        
        try:
            if not self.client:
                self.connect()
            
            if not self.is_connected():
                result["message"] = "No se pudo establecer conexión"
                return result
            
            # Información del servidor
            server_info = self.client.server_info()
            db_stats = self.get_database_stats()
            
            result.update({
                "success": True,
                "message": "Conexión exitosa",
                "details": {
                    "server_version": server_info.get("version"),
                    "database_name": self.database_name,
                    "collections": list(self.db.list_collection_names()),
                    "stats": db_stats
                }
            })
            
        except Exception as e:
            result["message"] = f"Error de conexión: {e}"
        
        return result
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()