import logging
import json
from datetime import datetime, time
import pytz
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)


@csrf_exempt
def api_fakeinfo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            aula = data.get('aula')
            carnet = data.get('carnet')
            ciclo_solicitado = data.get('ciclo')
            codmat = data.get('codMat')
            fecha = data.get('fecha')

            if not aula or not carnet or not ciclo_solicitado or not codmat or not fecha:
                return JsonResponse({'error': 'Debe proporcionar aula, carnet, ciclo, codMat y fecha.'}, status=400)

            # Convertir la fecha proporcionada a un objeto datetime
            tz = pytz.timezone('America/El_Salvador')
            fecha_proporcionada = datetime.strptime(fecha, "%Y-%m-%dT%H:%M:%S")
            hora_actual_str = fecha_proporcionada.isoformat()

            # Consulta de validación en la base de datos para asegurar que el carnet está inscrito en el ciclo y materia solicitados
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.Carnet, b.Aula, b.Dias, b.Hora, b.CodMat, a.Ciclo
                    FROM academic_cargainscripcion a
                    JOIN academic_cargaacademica b ON a.CodMat = b.CodMat
                        AND a.Seccion = b.Seccion
                        AND a.Ciclo = b.Ciclo
                    WHERE a.Carnet = %s
                    AND a.Ciclo = %s
                    AND b.Aula = %s
                    AND b.CodMat = %s
                """, [carnet, ciclo_solicitado, aula, codmat])

                results = cursor.fetchall()

            if not results:
                return JsonResponse(
                    {'success': False, 'error': 'No se encontró inscripción válida para el ciclo solicitado.'},
                    status=400)

            # Obtener el día de la semana actual en número (lunes=1, domingo=7)
            dia_actual = fecha_proporcionada.isoweekday()

            dias_semana = {
                'Lu': 1,
                'Ma': 2,
                'Mie': 3,
                'Jue': 4,
                'Vie': 5,
                'Sab': 6,
                'Dom': 7
            }

            asistencia_valida = False

            for row in results:
                _, aula_result, dias, hora, codmat_db, ciclo = row
                lista_dias = dias.split('-')
                dias_numericos = [dias_semana.get(dia, 0) for dia in lista_dias]

                es_dia_valido = dia_actual in dias_numericos

                # Dividir el rango de horas
                hora_inicio_str, hora_fin_str = hora.split('-')
                hora_inicio = time.fromisoformat(hora_inicio_str)
                hora_fin = time.fromisoformat(hora_fin_str)

                # Validar que la fecha y hora proporcionada coinciden con los requisitos de la clase
                if es_dia_valido and (hora_inicio <= fecha_proporcionada.time() <= hora_fin):
                    asistencia_valida = True

                    # Conectar a MongoDB y registrar la asistencia
                    try:
                        client = MongoClient(settings.DATABASES['mongodb']['CLIENT']['host'],
                                             settings.DATABASES['mongodb']['CLIENT']['port'])
                        db = client[settings.DATABASES['mongodb']['NAME']]
                        collection = db['mdb_asistencia']

                        documento = collection.find_one({'_id': carnet})
                        if documento is None or 'asistencias' not in documento or not isinstance(
                                documento['asistencias'], list):
                            # Crear un nuevo documento si no existe
                            nuevo_documento = {
                                '_id': carnet,
                                'asistencias': [
                                    {
                                        'carnet': carnet,
                                        'ciclo': ciclo,
                                        'codMat': codmat_db,
                                        'fechas': [hora_actual_str]
                                    }
                                ]
                            }
                            collection.replace_one({'_id': carnet}, nuevo_documento, upsert=True)
                        else:
                            # Actualizar el documento existente en MongoDB
                            existe_asistencia = any(
                                asistencia.get('ciclo') == ciclo and asistencia.get('codMat') == codmat_db
                                for asistencia in documento['asistencias']
                            )

                            if not existe_asistencia:
                                # Insertar una nueva materia si no existe para el ciclo
                                collection.update_one(
                                    {'_id': carnet},
                                    {'$push': {
                                        'asistencias': {'carnet': carnet, 'ciclo': ciclo, 'codMat': codmat_db,
                                                        'fechas': [hora_actual_str]}
                                    }}
                                )
                            else:
                                # Agregar fecha a la materia y ciclo existentes
                                collection.update_one(
                                    {'_id': carnet, 'asistencias.ciclo': ciclo, 'asistencias.codMat': codmat_db},
                                    {'$addToSet': {'asistencias.$.fechas': hora_actual_str}}
                                )

                    except Exception as e:
                        logger.error(f'Error al insertar en MongoDB: {str(e)}')
                        return JsonResponse({'success': False, 'error': f'Error en MongoDB: {str(e)}'}, status=500)

            if asistencia_valida:
                return JsonResponse({'success': True, 'data': 'Asistencia registrada correctamente.'}, status=200)
            else:
                return JsonResponse({'success': False, 'error': 'Asistencia no válida en el horario.'}, status=400)

        except Exception as e:
            logger.error(f'Error al procesar la solicitud: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)