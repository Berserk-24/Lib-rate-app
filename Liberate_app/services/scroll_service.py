#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, date
from models.user import User
from database.db_manager import DatabaseManager


class ScrollLimitService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.users_collection = db_manager.db.users
        self.DAILY_SCROLL_LIMIT = 1800  # 30 minutos en segundos
        self._observers = []  #cambio

    def attach(self, observer): #
        """Agregar un observador para notificaciones de cambios"""
        if observer not in self._observers:
            self._observers.append(observer)#cambio

    def check_scroll_limit(self, user: User) -> bool:
        """Verificar si el usuario puede seguir haciendo scroll"""
        try:
            # Resetear límites si es un nuevo día
            self._reset_daily_limits_if_needed(user)
            
            # Verificar límite de tiempo
            return user.scroll_time_today < self.DAILY_SCROLL_LIMIT
            
        except Exception as e:
            print(f"Error verificando límite de scroll: {e}")
            return False
    
    def add_scroll_time(self, user: User, seconds: int) -> bool:
        """Agregar tiempo de scroll al usuario"""
        try:
            # Resetear límites si es un nuevo día
            self._reset_daily_limits_if_needed(user)
            
            # Agregar tiempo de scroll
            user.scroll_time_today += seconds
            
            # Asegurar que no exceda el límite máximo
            if user.scroll_time_today > self.DAILY_SCROLL_LIMIT:
                user.scroll_time_today = self.DAILY_SCROLL_LIMIT
            
            # Actualizar en base de datos
            result = self.users_collection.update_one(
                {"_id": user.user_id},
                {
                    "$set": {
                        "scroll_time_today": user.scroll_time_today,
                        "last_scroll_reset": user.last_scroll_reset.isoformat()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error agregando tiempo de scroll: {e}")
            return False
    
    def get_remaining_scroll_time(self, user: User) -> int:
        """Obtener tiempo de scroll restante en segundos"""
        try:
            self._reset_daily_limits_if_needed(user)
            remaining = self.DAILY_SCROLL_LIMIT - user.scroll_time_today
            return max(0, remaining)
            
        except Exception as e:
            print(f"Error obteniendo tiempo restante: {e}")
            return 0
    
    def get_scroll_stats(self, user: User) -> dict:
        """Obtener estadísticas de scroll del usuario"""
        try:
            self._reset_daily_limits_if_needed(user)
            
            used_minutes = user.scroll_time_today // 60
            used_seconds = user.scroll_time_today % 60
            remaining_seconds = self.get_remaining_scroll_time(user)
            remaining_minutes = remaining_seconds // 60
            
            return {
                "total_limit_minutes": self.DAILY_SCROLL_LIMIT // 60,
                "used_time_seconds": user.scroll_time_today,
                "used_time_minutes": used_minutes,
                "used_time_formatted": f"{used_minutes}:{used_seconds:02d}",
                "remaining_time_seconds": remaining_seconds,
                "remaining_time_minutes": remaining_minutes,
                "remaining_time_formatted": f"{remaining_minutes}:{(remaining_seconds % 60):02d}",
                "percentage_used": (user.scroll_time_today / self.DAILY_SCROLL_LIMIT) * 100,
                "is_limit_reached": user.scroll_time_today >= self.DAILY_SCROLL_LIMIT
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def reset_user_scroll_time(self, user: User) -> bool:
        """Resetear tiempo de scroll del usuario (para admin)"""
        try:
            user.scroll_time_today = 0
            user.last_scroll_reset = datetime.now().date()
            
            result = self.users_collection.update_one(
                {"_id": user.user_id},
                {
                    "$set": {
                        "scroll_time_today": 0,
                        "last_scroll_reset": user.last_scroll_reset.isoformat()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error reseteando tiempo de scroll: {e}")
            return False
    
    def _reset_daily_limits_if_needed(self, user: User):
        """Resetear límites diarios si es necesario"""
        today = datetime.now().date()
        
        if user.last_scroll_reset != today:
            user.scroll_time_today = 0
            user.last_scroll_reset = today
            
            # Actualizar en base de datos
            self.users_collection.update_one(
                {"_id": user.user_id},
                {
                    "$set": {
                        "scroll_time_today": 0,
                        "last_scroll_reset": today.isoformat()
                    }
                }
            )
    
    def get_all_users_scroll_stats(self) -> list:
        """Obtener estadísticas de scroll de todos los usuarios (para admin)"""
        try:
            users_data = self.users_collection.find({}, {
                "username": 1,
                "scroll_time_today": 1,
                "last_scroll_reset": 1
            })
            
            stats = []
            for user_doc in users_data:
                # Crear objeto User temporal para usar las funciones existentes
                temp_user = User(
                    user_doc["_id"],
                    user_doc["username"],
                    "",  # email no necesario aquí
                    ""   # password no necesario aquí
                )
                temp_user.scroll_time_today = user_doc.get("scroll_time_today", 0)
                temp_user.last_scroll_reset = datetime.fromisoformat(
                    user_doc.get("last_scroll_reset", datetime.now().date().isoformat())
                ).date()
                
                user_stats = self.get_scroll_stats(temp_user)
                user_stats["username"] = user_doc["username"]
                stats.append(user_stats)
            
            return stats
            
        except Exception as e:
            print(f"Error obteniendo estadísticas globales: {e}")
            return []
    
    def is_scroll_warning_needed(self, user: User) -> bool:
        """Verificar si se debe mostrar advertencia de tiempo"""
        try:
            remaining = self.get_remaining_scroll_time(user)
            # Mostrar advertencia cuando quedan 5 minutos o menos
            return remaining <= 300 and remaining > 0
            
        except Exception as e:
            print(f"Error verificando advertencia: {e}")
            return False
    
    def get_daily_usage_report(self, user: User) -> str:
        """Generar reporte de uso diario"""
        try:
            stats = self.get_scroll_stats(user)
            
            if not stats:
                return "No se pudieron obtener las estadísticas"
            
            report = f"""
📊 Reporte de Uso Diario - {datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Usuario: {user.username}
⏰ Tiempo usado: {stats['used_time_formatted']} / 30:00
⏳ Tiempo restante: {stats['remaining_time_formatted']}
📈 Porcentaje usado: {stats['percentage_used']:.1f}%

{'🚫 LÍMITE ALCANZADO' if stats['is_limit_reached'] else '✅ Dentro del límite'}
            """
            
            return report.strip()
            
        except Exception as e:
            print(f"Error generando reporte: {e}")
            return "Error generando reporte de uso"