"""
Módulo para monitorización y telemetría del sistema.
Permite rastrear eventos, métricas y excepciones para mejorar la observabilidad.
"""
import logging
import time
import os
import json
import traceback
from typing import Any, Dict, Optional, Union, List
import uuid
from functools import wraps
from datetime import datetime

# Configuración condicional de Application Insights para Azure
try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.ext.azure import metrics_exporter
    from opencensus.stats import aggregation, measure, stats, view
    from opencensus.trace.samplers import AlwaysOnSampler
    from opencensus.trace.tracer import Tracer
    HAS_OPENCENSUS = True
except ImportError:
    HAS_OPENCENSUS = False

# Configurar logging para este módulo
logger = logging.getLogger(__name__)

class Monitor:
    """Sistema centralizado de monitoreo para los agentes."""
    
    def __init__(self, app_name: str = "AgenteBusqueda"):
        """
        Inicializa el sistema de monitorización.
        
        Args:
            app_name: Nombre de la aplicación para identificarla en los datos
        """
        self.app_name = app_name
        self.use_appinsights = False
        self.instrumentation_key = os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY")
        self.tracer = None
        self.metrics_exporter = None
        self.request_stats = {}  # Almacén para estadísticas
        
        # Configurar Application Insights si está disponible
        if HAS_OPENCENSUS and self.instrumentation_key:
            try:
                # Configurar Azure Log Handler
                log_handler = AzureLogHandler(
                    connection_string=f'InstrumentationKey={self.instrumentation_key}'
                )
                log_handler.setLevel(logging.INFO)
                
                # Añadir handler al logger raíz
                root_logger = logging.getLogger()
                root_logger.addHandler(log_handler)
                
                # Configurar trazado
                self.tracer = Tracer(
                    exporter=AzureExporter(
                        connection_string=f'InstrumentationKey={self.instrumentation_key}'
                    ),
                    sampler=AlwaysOnSampler()
                )
                
                # Configurar métricas
                self.metrics_exporter = metrics_exporter.new_metrics_exporter(
                    connection_string=f'InstrumentationKey={self.instrumentation_key}'
                )
                
                self.use_appinsights = True
                logger.info("Monitorización con Application Insights activada")
            except Exception as e:
                logger.warning(f"Error al configurar Application Insights: {e}")
        else:
            logger.info("Application Insights no disponible o no configurado, se usarán logs locales")
        
        # Definir medidas comunes para las métricas
        if self.use_appinsights:
            # Definir medida para tiempo de respuesta
            self.response_time_measure = measure.MeasureFloat(
                "response_time",
                "Tiempo de respuesta en segundos",
                "s"
            )
            
            # Definir vista para la medida
            response_time_view = view.View(
                "response_time_distribution",
                "Distribución de tiempos de respuesta",
                [],
                self.response_time_measure,
                aggregation.DistributionAggregation(
                    [0.01, 0.05, 0.1, 0.3, 0.6, 1.0, 2.0, 5.0, 10.0]
                )
            )
            
            # Registrar vista con el exportador
            view_manager = stats.stats.view_manager
            view_manager.register_view(response_time_view)
        
        logger.info(f"Sistema de monitoreo {app_name} inicializado")
    
    def log_event(self, event_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra un evento personalizado.
        
        Args:
            event_name: Nombre del evento
            properties: Propiedades adicionales del evento
        """
        if properties is None:
            properties = {}
        
        # Añadir timestamp y nombre de la app
        properties.update({
            "timestamp": datetime.utcnow().isoformat(),
            "app_name": self.app_name
        })
        
        # Registrar en Application Insights
        if self.use_appinsights:
            properties_json = json.dumps(properties)
            logger.info(f"Custom Event: {event_name}", extra={
                "custom_dimensions": {
                    "event_name": event_name,
                    "properties": properties_json
                }
            })
        
        # También registrar localmente
        logger.info(f"Evento: {event_name} - {properties}")
    
    def track_metric(self, metric_name: str, value: float, properties: Optional[Dict[str, str]] = None) -> None:
        """
        Registra una métrica para monitorización.
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor numérico de la métrica
            properties: Propiedades/dimensiones adicionales
        """
        if properties is None:
            properties = {}
        
        # Añadir propiedades comunes
        properties["app_name"] = self.app_name
        
        # Enviar a Application Insights
        if self.use_appinsights:
            # Usar el exportador de métricas
            self.metrics_exporter.add_metric_value(
                metric_name,
                value,
                properties
            )
        
        # También registrar localmente
        logger.info(f"Métrica: {metric_name}={value} {properties}")
    
    def track_dependency(self, name: str, target: str, success: bool, start_time: float, 
                      end_time: float, data: Optional[str] = None) -> None:
        """
        Registra una dependencia externa (API, base de datos, etc.)
        
        Args:
            name: Nombre del tipo de dependencia
            target: Destino de la dependencia (ej. URL)
            success: Si la llamada fue exitosa
            start_time: Tiempo de inicio (timestamp)
            end_time: Tiempo de fin (timestamp)
            data: Datos adicionales sobre la dependencia
        """
        duration = end_time - start_time
        
        properties = {
            "name": name,
            "target": target,
            "success": "true" if success else "false",
            "duration_ms": str(int(duration * 1000)),
            "timestamp": datetime.utcnow().isoformat(),
            "app_name": self.app_name
        }
        
        if data:
            properties["data"] = data
        
        # Registrar en Application Insights
        if self.use_appinsights:
            logger.info(f"Dependency: {name}", extra={
                "custom_dimensions": properties
            })
        
        # También registrar localmente
        logger.info(f"Dependencia: {name} - {properties}")
        
        # Registrar métrica de tiempo de respuesta
        self.track_metric(f"dependency_{name}_duration", duration, 
                        {"target": target, "success": "true" if success else "false"})
    
    def track_request(self, name: str, url: str, success: bool, start_time: float,
                   end_time: float, response_code: str) -> None:
        """
        Registra una solicitud HTTP entrante.
        
        Args:
            name: Nombre de la solicitud
            url: URL de la solicitud
            success: Si la solicitud fue exitosa
            start_time: Tiempo de inicio (timestamp)
            end_time: Tiempo de fin (timestamp)
            response_code: Código de respuesta HTTP
        """
        duration = end_time - start_time
        
        properties = {
            "name": name,
            "url": url,
            "success": "true" if success else "false",
            "duration_ms": str(int(duration * 1000)),
            "response_code": response_code,
            "timestamp": datetime.utcnow().isoformat(),
            "app_name": self.app_name
        }
        
        # Registrar en Application Insights
        if self.use_appinsights:
            logger.info(f"Request: {name}", extra={
                "custom_dimensions": properties
            })
        
        # También registrar localmente
        logger.info(f"Solicitud: {name} - {properties}")
        
        # Actualizar estadísticas
        endpoint = url.split("?")[0]  # Eliminar parámetros para agrupar por endpoint base
        if endpoint not in self.request_stats:
            self.request_stats[endpoint] = {
                "count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0
            }
        
        stats = self.request_stats[endpoint]
        stats["count"] += 1
        if success:
            stats["success_count"] += 1
        else:
            stats["error_count"] += 1
        stats["total_duration"] += duration
        stats["min_duration"] = min(stats["min_duration"], duration)
        stats["max_duration"] = max(stats["max_duration"], duration)
    
    def track_exception(self, exception: Exception, properties: Optional[Dict[str, str]] = None) -> None:
        """
        Registra una excepción.
        
        Args:
            exception: La excepción a registrar
            properties: Propiedades adicionales del contexto
        """
        if properties is None:
            properties = {}
        
        # Añadir info de la excepción
        properties.update({
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "stack_trace": traceback.format_exc(),
            "timestamp": datetime.utcnow().isoformat(),
            "app_name": self.app_name
        })
        
        # Registrar en Application Insights
        if self.use_appinsights:
            logger.exception(f"Exception: {type(exception).__name__}", extra={
                "custom_dimensions": properties
            })
        
        # También registrar localmente
        logger.exception(f"Excepción: {type(exception).__name__} - {properties}")
    
    def get_request_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene estadísticas acumuladas de solicitudes.
        
        Returns:
            Diccionario con estadísticas por endpoint
        """
        # Calcular promedios para cada endpoint
        stats_with_avg = {}
        for endpoint, stats in self.request_stats.items():
            endpoint_stats = stats.copy()
            if stats["count"] > 0:
                endpoint_stats["avg_duration"] = stats["total_duration"] / stats["count"]
                endpoint_stats["success_rate"] = stats["success_count"] / stats["count"]
            stats_with_avg[endpoint] = endpoint_stats
        
        return stats_with_avg
    
    def begin_trace(self, span_name: str, attributes: Optional[Dict[str, str]] = None) -> Any:
        """
        Inicia un nuevo span de trazado.
        
        Args:
            span_name: Nombre del span
            attributes: Atributos del span
            
        Returns:
            Objeto span para uso con end_trace
        """
        if attributes is None:
            attributes = {}
        
        # Añadir atributos comunes
        attributes["app_name"] = self.app_name
        
        if self.use_appinsights and self.tracer:
            try:
                span = self.tracer.start_span(span_name)
                for key, value in attributes.items():
                    span.add_attribute(key, value)
                return span
            except Exception as e:
                logger.warning(f"Error al iniciar traza: {e}")
                return None
        
        # Si no hay app insights, devolver un objeto simple con tiempo de inicio
        return {
            "name": span_name,
            "start_time": time.time(),
            "attributes": attributes
        }
    
    def end_trace(self, span: Any) -> None:
        """
        Finaliza un span de trazado.
        
        Args:
            span: Objeto span devuelto por begin_trace
        """
        if span is None:
            return
        
        if self.use_appinsights and self.tracer and hasattr(span, "end"):
            try:
                span.end()
            except Exception as e:
                logger.warning(f"Error al finalizar traza: {e}")
        elif isinstance(span, dict) and "start_time" in span:
            # Simple span local
            duration = time.time() - span["start_time"]
            logger.info(
                f"Traza: {span['name']} - duración={duration:.3f}s - atributos={span['attributes']}"
            )


# Decorador para medir tiempo de ejecución
def measure_execution_time(monitor_attr='monitor'):
    """
    Decorador para medir tiempo de ejecución de un método y registrarlo como métrica.
    
    Args:
        monitor_attr: Nombre del atributo que contiene el monitor en la clase
        
    Returns:
        Función decorada que mide y reporta su tiempo de ejecución
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener instancia de monitor del primer argumento (self)
            monitor = getattr(args[0], monitor_attr, None) if args else None
            
            # Si no hay monitor, ejecutar sin medir
            if not monitor:
                return func(*args, **kwargs)
            
            # Generar ID único para esta ejecución
            execution_id = str(uuid.uuid4())
            
            # Obtener nombre de la función
            function_name = func.__name__
            
            # Registrar inicio
            start_time = time.time()
            monitor.log_event(
                f"{function_name}.start",
                {"execution_id": execution_id}
            )
            
            try:
                # Ejecutar función
                result = func(*args, **kwargs)
                
                # Registrar tiempo exitoso
                end_time = time.time()
                duration = end_time - start_time
                monitor.track_metric(
                    f"{function_name}.duration",
                    duration,
                    {"execution_id": execution_id, "status": "success"}
                )
                
                monitor.log_event(
                    f"{function_name}.complete",
                    {
                        "execution_id": execution_id,
                        "duration": duration,
                        "status": "success"
                    }
                )
                
                return result
                
            except Exception as e:
                # Registrar excepción y tiempo de error
                end_time = time.time()
                duration = end_time - start_time
                
                monitor.track_exception(
                    e, 
                    {
                        "execution_id": execution_id,
                        "function": function_name,
                        "duration": duration
                    }
                )
                
                monitor.log_event(
                    f"{function_name}.error",
                    {
                        "execution_id": execution_id,
                        "duration": duration,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                
                # Re-lanzar la excepción
                raise
        return wrapper
    return decorator


# Instancia global del monitor
monitor = Monitor()
