from django.test import TestCase
from django.urls import reverse

from cuentas.models import Usuario
from core.models import Empresa
from .models import SeguimientoTicket, Ticket


class TicketsTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            email="cliente@ejemplo.com",
            password="ClaveSegura123!",
        )
        self.empresa = Empresa.objects.create(
            usuario=self.cliente,
            nombre_comercial="Empresa de prueba",
            sector=Empresa.Sector.COMERCIO,
            tamano=Empresa.Tamano.MICRO,
            cantidad_empleados=5,
            cantidad_equipos=4,
            telefono="8095551234",
            direccion="Santo Domingo",
        )
        self.ticket = Ticket.objects.create(
            empresa=self.empresa,
            asunto="No puedo acceder",
            descripcion="No puedo entrar a mi cuenta.",
            tipo=Ticket.Tipo.INCIDENTE,
            prioridad=Ticket.Prioridad.MEDIA,
        )
        self.client.force_login(self.cliente)

    def test_cliente_crea_ticket_abierto_para_su_empresa(self):
        respuesta = self.client.post(
            reverse("tickets:nuevo"),
            {
                "asunto": "Revisar respaldo",
                "tipo": Ticket.Tipo.CONSULTA,
                "prioridad": Ticket.Prioridad.BAJA,
                "descripcion": "Necesito ayuda con mis copias.",
            },
        )

        nuevo = Ticket.objects.get(asunto="Revisar respaldo")
        self.assertRedirects(
            respuesta,
            reverse("tickets:detalle", args=[nuevo.id]),
        )
        self.assertEqual(nuevo.empresa, self.empresa)
        self.assertEqual(nuevo.estado, Ticket.Estado.ABIERTO)

    def test_cliente_no_puede_ver_ticket_de_otra_empresa(self):
        otro_cliente = Usuario.objects.create_user(
            email="otro@ejemplo.com",
            password="ClaveSegura123!",
        )
        otra_empresa = Empresa.objects.create(
            usuario=otro_cliente,
            nombre_comercial="Otra empresa",
            sector=Empresa.Sector.SALUD,
            tamano=Empresa.Tamano.PEQUENA,
            cantidad_empleados=20,
            cantidad_equipos=10,
            telefono="8095555678",
            direccion="Distrito Nacional",
        )
        ticket_ajeno = Ticket.objects.create(
            empresa=otra_empresa,
            asunto="Ticket privado",
            descripcion="Contenido privado.",
            tipo=Ticket.Tipo.CONSULTA,
            prioridad=Ticket.Prioridad.BAJA,
        )

        respuesta = self.client.get(
            reverse("tickets:detalle", args=[ticket_ajeno.id])
        )

        self.assertEqual(respuesta.status_code, 404)

    def test_cliente_puede_enviar_mensaje(self):
        respuesta = self.client.post(
            reverse("tickets:detalle", args=[self.ticket.id]),
            {
                "accion": "mensaje",
                "mensaje": "Ya reinicié el equipo.",
            },
        )

        self.assertRedirects(
            respuesta,
            reverse("tickets:detalle", args=[self.ticket.id]),
        )
        seguimiento = SeguimientoTicket.objects.get(ticket=self.ticket)
        self.assertEqual(seguimiento.usuario, self.cliente)
        self.assertEqual(seguimiento.mensaje, "Ya reinicié el equipo.")

    def test_personal_puede_cerrar_ticket_y_se_guarda_fecha(self):
        tecnico = Usuario.objects.create_user(
            email="tecnico@ejemplo.com",
            password="ClaveSegura123!",
            rol=Usuario.Rol.TECNICO,
        )
        self.client.force_login(tecnico)

        respuesta = self.client.post(
            reverse("tickets:detalle", args=[self.ticket.id]),
            {
                "accion": "estado",
                "estado": Ticket.Estado.CERRADO,
            },
        )

        self.assertRedirects(
            respuesta,
            reverse("tickets:detalle", args=[self.ticket.id]),
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.Estado.CERRADO)
        self.assertIsNotNone(self.ticket.fecha_cierre)

    def test_personal_puede_filtrar_tickets_por_estado(self):
        tecnico = Usuario.objects.create_user(
            email="tecnico@ejemplo.com",
            password="ClaveSegura123!",
            rol=Usuario.Rol.TECNICO,
        )
        Ticket.objects.create(
            empresa=self.empresa,
            asunto="Ticket cerrado",
            descripcion="Ya fue atendido.",
            tipo=Ticket.Tipo.CONSULTA,
            prioridad=Ticket.Prioridad.BAJA,
            estado=Ticket.Estado.CERRADO,
        )
        self.client.force_login(tecnico)

        respuesta = self.client.get(
            reverse("tickets:gestion"),
            {"estado": Ticket.Estado.ABIERTO},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, self.ticket.asunto)
        self.assertNotContains(respuesta, "Ticket cerrado")
