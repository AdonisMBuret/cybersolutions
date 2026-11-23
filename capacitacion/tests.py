from django.test import TestCase
from django.urls import reverse

from cuentas.models import Usuario
from .models import Leccion, ProgresoLeccion
from .views import CORREOS_SIMULACRO


class CapacitacionTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="cliente@ejemplo.com",
            password="ClaveSegura123!",
        )
        self.leccion = Leccion.objects.create(
            titulo="Cuidar las contraseñas",
            contenido="Usa una contraseña diferente para cada cuenta.",
            duracion_minutos=10,
            orden=1,
            tipo=Leccion.Tipo.LECCION,
            estado=Leccion.Estado.ACTIVA,
        )
        self.simulacro = Leccion.objects.create(
            titulo="Reconocer correos sospechosos",
            contenido="Lee con atención los ejemplos.",
            duracion_minutos=5,
            orden=2,
            tipo=Leccion.Tipo.SIMULACRO,
            estado=Leccion.Estado.ACTIVA,
        )
        self.client.force_login(self.usuario)

    def test_lista_muestra_progreso_y_protege_acceso(self):
        self.client.logout()
        respuesta_sin_sesion = self.client.get(
            reverse("capacitacion:lista")
        )
        self.assertEqual(respuesta_sin_sesion.status_code, 302)

        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse("capacitacion:lista"))
        self.assertContains(respuesta, "Progreso: 0 de 2 actividades completadas")
        self.assertContains(respuesta, "Cuidar las contraseñas")
        self.assertContains(respuesta, "Pendiente")

    def test_abrir_y_completar_leccion_guarda_el_progreso(self):
        url = reverse("capacitacion:leccion", args=[self.leccion.id])
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        progreso = ProgresoLeccion.objects.get(
            usuario=self.usuario,
            leccion=self.leccion,
        )
        self.assertEqual(progreso.estado, ProgresoLeccion.Estado.EN_CURSO)

        respuesta = self.client.post(url)
        self.assertRedirects(respuesta, url)
        progreso.refresh_from_db()
        self.assertEqual(progreso.estado, ProgresoLeccion.Estado.COMPLETADA)
        self.assertIsNotNone(progreso.fecha_completada)

    def test_simulacro_calcula_y_guarda_el_puntaje(self):
        respuestas = {
            f"correo_{correo['id']}": (
                "si" if correo["es_fraude"] else "no"
            )
            for correo in CORREOS_SIMULACRO
        }
        respuestas["correo_1"] = "no"

        respuesta = self.client.post(
            reverse("capacitacion:simulacro", args=[self.simulacro.id]),
            respuestas,
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "80 / 100")
        progreso = ProgresoLeccion.objects.get(
            usuario=self.usuario,
            leccion=self.simulacro,
        )
        self.assertEqual(progreso.estado, ProgresoLeccion.Estado.COMPLETADA)
        self.assertEqual(progreso.puntaje, 80)
        self.assertIsNotNone(progreso.fecha_completada)
        self.assertContains(
            self.client.get(reverse("capacitacion:lista")),
            "Puntaje anterior: 80 / 100",
        )

    def test_simulacro_exige_responder_todos_los_correos(self):
        respuesta = self.client.post(
            reverse("capacitacion:simulacro", args=[self.simulacro.id]),
            {"correo_1": "si"},
        )

        self.assertEqual(respuesta.status_code, 200)
        progreso = ProgresoLeccion.objects.get(
            usuario=self.usuario,
            leccion=self.simulacro,
        )
        self.assertEqual(progreso.estado, ProgresoLeccion.Estado.EN_CURSO)
        self.assertIsNone(progreso.puntaje)

    def test_simulacro_tiene_tres_ejemplos_fraudulentos_y_dos_legitimos(self):
        fraudulentos = sum(
            correo["es_fraude"] for correo in CORREOS_SIMULACRO
        )
        self.assertEqual(len(CORREOS_SIMULACRO), 5)
        self.assertEqual(fraudulentos, 3)
