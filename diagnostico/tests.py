from decimal import Decimal

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from cuentas.models import Usuario
from core.models import Empresa, Paquete

from .calculos import calcular_resultado
from .models import Diagnostico, Reporte


class CalcularResultadoTests(SimpleTestCase):
    def test_cero_respuestas_positivas_recomienda_completo(self):
        resultado = calcular_resultado((False, False, False, False, False, False))

        self.assertEqual(resultado["indice_proteccion"], 0)
        self.assertEqual(resultado["nivel_riesgo"], "ALTO")
        self.assertEqual(resultado["nombre_paquete"], "Completo")

    def test_tres_respuestas_positivas_recomienda_intermedio(self):
        resultado = calcular_resultado((True, True, True, False, False, False))

        self.assertEqual(resultado["indice_proteccion"], 3)
        self.assertEqual(resultado["nivel_riesgo"], "MEDIO")
        self.assertEqual(resultado["nombre_paquete"], "Intermedio")

    def test_seis_respuestas_positivas_recomienda_basico(self):
        resultado = calcular_resultado((True, True, True, True, True, True))

        self.assertEqual(resultado["indice_proteccion"], 6)
        self.assertEqual(resultado["nivel_riesgo"], "BAJO")
        self.assertEqual(resultado["nombre_paquete"], "Básico")


class ReportePDFTests(TestCase):
    def setUp(self):
        self.dueno = Usuario.objects.create_user(
            "dueno@ejemplo.do",
            "clave-temporal",
        )
        self.otro_usuario = Usuario.objects.create_user(
            "otro@ejemplo.do",
            "clave-temporal",
        )
        self.empresa = Empresa.objects.create(
            usuario=self.dueno,
            nombre_comercial="Empresa de prueba",
            sector=Empresa.Sector.COMERCIO,
            tamano=Empresa.Tamano.MICRO,
            cantidad_empleados=3,
            cantidad_equipos=2,
            telefono="8095551234",
            direccion="Distrito Nacional",
        )
        paquete = Paquete.objects.create(
            nombre=Paquete.Nombre.COMPLETO,
            descripcion="Paquete de prueba",
            servicios_incluidos="Protección",
            precio_mensual=Decimal("7000.00"),
            estado=Paquete.Estado.ACTIVO,
        )
        self.diagnostico = Diagnostico.objects.create(
            empresa=self.empresa,
            paquete_recomendado=paquete,
            tiene_antivirus=True,
            indice_proteccion=1,
            nivel_riesgo=Diagnostico.NivelRiesgo.ALTO,
        )
        self.url = reverse(
            "diagnostico:reporte_pdf",
            kwargs={"id": self.diagnostico.id},
        )

    def test_dueno_descarga_pdf_y_se_registra_el_reporte(self):
        self.client.force_login(self.dueno)

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "application/pdf")
        self.assertIn("attachment;", respuesta["Content-Disposition"])
        self.assertTrue(respuesta.content.startswith(b"%PDF"))
        reporte = Reporte.objects.get(diagnostico=self.diagnostico)
        self.assertEqual(reporte.ruta_archivo, "generado bajo demanda")
        self.assertIn("copias de respaldo", reporte.resumen.lower())

    def test_administrador_puede_descargar_el_pdf(self):
        administrador = Usuario.objects.create_user(
            "admin@ejemplo.do",
            "clave-temporal",
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.client.force_login(administrador)

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Reporte.objects.count(), 1)

    def test_otro_usuario_no_puede_descargar_el_pdf(self):
        self.client.force_login(self.otro_usuario)

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(Reporte.objects.count(), 0)
