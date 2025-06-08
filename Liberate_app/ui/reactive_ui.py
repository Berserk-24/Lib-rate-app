#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Callable, Any, Optional
import threading
from datetime import datetime
import time


class ReactiveUI:
    """Sistema de UI reactiva para manejar eventos y actualizaciones en tiempo real"""
    
    def __init__(self):
        self.observers: Dict[str, List[Callable]] = {}
        self.state: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.event_history: List[Dict] = []
        self.max_history = 100
        self._running = True
        self._update_queue = []
        self._ui_elements = {}
        self._bindings = {}
    
    def subscribe(self, event_name: str, callback: Callable):
        """
        Suscribirse a un evento específico
        
        Args:
            event_name: Nombre del evento
            callback: Función callback a ejecutar cuando ocurra el evento
        """
        with self.lock:
            if event_name not in self.observers:
                self.observers[event_name] = []
            
            if callback not in self.observers[event_name]:
                self.observers[event_name].append(callback)
                print(f"✅ Suscrito a evento '{event_name}'")
    
    def unsubscribe(self, event_name: str, callback: Callable):
        """
        Desuscribirse de un evento
        
        Args:
            event_name: Nombre del evento
            callback: Función callback a remover
        """
        with self.lock:
            if event_name in self.observers and callback in self.observers[event_name]:
                self.observers[event_name].remove(callback)
                print(f"✅ Desuscrito del evento '{event_name}'")
    
    def emit(self, event_name: str, data: Any = None):
        """
        Emitir un evento a todos los observadores suscritos
        
        Args:
            event_name: Nombre del evento
            data: Datos a pasar a los callbacks
        """
        with self.lock:
            # Registrar evento en historial
            self._add_to_history(event_name, data)
            
            if event_name in self.observers:
                observers_copy = self.observers[event_name].copy()
            else:
                observers_copy = []
        
        # Ejecutar callbacks fuera del lock para evitar deadlocks
        for callback in observers_copy:
            try:
                callback(data)
            except Exception as e:
                print(f"Error al ejecutar callback para '{event_name}': {e}")
    
    def _add_to_history(self, event_name: str, data: Any):
        """
        Agregar evento al historial
        
        Args:
            event_name: Nombre del evento
            data: Datos del evento
        """
        event_record = {
            'timestamp': datetime.now(),
            'event': event_name,
            'data': data
        }
        
        self.event_history.append(event_record)
        
        # Mantener solo los últimos max_history eventos
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
    
    def set_state(self, key: str, value: Any, emit_change: bool = True):
        """
        Establecer un valor en el estado y emitir evento de cambio
        
        Args:
            key: Clave del estado
            value: Valor a establecer
            emit_change: Si debe emitir evento de cambio
        """
        with self.lock:
            old_value = self.state.get(key)
            self.state[key] = value
        
        if emit_change and old_value != value:
            self.emit(f"state_changed_{key}", {
                'key': key,
                'old_value': old_value,
                'new_value': value
            })
            self.emit("state_changed", {
                'key': key,
                'old_value': old_value,
                'new_value': value
            })
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Obtener un valor del estado
        
        Args:
            key: Clave del estado
            default: Valor por defecto si no existe
            
        Returns:
            Valor del estado o valor por defecto
        """
        with self.lock:
            return self.state.get(key, default)
    
    def update_state(self, updates: Dict[str, Any], emit_change: bool = True):
        """
        Actualizar múltiples valores del estado
        
        Args:
            updates: Diccionario con las actualizaciones
            emit_change: Si debe emitir eventos de cambio
        """
        changes = {}
        
        with self.lock:
            for key, value in updates.items():
                old_value = self.state.get(key)
                self.state[key] = value
                if old_value != value:
                    changes[key] = {'old': old_value, 'new': value}
        
        if emit_change and changes:
            for key, change in changes.items():
                self.emit(f"state_changed_{key}", {
                    'key': key,
                    'old_value': change['old'],
                    'new_value': change['new']
                })
            
            self.emit("batch_state_changed", changes)
    
    def bind_element(self, element_id: str, state_key: str, update_callback: Callable):
        """
        Vincular un elemento de UI a una clave del estado
        
        Args:
            element_id: ID del elemento de UI
            state_key: Clave del estado a vincular
            update_callback: Función para actualizar el elemento
        """
        self._ui_elements[element_id] = {
            'state_key': state_key,
            'callback': update_callback
        }
        
        # Suscribirse a cambios de estado
        self.subscribe(f"state_changed_{state_key}", 
                      lambda data: self._update_bound_element(element_id, data))
        
        # Actualizar inmediatamente con el valor actual
        current_value = self.get_state(state_key)
        if current_value is not None:
            try:
                update_callback(current_value)
            except Exception as e:
                print(f"Error actualizando elemento {element_id}: {e}")
    
    def _update_bound_element(self, element_id: str, data: Dict):
        """
        Actualizar un elemento vinculado cuando cambia el estado
        
        Args:
            element_id: ID del elemento
            data: Datos del cambio de estado
        """
        if element_id in self._ui_elements:
            try:
                callback = self._ui_elements[element_id]['callback']
                callback(data['new_value'])
            except Exception as e:
                print(f"Error actualizando elemento vinculado {element_id}: {e}")
    
    def unbind_element(self, element_id: str):
        """
        Desvincular un elemento de UI del estado
        
        Args:
            element_id: ID del elemento a desvincular
        """
        if element_id in self._ui_elements:
            state_key = self._ui_elements[element_id]['state_key']

            del self._ui_elements[element_id]
    
    def get_event_history(self, event_name: Optional[str] = None, 
                         limit: Optional[int] = None) -> List[Dict]:
        """
        Obtener el historial de eventos
        
        Args:
            event_name: Filtrar por nombre de evento (opcional)
            limit: Limitar número de eventos (opcional)
            
        Returns:
            Lista de eventos del historial
        """
        with self.lock:
            history = self.event_history.copy()
        
        if event_name:
            history = [e for e in history if e['event'] == event_name]
        
        # Ordenar por timestamp más reciente primero
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        if limit:
            history = history[:limit]
        
        return history
    
    def clear_history(self):
        """Limpiar el historial de eventos"""
        with self.lock:
            self.event_history.clear()
        
        self.emit("history_cleared", None)
    
    def get_observers_count(self, event_name: Optional[str] = None) -> Dict[str, int]:
        """
        Obtener el número de observadores por evento
        
        Args:
            event_name: Evento específico (opcional)
            
        Returns:
            Diccionario con el conteo de observadores
        """
        with self.lock:
            if event_name:
                return {event_name: len(self.observers.get(event_name, []))}
            else:
                return {event: len(callbacks) for event, callbacks in self.observers.items()}
    
    def emit_async(self, event_name: str, data: Any = None, delay: float = 0):
        """
        Emitir un evento de forma asíncrona
        
        Args:
            event_name: Nombre del evento
            data: Datos del evento
            delay: Retraso en segundos antes de emitir
        """
        def delayed_emit():
            if delay > 0:
                time.sleep(delay)
            self.emit(event_name, data)
        
        thread = threading.Thread(target=delayed_emit, daemon=True)
        thread.start()
    
    def create_debounced_emitter(self, event_name: str, delay: float = 0.5) -> Callable:
        """
        Crear un emisor con debounce para evitar múltiples emisiones rápidas
        
        Args:
            event_name: Nombre del evento
            delay: Tiempo de espera en segundos
            
        Returns:
            Función emisora con debounce
        """
        last_call_time = {'time': 0}
        timer = {'timer': None}
        
        def debounced_emit(data: Any = None):
            current_time = time.time()
            last_call_time['time'] = current_time
            
            # Cancelar timer anterior si existe
            if timer['timer']:
                timer['timer'].cancel()
            
            # Crear nuevo timer
            def emit_if_latest():
                if time.time() - last_call_time['time'] >= delay - 0.01:
                    self.emit(event_name, data)
            
            timer['timer'] = threading.Timer(delay, emit_if_latest)
            timer['timer'].start()
        
        return debounced_emit
    
    def dispose(self):
        """Limpiar recursos y detener el sistema reactivo"""
        self._running = False
        
        with self.lock:
            self.observers.clear()
            self.state.clear()
            self.event_history.clear()
            self._ui_elements.clear()
        
        self.emit("system_disposed", None)
        
        print("🧹 Sistema ReactiveUI limpiado")
    
    def debug_info(self) -> Dict[str, Any]:
        """
        Obtener información de debug del sistema
        
        Returns:
            Diccionario con información de debug
        """
        with self.lock:
            return {
                'observers': {event: len(callbacks) for event, callbacks in self.observers.items()},
                'state_keys': list(self.state.keys()),
                'event_history_count': len(self.event_history),
                'bound_elements': list(self._ui_elements.keys()),
                'is_running': self._running
            }