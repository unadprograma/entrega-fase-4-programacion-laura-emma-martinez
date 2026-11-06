
from abc import ABC, abstractmethod
import datetime
import logging
import re

# ==========================================
# CONFIGURACIÓN DEL SISTEMA DE LOGS
# ==========================================
logging.basicConfig(
    filename='sistema.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)


# ==========================================
# EXCEPCIONES PERSONALIZADAS
# ==========================================
class ErrorSistemaFJ(Exception):
    """Clase base para excepciones del sistema."""


class ErrorCliente(ErrorSistemaFJ):
    """Errores relacionados con los clientes."""


class ErrorServicio(ErrorSistemaFJ):
    """Errores en la creación, validación o disponibilidad de servicios."""


class ErrorReserva(ErrorSistemaFJ):
    """Errores al procesar, confirmar o cancelar reservas."""


def _fallar(clase_error, mensaje):
    """Registra el error en el log y lanza la excepción indicada."""
    logging.error(mensaje)
    raise clase_error(mensaje)


def _es_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


# ==========================================
# CLASE ABSTRACTA BASE
# ==========================================
class EntidadBase(ABC):
    def __init__(self, identificador: str):
        if not isinstance(identificador, str) or not identificador.strip():
            _fallar(ErrorSistemaFJ, "El identificador debe ser un texto no vacío.")
        self._identificador = identificador.strip()

    @property
    def identificador(self):
        return self._identificador

    @abstractmethod
    def obtener_detalles(self) -> str:
        pass


# ==========================================
# CLASE CLIENTE
# ==========================================
class Cliente(EntidadBase):
    def __init__(self, identificador: str, nombre: str, correo: str, telefono: str):
        super().__init__(identificador)
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or not valor.strip():
            _fallar(ErrorCliente, f"Nombre inválido: {valor!r}. Debe ser un texto no vacío.")
        self._nombre = valor.strip()

    @property
    def correo(self):
        return self._correo

    @correo.setter
    def correo(self, valor):
        patron = r"[^@\s]+@[^@\s]+\.[^@\s]+"
        if not isinstance(valor, str) or not re.fullmatch(patron, valor.strip()):
            _fallar(ErrorCliente, f"Correo electrónico inválido: {valor!r}.")
        self._correo = valor.strip()

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if not isinstance(valor, str) or not valor.isdigit() or not (7 <= len(valor) <= 15):
            _fallar(ErrorCliente,
                    f"Teléfono inválido: {valor!r}. Debe contener solo números (7 a 15 dígitos).")
        self._telefono = valor

    def obtener_detalles(self) -> str:
        return (f"Cliente [ID: {self.identificador}] - Nombre: {self.nombre}, "
                f"Correo: {self.correo}")


# ==========================================
# CLASE ABSTRACTA SERVICIO
# ==========================================
class Servicio(EntidadBase, ABC):
    def __init__(self, identificador: str, nombre_servicio: str, precio_base: float,
                 disponible: bool = True):
        super().__init__(identificador)
        self.nombre_servicio = nombre_servicio
        self.precio_base = precio_base
        self.disponible = disponible

    @property
    def nombre_servicio(self):
        return self._nombre_servicio

    @nombre_servicio.setter
    def nombre_servicio(self, valor):
        if not isinstance(valor, str) or not valor.strip():
            _fallar(ErrorServicio, f"Nombre de servicio inválido: {valor!r}.")
        self._nombre_servicio = valor.strip()

    @property
    def precio_base(self):
        return self._precio_base

    @precio_base.setter
    def precio_base(self, valor):
        if not _es_numero(valor):
            _fallar(ErrorServicio, f"El precio base debe ser numérico: {valor!r}.")
        if valor < 0:
            _fallar(ErrorServicio, "El precio base no puede ser negativo.")
        self._precio_base = valor

    @property
    def disponible(self):
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        if not isinstance(valor, bool):
            _fallar(ErrorServicio, "La disponibilidad debe ser True o False.")
        self._disponible = valor

    @abstractmethod
    def validar_parametros(self, *args, **kwargs) -> None:
        """Valida los parámetros de cálculo; lanza ErrorServicio si son inválidos."""

    @abstractmethod
    def calcular_costo(self, *args, **kwargs) -> float:
        """Calcula el costo del servicio (sobrescrito en cada servicio)."""

    def calcular_costo_con_impuesto(self, *args, iva_porcentaje: float = 19.0, **kwargs) -> float:
        """Variante sobrecargada: costo base + IVA (por defecto 19 %)."""
        if not _es_numero(iva_porcentaje) or not (0 <= iva_porcentaje <= 100):
            _fallar(ErrorServicio, f"Porcentaje de IVA inválido: {iva_porcentaje!r}.")
        costo = self.calcular_costo(*args, **kwargs)
        return costo * (1 + iva_porcentaje / 100)


# ==========================================
# SERVICIOS ESPECIALIZADOS (HERENCIA Y POLIMORFISMO)
# ==========================================
class ReservaSalas(Servicio):
    def __init__(self, identificador: str, nombre_servicio: str, precio_base: float,
                 capacidad: int, disponible: bool = True):
        super().__init__(identificador, nombre_servicio, precio_base, disponible)
        self.capacidad = capacidad

    @property
    def capacidad(self):
        return self._capacidad

    @capacidad.setter
    def capacidad(self, valor):
        if not _es_entero(valor) or valor <= 0:
            _fallar(ErrorServicio, "La capacidad de la sala debe ser un entero mayor a cero.")
        self._capacidad = valor

    def validar_parametros(self, horas, descuento_porcentaje=0.0):
        if not _es_entero(horas) or horas <= 0:
            _fallar(ErrorServicio, "Las horas de reserva de sala deben ser un entero mayor a cero.")
        if not _es_numero(descuento_porcentaje) or not (0 <= descuento_porcentaje <= 100):
            _fallar(ErrorServicio, "El porcentaje de descuento no es válido (0 a 100).")

    def calcular_costo(self, horas: int, descuento_porcentaje: float = 0.0) -> float:
        self.validar_parametros(horas, descuento_porcentaje)
        subtotal = self.precio_base * horas
        return subtotal - subtotal * (descuento_porcentaje / 100)

    def obtener_detalles(self) -> str:
        return (f"Sala [ID: {self.identificador}] - {self.nombre_servicio} "
                f"(Capacidad: {self.capacidad} personas)")


class AlquilerEquipos(Servicio):
    SEGURO_DIARIO = 50000  # costo fijo del seguro por día

    def __init__(self, identificador: str, nombre_servicio: str, precio_base: float,
                 tipo_equipo: str, disponible: bool = True):
        super().__init__(identificador, nombre_servicio, precio_base, disponible)
        if not isinstance(tipo_equipo, str) or not tipo_equipo.strip():
            _fallar(ErrorServicio, "El tipo de equipo no puede estar vacío.")
        self.tipo_equipo = tipo_equipo.strip()

    def validar_parametros(self, dias, seguro_adicional=False):
        if not _es_entero(dias) or dias <= 0:
            _fallar(ErrorServicio, "Los días de alquiler deben ser un entero mayor a cero.")
        if not isinstance(seguro_adicional, bool):
            _fallar(ErrorServicio, "El parámetro 'seguro' debe ser True o False.")

    def calcular_costo(self, dias: int, seguro_adicional: bool = False) -> float:
        self.validar_parametros(dias, seguro_adicional)
        costo = self.precio_base * dias
        if seguro_adicional:
            costo += self.SEGURO_DIARIO * dias
        return costo

    def obtener_detalles(self) -> str:
        return (f"Equipo [ID: {self.identificador}] - {self.nombre_servicio} "
                f"(Tipo: {self.tipo_equipo})")


class AsesoriasEspecializadas(Servicio):
    MULTIPLICADOR_COMPLEJIDAD = 1.5

    def __init__(self, identificador: str, nombre_servicio: str, precio_base: float,
                 area: str, disponible: bool = True):
        super().__init__(identificador, nombre_servicio, precio_base, disponible)
        if not isinstance(area, str) or not area.strip():
            _fallar(ErrorServicio, "El área de la asesoría no puede estar vacía.")
        self.area = area.strip()

    def validar_parametros(self, sesiones, complejidad_alta=False):
        if not _es_entero(sesiones) or sesiones <= 0:
            _fallar(ErrorServicio, "Las sesiones de asesoría deben ser un entero mayor a cero.")
        if not isinstance(complejidad_alta, bool):
            _fallar(ErrorServicio, "El parámetro 'complejidad' debe ser True o False.")

    def calcular_costo(self, sesiones: int, complejidad_alta: bool = False) -> float:
        self.validar_parametros(sesiones, complejidad_alta)
        multiplicador = self.MULTIPLICADOR_COMPLEJIDAD if complejidad_alta else 1.0
        return self.precio_base * sesiones * multiplicador

    def obtener_detalles(self) -> str:
        return (f"Asesoría [ID: {self.identificador}] - {self.nombre_servicio} "
                f"(Área: {self.area})")


# ==========================================
# CLASE RESERVA
# ==========================================
class Reserva:
    """Estados: Pendiente -> Procesada -> Confirmada | Fallida | Cancelada."""

    def __init__(self, id_reserva: str, cliente: Cliente, servicio: Servicio,
                 cantidad_tiempo: int, **opciones):
        # opciones admitidas: descuento, seguro, complejidad, iva
        if not isinstance(cliente, Cliente):
            _fallar(ErrorReserva, "La reserva debe tener un cliente válido.")
        if not isinstance(servicio, Servicio):
            _fallar(ErrorReserva, "La reserva debe tener un servicio válido.")
        self.id_reserva = id_reserva
        self.cliente = cliente
        self.servicio = servicio
        self.cantidad_tiempo = cantidad_tiempo
        self.opciones = opciones
        self.fecha_creacion = datetime.datetime.now()
        self.estado = "Pendiente"
        self.costo_total = 0.0

    def _parametros_costo(self) -> dict:
        """Polimorfismo: cada tipo de servicio recibe sus propios parámetros opcionales."""
        if isinstance(self.servicio, ReservaSalas):
            return {"descuento_porcentaje": self.opciones.get("descuento", 0.0)}
        if isinstance(self.servicio, AlquilerEquipos):
            return {"seguro_adicional": self.opciones.get("seguro", False)}
        if isinstance(self.servicio, AsesoriasEspecializadas):
            return {"complejidad_alta": self.opciones.get("complejidad", False)}
        _fallar(ErrorReserva, "Tipo de servicio desconocido.")

    def procesar_reserva(self):
        """Calcula el costo con manejo try/except/else/finally y encadenamiento."""
        try:
            logging.info(f"Iniciando procesamiento de reserva {self.id_reserva}")
            if self.estado in ("Cancelada", "Confirmada"):
                _fallar(ErrorReserva,
                        f"La reserva {self.id_reserva} ya está {self.estado.lower()}.")
            if not self.servicio.disponible:
                _fallar(ErrorServicio,
                        f"El servicio '{self.servicio.nombre_servicio}' no está disponible.")

            parametros = self._parametros_costo()
            iva = self.opciones.get("iva")
            if iva is not None:
                self.costo_total = self.servicio.calcular_costo_con_impuesto(
                    self.cantidad_tiempo, iva_porcentaje=iva, **parametros)
            else:
                self.costo_total = self.servicio.calcular_costo(self.cantidad_tiempo, **parametros)
            self.estado = "Procesada"

        except ErrorReserva:
            raise  # ya fue registrado; el estado no cambia
        except (ErrorServicio, ErrorCliente) as err:
            self.estado = "Fallida"
            logging.error(f"Error de dominio en reserva {self.id_reserva}: {err}")
            raise ErrorReserva(
                f"Fallo al procesar reserva {self.id_reserva}: {err}") from err
        except Exception as ex:
            self.estado = "Error Grave"
            logging.error(f"Excepción no esperada en reserva {self.id_reserva}: {ex!r}")
            raise ErrorReserva(
                f"Error inesperado en reserva {self.id_reserva}: {ex!r}") from ex
        else:
            logging.info(f"Reserva {self.id_reserva} procesada. Costo: {self.costo_total:,.2f}")
            print(f"-> [ÉXITO] Reserva {self.id_reserva} procesada. "
                  f"Costo total: ${self.costo_total:,.2f}")
        finally:
            print(f"-> [ESTADO] Fin de procesamiento de {self.id_reserva}. "
                  f"Estado actual: {self.estado}")

    def confirmar_reserva(self):
        if self.estado != "Procesada":
            _fallar(ErrorReserva,
                    f"No se puede confirmar {self.id_reserva}: estado actual '{self.estado}'.")
        self.estado = "Confirmada"
        logging.info(f"Reserva {self.id_reserva} confirmada.")
        print(f"-> [CONFIRMADA] La reserva {self.id_reserva} fue confirmada.")

    def cancelar_reserva(self):
        if self.estado == "Cancelada":
            _fallar(ErrorReserva, f"La reserva {self.id_reserva} ya se encuentra cancelada.")
        self.estado = "Cancelada"
        logging.info(f"Reserva {self.id_reserva} cancelada exitosamente.")
        print(f"-> [CANCELADA] La reserva {self.id_reserva} ha sido anulada.")

    def obtener_detalles(self) -> str:
        return (f"Reserva [{self.id_reserva}] {self.cliente.nombre} -> "
                f"{self.servicio.nombre_servicio} | {self.estado} | ${self.costo_total:,.2f}")


# ==========================================
# GESTOR DEL SISTEMA (LISTAS INTERNAS)
# ==========================================
class GestorSistema:
    def __init__(self):
        self._clientes = []
        self._servicios = []
        self._reservas = []

    @staticmethod
    def _buscar(lista, id_buscado, clase_error, nombre):
        for item in lista:
            identificador = getattr(item, "identificador", getattr(item, "id_reserva", None))
            if identificador == id_buscado:
                return item
        _fallar(clase_error, f"{nombre} '{id_buscado}' no existe.")

    def registrar_cliente(self, cliente: Cliente):
        if any(c.identificador == cliente.identificador for c in self._clientes):
            _fallar(ErrorCliente, f"Ya existe un cliente con ID '{cliente.identificador}'.")
        self._clientes.append(cliente)
        logging.info(f"Cliente registrado: {cliente.identificador}")

    def registrar_servicio(self, servicio: Servicio):
        if any(s.identificador == servicio.identificador for s in self._servicios):
            _fallar(ErrorServicio, f"Ya existe un servicio con ID '{servicio.identificador}'.")
        self._servicios.append(servicio)
        logging.info(f"Servicio registrado: {servicio.identificador}")

    def buscar_cliente(self, id_cliente):
        return self._buscar(self._clientes, id_cliente, ErrorCliente, "Cliente")

    def buscar_servicio(self, id_servicio):
        return self._buscar(self._servicios, id_servicio, ErrorServicio, "Servicio")

    def buscar_reserva(self, id_reserva):
        return self._buscar(self._reservas, id_reserva, ErrorReserva, "Reserva")

    def crear_reserva(self, id_reserva, id_cliente, id_servicio, cantidad_tiempo, **opciones):
        cliente = self.buscar_cliente(id_cliente)
        servicio = self.buscar_servicio(id_servicio)
        reserva = Reserva(id_reserva, cliente, servicio, cantidad_tiempo, **opciones)
        self._reservas.append(reserva)  # se guarda aunque luego falle, para auditoría
        logging.info(f"Reserva creada: {id_reserva}")
        return reserva

    def resumen(self):
        print("\n================ RESUMEN FINAL ================")
        print(f"Clientes registrados : {len(self._clientes)}")
        print(f"Servicios registrados: {len(self._servicios)}")
        print(f"Reservas creadas     : {len(self._reservas)}")
        for r in self._reservas:
            print("  -", r.obtener_detalles())


# ==========================================
# SIMULACIÓN DE OPERACIONES
# ==========================================
def ejecutar(numero, descripcion, operacion):
    """Ejecuta una operación; el programa continúa aunque ocurra un error."""
    print(f"\nOperación {numero}: {descripcion}")
    try:
        operacion()
    except ErrorSistemaFJ as e:
        print(f"-> [ERROR CONTROLADO] {type(e).__name__}: {e}")
        if e.__cause__:
            print(f"   causa original: {type(e.__cause__).__name__}: {e.__cause__}")
    except Exception as e:  # cualquier error imprevisto tampoco detiene el sistema
        logging.error(f"Error inesperado en operación {numero}: {e!r}")
        print(f"-> [ERROR INESPERADO CONTROLADO] {e!r}")


def procesar_y_confirmar(reserva):
    reserva.procesar_reserva()
    reserva.confirmar_reserva()


if __name__ == "__main__":
    print("==================================================")
    print("   SIMULACIÓN - SOFTWARE FJ (16 OPERACIONES)      ")
    print("==================================================")
    logging.info("=== Inicio de la simulación ===")
    g = GestorSistema()

    ejecutar(1, "Registro válido de clientes",
             lambda: [g.registrar_cliente(c) for c in (
                 Cliente("C001", "Carlos Pérez", "carlos@mail.com", "3104567890"),
                 Cliente("C002", "María Rodríguez", "maria@mail.com", "3157894561"),
                 Cliente("C003", "Luis Torres", "luis@mail.com", "3009876543"))])

    ejecutar(2, "Registro válido de servicios (sala, equipo, asesoría, sala no disponible)",
             lambda: [g.registrar_servicio(s) for s in (
                 ReservaSalas("S001", "Sala Ejecutiva", 40000, 15),
                 AlquilerEquipos("E001", "Laptop Core i7", 80000, "Cómputo"),
                 AsesoriasEspecializadas("A001", "Arquitectura de Software", 120000, "Ingeniería"),
                 ReservaSalas("S002", "Sala en Mantenimiento", 30000, 8, disponible=False))])

    ejecutar(3, "Cliente con correo inválido",
             lambda: Cliente("C004", "Ana Gómez", "correo-sin-arroba", "3201234567"))

    ejecutar(4, "Cliente con teléfono inválido",
             lambda: Cliente("C005", "Sofía Ruiz", "sofia@mail.com", "310abc7890"))

    ejecutar(5, "Cliente con nombre que no es texto",
             lambda: Cliente("C006", 12345, "x@mail.com", "3001234567"))

    ejecutar(6, "Servicio con precio negativo",
             lambda: ReservaSalas("S999", "Sala Rota", -5000, 5))

    ejecutar(7, "Servicio con capacidad cero",
             lambda: ReservaSalas("S998", "Sala Fantasma", 20000, 0))

    ejecutar(8, "Reserva de sala 4 h con 10 % de descuento (procesar + confirmar)",
             lambda: procesar_y_confirmar(
                 g.crear_reserva("R001", "C001", "S001", 4, descuento=10.0)))

    ejecutar(9, "Alquiler de equipo 5 días con seguro e IVA 19 %",
             lambda: procesar_y_confirmar(
                 g.crear_reserva("R002", "C002", "E001", 5, seguro=True, iva=19.0)))

    ejecutar(10, "Asesoría de alta complejidad, 3 sesiones",
             lambda: procesar_y_confirmar(
                 g.crear_reserva("R003", "C003", "A001", 3, complejidad=True)))

    ejecutar(11, "Reserva con tiempo negativo (reserva fallida)",
             lambda: g.crear_reserva("R004", "C001", "S001", -2).procesar_reserva())

    ejecutar(12, "Reserva con parámetro faltante (duración None)",
             lambda: g.crear_reserva("R005", "C001", "S001", None).procesar_reserva())

    ejecutar(13, "Reserva con cliente inexistente",
             lambda: g.crear_reserva("R006", "C999", "S001", 2))

    ejecutar(14, "Reserva de servicio no disponible",
             lambda: g.crear_reserva("R007", "C002", "S002", 2).procesar_reserva())

    ejecutar(15, "Cancelación exitosa de una reserva existente",
             lambda: g.buscar_reserva("R002").cancelar_reserva())

    ejecutar(16, "Doble cancelación de la misma reserva (error controlado)",
             lambda: g.buscar_reserva("R002").cancelar_reserva())

    g.resumen()
    logging.info("=== Fin de la simulación ===")
    print("\n==================================================")
    print(" SIMULACIÓN FINALIZADA. REVISAR ARCHIVO 'sistema.log'")
    print("==================================================")