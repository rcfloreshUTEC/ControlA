import logging
import json
from datetime import datetime, time
import pytz
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)


# @login_required()
@csrf_exempt
def api_fakeinfo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            aula = data.get('aula')
            carnet = data.get('carnet')
            fecha = data.get('fecha')

            if not aula or not carnet or not fecha:
                return JsonResponse({'error': 'Debe proporcionar el aula, el carnet y la fecha.'}, status=400)

            tz = pytz.timezone('America/El_Salvador')
            fecha_proporcionada = datetime.strptime(fecha, "%Y-%m-%dT%H:%M:%S")
            hora_actual_str = fecha_proporcionada.isoformat()

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.Carnet, b.Aula, b.Dias, b.hora, b.CodMat, RIGHT(b.Ciclo, 7) as Ciclo
                    FROM academic_cargainscripcion a, academic_cargaacademica b
                    WHERE b.Aula = %s
                    AND a.Carnet = %s
                    AND a.Seccion = b.Seccion
                    AND a.CodMat = b.CodMat
                """, [aula, carnet])
                results = cursor.fetchall()

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
            asistencia_data = []

            for row in results:
                carnet_db, aula_result, dias, hora, codmat, ciclo = row
                lista_dias = dias.split('-')
                dias_numericos = [dias_semana.get(dia, 0) for dia in lista_dias]
                es_dia_valido = dia_actual in dias_numericos

                hora_inicio_str, hora_fin_str = hora.split('-')
                hora_inicio = time.fromisoformat(hora_inicio_str)
                hora_fin = time.fromisoformat(hora_fin_str)

                if es_dia_valido and (hora_inicio <= fecha_proporcionada.time() <= hora_fin):
                    asistencia_valida = True
                    asistencia_data.append({
                        'Carnet': carnet_db,
                        'Aula': aula_result,
                        'Dias': dias,
                        'Hora': hora,
                        'CodMat': codmat,
                        'Ciclo': ciclo
                    })

                    try:
                        client = MongoClient(settings.DATABASES['mongodb']['CLIENT']['host'],
                                             settings.DATABASES['mongodb']['CLIENT']['port'])
                        db = client[settings.DATABASES['mongodb']['NAME']]
                        collection = db['mdb_asistencia']

                        documento = collection.find_one({'_id': carnet})
                        if documento is None or 'asistencias' not in documento or not isinstance(
                                documento['asistencias'], list):
                            nuevo_documento = {
                                '_id': carnet,
                                'asistencias': [
                                    {
                                        'carnet': carnet,
                                        'ciclo': ciclo,
                                        'codMat': codmat,
                                        'fechas': [hora_actual_str]
                                    }
                                ]
                            }
                            collection.replace_one({'_id': carnet}, nuevo_documento, upsert=True)
                        else:
                            existe_asistencia = any(
                                asistencia.get('ciclo') == ciclo and asistencia.get('codMat') == codmat
                                for asistencia in documento['asistencias']
                            )

                            if not existe_asistencia:
                                collection.update_one(
                                    {'_id': carnet},
                                    {'$push': {
                                        'asistencias': {'carnet': carnet, 'ciclo': ciclo, 'codMat': codmat,
                                                        'fechas': [hora_actual_str]}
                                    }}
                                )
                            else:
                                collection.update_one(
                                    {'_id': carnet, 'asistencias.ciclo': ciclo, 'asistencias.codMat': codmat},
                                    {'$addToSet': {'asistencias.$.fechas': hora_actual_str}}
                                )

                    except Exception as e:
                        logger.error(f'Error al insertar en MongoDB: {str(e)}')
                        return JsonResponse({'success': False, 'error': f'Error en MongoDB: {str(e)}'}, status=500)

            if asistencia_valida:
                return JsonResponse({'success': True, 'data': asistencia_data}, status=200)
            else:
                return JsonResponse({'success': False, 'error': 'Asistencia no válida en el horario.'}, status=400)

        except Exception as e:
            logger.error(f'Error al procesar la solicitud: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido. Use POST.'}, status=405)