from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from capacitacion.models import Leccion, ProgresoLeccion
from cuentas.models import Usuario
from diagnostico.models import Diagnostico
from tickets.models import SeguimientoTicket, Ticket
from core.models import Contrato, Empresa, Paquete, Pago


CONTRASENA_ADMIN = "Admin12345!"
CONTRASENA_CLIENTES = "Cliente12345!"


class Command(BaseCommand):
    help = "Crea o actualiza los datos de demostración de la plataforma."

    def handle(self, *args, **options):
        with transaction.atomic():
            usuarios = self._cargar_usuarios()
            paquetes = self._cargar_paquetes()
            empresas = self._cargar_empresas(usuarios)
            contratos = self._cargar_contratos(empresas, paquetes)
            self._cargar_pagos(contratos)
            self._cargar_diagnostico(empresas["colmado"], paquetes["intermedio"])
            lecciones = self._cargar_lecciones()
            self._cargar_progresos(usuarios["cliente"], lecciones)
            self._cargar_tickets(usuarios, empresas)

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados."))
        self.stdout.write("Usuarios y contraseñas:")
        self.stdout.write(
            f"admin@cybersolutions.do : {CONTRASENA_ADMIN}"
        )
        for numero in range(1, 5):
            email = (
                "cliente@demo.do"
                if numero == 1
                else f"cliente{numero}@demo.do"
            )
            self.stdout.write(f"{email} : {CONTRASENA_CLIENTES}")

    def _cargar_usuarios(self):
        especificaciones = {
            "admin": (
                "admin@cybersolutions.do",
                CONTRASENA_ADMIN,
                Usuario.Rol.ADMINISTRADOR,
                True,
            ),
            "cliente": (
                "cliente@demo.do",
                CONTRASENA_CLIENTES,
                Usuario.Rol.CLIENTE,
                False,
            ),
            "cliente2": (
                "cliente2@demo.do",
                CONTRASENA_CLIENTES,
                Usuario.Rol.CLIENTE,
                False,
            ),
            "cliente3": (
                "cliente3@demo.do",
                CONTRASENA_CLIENTES,
                Usuario.Rol.CLIENTE,
                False,
            ),
            "cliente4": (
                "cliente4@demo.do",
                CONTRASENA_CLIENTES,
                Usuario.Rol.CLIENTE,
                False,
            ),
        }
        usuarios = {}
        for clave, (email, password, rol, es_superusuario) in especificaciones.items():
            usuario, creado = Usuario.objects.get_or_create(
                email=email,
                defaults={
                    "rol": rol,
                    "estado": Usuario.Estado.ACTIVO,
                    "is_active": True,
                    "is_staff": es_superusuario,
                    "is_superuser": es_superusuario,
                },
            )
            usuario.rol = rol
            usuario.estado = Usuario.Estado.ACTIVO
            usuario.is_active = True
            usuario.is_staff = es_superusuario
            usuario.is_superuser = es_superusuario
            if creado or not usuario.check_password(password):
                usuario.set_password(password)
            usuario.save()
            usuarios[clave] = usuario
        return usuarios

    def _cargar_paquetes(self):
        especificaciones = {
            "basico": {
                "nombre": Paquete.Nombre.BASICO,
                "descripcion": "Protección esencial para tu negocio.",
                "servicios_incluidos": (
                    "Diagnóstico de riesgos\nProtección de equipos"
                ),
                "precio_mensual": Decimal("2500.00"),
            },
            "intermedio": {
                "nombre": Paquete.Nombre.INTERMEDIO,
                "descripcion": "Protección y respaldo para tu negocio.",
                "servicios_incluidos": (
                    "Todo lo del Básico\nRespaldo de información\n"
                    "Protección del correo"
                ),
                "precio_mensual": Decimal("4500.00"),
            },
            "completo": {
                "nombre": Paquete.Nombre.COMPLETO,
                "descripcion": "Protección integral para tu negocio.",
                "servicios_incluidos": (
                    "Todo lo del Intermedio\nCapacitación del personal\n"
                    "Soporte continuo"
                ),
                "precio_mensual": Decimal("7000.00"),
            },
        }
        paquetes = {}
        for clave, datos in especificaciones.items():
            paquete, _ = Paquete.objects.update_or_create(
                nombre=datos["nombre"],
                defaults={
                    **datos,
                    "estado": Paquete.Estado.ACTIVO,
                },
            )
            paquetes[clave] = paquete
        return paquetes

    def _cargar_empresas(self, usuarios):
        especificaciones = {
            "colmado": {
                "usuario": usuarios["cliente"],
                "nombre_comercial": "Colmado La Esperanza",
                "sector": Empresa.Sector.COMERCIO,
                "tamano": Empresa.Tamano.MICRO,
                "cantidad_empleados": 5,
                "cantidad_equipos": 3,
                "telefono": "8095550101",
                "direccion": "Distrito Nacional",
            },
            "clinica": {
                "usuario": usuarios["cliente2"],
                "nombre_comercial": "Clínica Dental Sonrisa",
                "sector": Empresa.Sector.SALUD,
                "tamano": Empresa.Tamano.PEQUENA,
                "cantidad_empleados": 24,
                "cantidad_equipos": 15,
                "telefono": "8095550102",
                "direccion": "Distrito Nacional",
            },
            "ferreteria": {
                "usuario": usuarios["cliente3"],
                "nombre_comercial": "Ferretería El Maestro",
                "sector": Empresa.Sector.COMERCIO,
                "tamano": Empresa.Tamano.MICRO,
                "cantidad_empleados": 8,
                "cantidad_equipos": 6,
                "telefono": "8095550103",
                "direccion": "Distrito Nacional",
            },
            "salon": {
                "usuario": usuarios["cliente4"],
                "nombre_comercial": "Salón Bella Imagen",
                "sector": Empresa.Sector.SERVICIOS_PROFESIONALES,
                "tamano": Empresa.Tamano.MICRO,
                "cantidad_empleados": 6,
                "cantidad_equipos": 4,
                "telefono": "8095550104",
                "direccion": "Distrito Nacional",
            },
        }
        empresas = {}
        for clave, datos in especificaciones.items():
            usuario = datos["usuario"]
            defaults = {
                nombre: valor
                for nombre, valor in datos.items()
                if nombre != "usuario"
            }
            empresa, _ = Empresa.objects.update_or_create(
                usuario=usuario,
                defaults=defaults,
            )
            empresas[clave] = empresa
        return empresas

    def _cargar_contratos(self, empresas, paquetes):
        especificaciones = (
            {
                "clave": "colmado",
                "empresa": empresas["colmado"],
                "paquete": paquetes["intermedio"],
                "tipo": Contrato.TipoContrato.MENSUAL,
                "estado": Contrato.Estado.ACTIVO,
                "inicio": date(2026, 11, 15),
                "fin": date(2026, 12, 15),
            },
            {
                "clave": "clinica",
                "empresa": empresas["clinica"],
                "paquete": paquetes["completo"],
                "tipo": Contrato.TipoContrato.ANUAL,
                "estado": Contrato.Estado.ACTIVO,
                "inicio": date(2026, 7, 1),
                "fin": date(2027, 6, 30),
            },
            {
                "clave": "ferreteria",
                "empresa": empresas["ferreteria"],
                "paquete": paquetes["basico"],
                "tipo": Contrato.TipoContrato.MENSUAL,
                "estado": Contrato.Estado.SOLICITADO,
                "inicio": None,
                "fin": None,
            },
            {
                "clave": "salon",
                "empresa": empresas["salon"],
                "paquete": paquetes["intermedio"],
                "tipo": Contrato.TipoContrato.TRIMESTRAL,
                "estado": Contrato.Estado.VENCIDO,
                "inicio": date(2026, 8, 3),
                "fin": date(2026, 11, 1),
            },
        )
        contratos = {}
        for datos in especificaciones:
            contrato, _ = Contrato.objects.update_or_create(
                empresa=datos["empresa"],
                paquete=datos["paquete"],
                tipo_contrato=datos["tipo"],
                defaults={
                    "precio_acordado": datos["paquete"].precio_mensual,
                    "fecha_inicio": datos["inicio"],
                    "fecha_fin": datos["fin"],
                    "estado": datos["estado"],
                },
            )
            contratos[datos["clave"]] = contrato
        return contratos

    def _cargar_pagos(self, contratos):
        for clave in ("colmado", "clinica"):
            contrato = contratos[clave]
            Pago.objects.update_or_create(
                contrato=contrato,
                referencia=f"DEMO-{clave.upper()}-2026",
                defaults={
                    "monto": contrato.precio_acordado,
                    "fecha_pago": timezone.now(),
                    "metodo_pago": Pago.MetodoPago.TRANSFERENCIA,
                    "estado": Pago.Estado.PAGADO,
                },
            )

    def _cargar_diagnostico(self, empresa, paquete):
        Diagnostico.objects.update_or_create(
            empresa=empresa,
            indice_proteccion=4,
            nivel_riesgo=Diagnostico.NivelRiesgo.MEDIO,
            defaults={
                "paquete_recomendado": paquete,
                "tiene_antivirus": True,
                "tiene_respaldo": False,
                "tiene_contrasenas_2fa": True,
                "tiene_firewall": True,
                "tiene_actualizaciones": True,
                "tiene_politica_escrita": False,
            },
        )

    def _cargar_lecciones(self):
        especificaciones = (
            {
                "titulo": "Contraseñas seguras",
                "contenido": (
                    "Usa una contraseña distinta para cada cuenta importante. "
                    "Una frase larga es más difícil de adivinar que una palabra "
                    "corta. Evita fechas de nacimiento y nombres que otras "
                    "personas puedan conocer. Activa la verificación en dos "
                    "pasos cuando esté disponible."
                ),
                "duracion_minutos": 5,
                "orden": 1,
                "tipo": Leccion.Tipo.LECCION,
            },
            {
                "titulo": "Cómo reconocer un correo falso",
                "contenido": (
                    "Desconfía de los mensajes que te apuran o amenazan con "
                    "cerrar una cuenta. Revisa con cuidado quién envía el "
                    "correo antes de abrir enlaces o archivos. Nunca compartas "
                    "contraseñas ni códigos por correo. Si tienes dudas, "
                    "confirma el mensaje por un canal que ya conoces."
                ),
                "duracion_minutos": 6,
                "orden": 2,
                "tipo": Leccion.Tipo.LECCION,
            },
            {
                "titulo": "Copias de respaldo",
                "contenido": (
                    "Guarda copias de los documentos importantes de tu "
                    "negocio. Programa respaldos regulares para no depender de "
                    "hacerlos manualmente. Conserva una copia separada de los "
                    "equipos que usas a diario. Comprueba de vez en cuando que "
                    "puedes recuperar los archivos."
                ),
                "duracion_minutos": 5,
                "orden": 3,
                "tipo": Leccion.Tipo.LECCION,
            },
            {
                "titulo": "Uso seguro de redes sociales",
                "contenido": (
                    "Publica solo la información del negocio que deseas hacer "
                    "pública. Limita quién puede entrar a las cuentas de la "
                    "empresa. Usa contraseñas diferentes y activa la "
                    "verificación en dos pasos. Revisa los mensajes antes de "
                    "abrir enlaces o compartir datos."
                ),
                "duracion_minutos": 6,
                "orden": 4,
                "tipo": Leccion.Tipo.LECCION,
            },
            {
                "titulo": "Simulacro de phishing",
                "contenido": (
                    "Lee cada correo de ejemplo con atención. Decide si el "
                    "mensaje intenta engañarte o si es legítimo. Al enviar tus "
                    "respuestas verás el puntaje y una explicación breve."
                ),
                "duracion_minutos": 8,
                "orden": 5,
                "tipo": Leccion.Tipo.SIMULACRO,
            },
        )
        lecciones = {}
        for datos in especificaciones:
            leccion, _ = Leccion.objects.update_or_create(
                titulo=datos["titulo"],
                defaults={
                    **datos,
                    "estado": Leccion.Estado.ACTIVA,
                },
            )
            lecciones[datos["titulo"]] = leccion
        return lecciones

    def _cargar_progresos(self, usuario, lecciones):
        ahora = timezone.now()
        especificaciones = (
            ("Contraseñas seguras", ProgresoLeccion.Estado.COMPLETADA, None),
            (
                "Cómo reconocer un correo falso",
                ProgresoLeccion.Estado.COMPLETADA,
                None,
            ),
            ("Copias de respaldo", ProgresoLeccion.Estado.EN_CURSO, None),
            (
                "Uso seguro de redes sociales",
                ProgresoLeccion.Estado.PENDIENTE,
                None,
            ),
            (
                "Simulacro de phishing",
                ProgresoLeccion.Estado.COMPLETADA,
                80,
            ),
        )
        for titulo, estado, puntaje in especificaciones:
            ProgresoLeccion.objects.update_or_create(
                usuario=usuario,
                leccion=lecciones[titulo],
                defaults={
                    "estado": estado,
                    "puntaje": puntaje,
                    "fecha_completada": (
                        ahora
                        if estado == ProgresoLeccion.Estado.COMPLETADA
                        else None
                    ),
                },
            )

    def _cargar_tickets(self, usuarios, empresas):
        ahora = timezone.now()
        especificaciones = (
            {
                "clave": "correo",
                "empresa": empresas["colmado"],
                "asunto": "Correo sospechoso recibido",
                "descripcion": (
                    "Recibí un correo que me pide confirmar la contraseña "
                    "del negocio."
                ),
                "tipo": Ticket.Tipo.INCIDENTE,
                "prioridad": Ticket.Prioridad.ALTA,
                "estado": Ticket.Estado.ABIERTO,
            },
            {
                "clave": "respaldo",
                "empresa": empresas["colmado"],
                "asunto": "Consulta sobre respaldo",
                "descripcion": "Quisiera conocer el estado del respaldo.",
                "tipo": Ticket.Tipo.CONSULTA,
                "prioridad": Ticket.Prioridad.MEDIA,
                "estado": Ticket.Estado.CERRADO,
            },
            {
                "clave": "contrasena",
                "empresa": empresas["colmado"],
                "asunto": "Cambio de contraseña",
                "descripcion": "Solicité ayuda para cambiar una contraseña.",
                "tipo": Ticket.Tipo.SOLICITUD,
                "prioridad": Ticket.Prioridad.BAJA,
                "estado": Ticket.Estado.CERRADO,
            },
            {
                "clave": "clinica",
                "empresa": empresas["clinica"],
                "asunto": "Revisar correo de la clínica",
                "descripcion": "Necesitamos revisar un correo recibido.",
                "tipo": Ticket.Tipo.INCIDENTE,
                "prioridad": Ticket.Prioridad.MEDIA,
                "estado": Ticket.Estado.ABIERTO,
            },
            {
                "clave": "ferreteria",
                "empresa": empresas["ferreteria"],
                "asunto": "Ayuda con un equipo",
                "descripcion": "Uno de los equipos necesita revisión.",
                "tipo": Ticket.Tipo.SOLICITUD,
                "prioridad": Ticket.Prioridad.BAJA,
                "estado": Ticket.Estado.ABIERTO,
            },
        )
        tickets = {}
        for datos in especificaciones:
            ticket, _ = Ticket.objects.update_or_create(
                empresa=datos["empresa"],
                asunto=datos["asunto"],
                defaults={
                    "descripcion": datos["descripcion"],
                    "tipo": datos["tipo"],
                    "prioridad": datos["prioridad"],
                    "estado": datos["estado"],
                    "fecha_cierre": (
                        ahora
                        if datos["estado"] == Ticket.Estado.CERRADO
                        else None
                    ),
                },
            )
            tickets[datos["clave"]] = ticket

        mensajes = (
            (
                usuarios["cliente"],
                "Recibí ese correo. ¿Debo abrir el enlace que aparece en el mensaje?",
            ),
            (
                usuarios["admin"],
                "No respondas el correo ni abras sus enlaces. Ya lo estamos revisando.",
            ),
        )
        for usuario, mensaje in mensajes:
            SeguimientoTicket.objects.update_or_create(
                ticket=tickets["correo"],
                usuario=usuario,
                mensaje=mensaje,
                defaults={},
            )
