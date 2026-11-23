import re
from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from capacitacion.models import Leccion, ProgresoLeccion
from cuentas.models import Usuario
from diagnostico.models import Diagnostico
from tickets.models import Ticket
from .models import Contrato, Empresa, Paquete, Pago


class ContratacionTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            "cliente@ejemplo.do",
            "clave-temporal",
        )
        self.empresa = Empresa.objects.create(
            usuario=self.cliente,
            nombre_comercial="Empresa de prueba",
            sector=Empresa.Sector.COMERCIO,
            tamano=Empresa.Tamano.MICRO,
            cantidad_empleados=3,
            cantidad_equipos=2,
            telefono="8095551234",
            direccion="Distrito Nacional",
        )
        self.paquete = Paquete.objects.create(
            nombre=Paquete.Nombre.INTERMEDIO,
            descripcion="Paquete de prueba",
            servicios_incluidos="Antivirus\nRespaldo",
            precio_mensual=Decimal("1000.00"),
            estado=Paquete.Estado.ACTIVO,
        )

    def test_catalogo_publico_muestra_paquetes_activos_y_recomendados(self):
        inactivo = Paquete.objects.create(
            nombre=Paquete.Nombre.COMPLETO,
            descripcion="Paquete inactivo",
            servicios_incluidos="Servicio",
            precio_mensual=Decimal("2000.00"),
            estado=Paquete.Estado.INACTIVO,
        )

        respuesta = self.client.get(
            reverse("core:paquetes"),
            {"recomendado": self.paquete.id},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Recomendado")
        self.assertContains(respuesta, "RD$ 1,000.00")
        self.assertNotContains(respuesta, inactivo.descripcion)

    def test_cliente_solicita_contrato_con_precio_mensual_descuento(self):
        self.client.force_login(self.cliente)
        catalogo = self.client.get(
            reverse("core:paquetes"),
            {"recomendado": self.paquete.id},
        )
        self.assertEqual(catalogo.status_code, 200)
        self.assertContains(catalogo, 'name="paquete"')

        descuentos = (
            (Contrato.TipoContrato.MENSUAL, Decimal("1000.00")),
            (Contrato.TipoContrato.TRIMESTRAL, Decimal("950.00")),
            (Contrato.TipoContrato.ANUAL, Decimal("900.00")),
        )

        for tipo_contrato, precio_esperado in descuentos:
            with self.subTest(tipo_contrato=tipo_contrato):
                respuesta = self.client.post(
                    reverse("core:paquetes"),
                    {
                        "paquete": self.paquete.id,
                        "tipo_contrato": tipo_contrato,
                    },
                )
                contrato = Contrato.objects.latest("id")

                self.assertRedirects(
                    respuesta,
                    reverse("core:pago", kwargs={"id": contrato.id}),
                    fetch_redirect_response=False,
                )
                self.assertEqual(contrato.empresa, self.empresa)
                self.assertEqual(contrato.estado, Contrato.Estado.SOLICITADO)
                self.assertEqual(contrato.precio_acordado, precio_esperado)

    def test_solo_clientes_pueden_solicitar_contratacion(self):
        respuesta_anonima = self.client.post(
            reverse("core:paquetes"),
            {
                "paquete": self.paquete.id,
                "tipo_contrato": Contrato.TipoContrato.MENSUAL,
            },
        )
        self.assertEqual(respuesta_anonima.status_code, 302)
        self.assertTrue(respuesta_anonima.url.startswith("/cuentas/acceso/"))

        administrador = Usuario.objects.create_user(
            "admin@ejemplo.do",
            "clave-temporal",
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.client.force_login(administrador)
        respuesta_administrador = self.client.post(
            reverse("core:paquetes"),
            {
                "paquete": self.paquete.id,
                "tipo_contrato": Contrato.TipoContrato.MENSUAL,
            },
        )

        self.assertEqual(respuesta_administrador.status_code, 403)
        self.assertEqual(Contrato.objects.count(), 0)

    def test_pago_activa_contrato_sin_guardar_datos_de_tarjeta(self):
        self.client.force_login(self.cliente)
        duraciones = (
            (Contrato.TipoContrato.MENSUAL, 30, Decimal("1000.00")),
            (Contrato.TipoContrato.TRIMESTRAL, 90, Decimal("950.00")),
            (Contrato.TipoContrato.ANUAL, 365, Decimal("900.00")),
        )

        for tipo_contrato, duracion, precio in duraciones:
            with self.subTest(tipo_contrato=tipo_contrato):
                contrato = Contrato.objects.create(
                    empresa=self.empresa,
                    paquete=self.paquete,
                    tipo_contrato=tipo_contrato,
                    precio_acordado=precio,
                )
                url_pago = reverse("core:pago", kwargs={"id": contrato.id})
                pagina_pago = self.client.get(url_pago)
                self.assertEqual(pagina_pago.status_code, 200)
                self.assertNotContains(pagina_pago, "Número de tarjeta")

                respuesta = self.client.post(
                    url_pago,
                    {
                        "nombre_titular": "Nombre de prueba",
                        "metodo_pago": Pago.MetodoPago.TARJETA,
                    },
                )

                self.assertRedirects(
                    respuesta,
                    "/panel/",
                    fetch_redirect_response=False,
                )
                contrato.refresh_from_db()
                pago = Pago.objects.get(contrato=contrato)
                fecha_inicio = timezone.localdate()

                self.assertEqual(contrato.estado, Contrato.Estado.ACTIVO)
                self.assertEqual(contrato.fecha_inicio, fecha_inicio)
                self.assertEqual(
                    contrato.fecha_fin,
                    fecha_inicio + timedelta(days=duracion),
                )
                self.assertEqual(pago.estado, Pago.Estado.PAGADO)
                self.assertEqual(pago.monto, contrato.precio_acordado)
                self.assertEqual(pago.metodo_pago, Pago.MetodoPago.TARJETA)
                self.assertRegex(pago.referencia, re.compile(r"^[A-Z0-9]{10}$"))


class PanelesTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            "cliente@panel.do",
            "clave-temporal",
        )
        self.empresa = Empresa.objects.create(
            usuario=self.cliente,
            nombre_comercial="Compañía Ámbar",
            sector=Empresa.Sector.COMERCIO,
            tamano=Empresa.Tamano.MICRO,
            cantidad_empleados=4,
            cantidad_equipos=3,
            telefono="8095554321",
            direccion="Distrito Nacional",
        )
        self.paquete = Paquete.objects.create(
            nombre=Paquete.Nombre.BASICO,
            descripcion="Paquete para las pruebas",
            servicios_incluidos="Protección",
            precio_mensual=Decimal("2500.00"),
            estado=Paquete.Estado.ACTIVO,
        )

    def test_panel_cliente_muestra_diagnostico_contrato_y_tickets(self):
        Diagnostico.objects.create(
            empresa=self.empresa,
            indice_proteccion=4,
            nivel_riesgo=Diagnostico.NivelRiesgo.MEDIO,
        )
        Contrato.objects.create(
            empresa=self.empresa,
            paquete=self.paquete,
            tipo_contrato=Contrato.TipoContrato.MENSUAL,
            precio_acordado=Decimal("2500.00"),
            estado=Contrato.Estado.ACTIVO,
            fecha_inicio=timezone.localdate(),
            fecha_fin=timezone.localdate() + timedelta(days=30),
        )
        ticket = Ticket.objects.create(
            empresa=self.empresa,
            asunto="Revisar el respaldo",
            descripcion="El respaldo necesita revisión.",
            tipo=Ticket.Tipo.CONSULTA,
            prioridad=Ticket.Prioridad.MEDIA,
        )
        self.client.force_login(self.cliente)

        respuesta = self.client.get(reverse("core:panel"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Bienvenido, Compañía Ámbar")
        self.assertContains(respuesta, "4 / 6")
        self.assertContains(respuesta, "Básico")
        self.assertContains(respuesta, ticket.asunto)
        self.assertEqual(respuesta.context["tickets_abiertos"], 1)

    def test_panel_cliente_muestra_mensajes_si_no_hay_datos(self):
        self.client.force_login(self.cliente)

        respuesta = self.client.get(reverse("core:panel"))

        self.assertContains(respuesta, "Sin diagnóstico")
        self.assertContains(respuesta, "Sin contrato")
        self.assertEqual(respuesta.context["tickets_abiertos"], 0)

    def test_panel_personal_muestra_indicadores_y_filtra_contratos(self):
        contrato = Contrato.objects.create(
            empresa=self.empresa,
            paquete=self.paquete,
            tipo_contrato=Contrato.TipoContrato.TRIMESTRAL,
            precio_acordado=Decimal("2375.00"),
            estado=Contrato.Estado.ACTIVO,
            fecha_inicio=timezone.localdate(),
            fecha_fin=timezone.localdate() + timedelta(days=90),
        )
        Contrato.objects.create(
            empresa=self.empresa,
            paquete=self.paquete,
            tipo_contrato=Contrato.TipoContrato.MENSUAL,
            precio_acordado=Decimal("2500.00"),
            estado=Contrato.Estado.SOLICITADO,
        )
        Pago.objects.create(
            contrato=contrato,
            monto=Decimal("2375.00"),
            metodo_pago=Pago.MetodoPago.TRANSFERENCIA,
            referencia="PANEL12345",
            estado=Pago.Estado.PAGADO,
        )
        Ticket.objects.create(
            empresa=self.empresa,
            asunto="Ticket abierto",
            descripcion="Necesita atención.",
            tipo=Ticket.Tipo.INCIDENTE,
            prioridad=Ticket.Prioridad.ALTA,
        )
        administrador = Usuario.objects.create_user(
            "admin@panel.do",
            "clave-temporal",
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.client.force_login(administrador)

        respuesta = self.client.get(
            reverse("core:panel_admin"),
            {"q": "Compañía", "estado": Contrato.Estado.ACTIVO},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["clientes_activos"], 1)
        self.assertEqual(respuesta.context["contratos_vigentes"], 1)
        self.assertEqual(respuesta.context["tickets_abiertos"], 1)
        self.assertEqual(respuesta.context["ingresos_mes"], Decimal("2375.00"))
        self.assertContains(respuesta, "Compañía Ámbar")
        self.assertContains(respuesta, 'href="/panel-admin/"')
        self.assertEqual(
            list(respuesta.context["contratos"]),
            [contrato],
        )

    def test_exportacion_csv_usa_utf8_sig_y_los_filtros(self):
        Contrato.objects.create(
            empresa=self.empresa,
            paquete=self.paquete,
            tipo_contrato=Contrato.TipoContrato.ANUAL,
            precio_acordado=Decimal("2250.00"),
            estado=Contrato.Estado.ACTIVO,
            fecha_inicio=timezone.localdate(),
            fecha_fin=timezone.localdate() + timedelta(days=365),
        )
        administrador = Usuario.objects.create_user(
            "admin@panel.do",
            "clave-temporal",
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.client.force_login(administrador)

        respuesta = self.client.get(
            reverse("core:panel_admin"),
            {
                "q": "Compañía",
                "estado": Contrato.Estado.ACTIVO,
                "exportar": "csv",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.content.startswith(b"\xef\xbb\xbf"))
        contenido = respuesta.content.decode("utf-8-sig")
        self.assertIn("Cliente,Paquete,Tipo,Estado,Vence", contenido)
        self.assertIn("Compañía Ámbar", contenido)
        self.assertIn("Anual", contenido)

    def test_paneles_restringen_el_acceso_por_rol(self):
        self.client.force_login(self.cliente)
        respuesta_cliente = self.client.get(reverse("core:panel_admin"))
        self.assertEqual(respuesta_cliente.status_code, 403)

        administrador = Usuario.objects.create_user(
            "admin@panel.do",
            "clave-temporal",
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.client.force_login(administrador)
        respuesta_personal = self.client.get(reverse("core:panel"))
        self.assertEqual(respuesta_personal.status_code, 403)


class CargarDemoTests(TestCase):
    def test_comando_es_idempotente_y_carga_los_datos_solicitados(self):
        salida = StringIO()
        call_command("cargar_demo", stdout=salida)

        self.assertEqual(Usuario.objects.count(), 5)
        self.assertEqual(Empresa.objects.count(), 4)
        self.assertEqual(Paquete.objects.count(), 3)
        self.assertEqual(Contrato.objects.count(), 4)
        self.assertEqual(Pago.objects.count(), 2)
        self.assertEqual(Diagnostico.objects.count(), 1)
        self.assertEqual(Leccion.objects.count(), 5)
        self.assertEqual(ProgresoLeccion.objects.count(), 5)
        self.assertEqual(Ticket.objects.count(), 5)

        cliente = Usuario.objects.get(email="cliente@demo.do")
        self.assertTrue(cliente.check_password("Cliente12345!"))
        admin = Usuario.objects.get(email="admin@cybersolutions.do")
        self.assertEqual(admin.rol, Usuario.Rol.ADMINISTRADOR)
        self.assertTrue(admin.is_superuser)

        simulacro = Leccion.objects.get(titulo="Simulacro de phishing")
        progreso_simulacro = ProgresoLeccion.objects.get(
            usuario=cliente,
            leccion=simulacro,
        )
        self.assertEqual(progreso_simulacro.puntaje, 80)
        self.assertEqual(
            progreso_simulacro.estado,
            ProgresoLeccion.Estado.COMPLETADA,
        )

        call_command("cargar_demo", stdout=salida)
        self.assertEqual(Usuario.objects.count(), 5)
        self.assertEqual(Empresa.objects.count(), 4)
        self.assertEqual(Paquete.objects.count(), 3)
        self.assertEqual(Contrato.objects.count(), 4)
        self.assertEqual(Pago.objects.count(), 2)
        self.assertEqual(Diagnostico.objects.count(), 1)
        self.assertEqual(Leccion.objects.count(), 5)
        self.assertEqual(ProgresoLeccion.objects.count(), 5)
        self.assertEqual(Ticket.objects.count(), 5)
        self.assertEqual(
            Ticket.objects.get(asunto="Correo sospechoso recibido")
            .seguimientoticket_set.count(),
            2,
        )
        self.assertIn("admin@cybersolutions.do : Admin12345!", salida.getvalue())
        self.assertIn("cliente4@demo.do : Cliente12345!", salida.getvalue())
