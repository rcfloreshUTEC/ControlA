from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.conf import settings
import json
from datetime import datetime, time
import pytz
from pymongo import MongoClient

@csrf_exempt
def check_student(request):
    # Verifica la API Key
    api_key = request.headers.get('X-API-KEY')
    if api_key != settings.API_KEY:
        return JsonResponse({'error': 'API Key no válida'}, status=403)

    tz = pytz.timezone('America/El_Salvador')

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            aula = body.get('aula')
            carnet = body.get('carnet')

            if not aula or not carnet:
                return JsonResponse({'error': 'Debe proporcionar el aula y el carnet.'}, status=400)

            # Realizar la consulta en la base de datos
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.Carnet, b.Aula, b.Dias, b.hora, b.CodMat, b.Ciclo, a.Seccion
                    FROM academic_cargainscripcion a
                    JOIN academic_cargaacademica b ON a.CodMat = b.CodMat AND a.Seccion = b.Seccion
                    WHERE b.Aula = %s
                    AND a.Carnet = %s
                """, [aula, carnet])

                results = cursor.fetchall()

            dia_actual = datetime.now(tz).isoweekday()

            dias_semana = {
                'Lu': 1,
                'Ma': 2,
                'Mie': 3,
                'Jue': 4,
                'Vie': 5,
                'Sab': 6,
                'Dom': 7
            }

            hora_actual = datetime.now(tz)
            hora_actual_str = hora_actual.isoformat()

            data = []
            rsmdb = False
            for row in results:
                carnet, aula_result, dias, hora, codmat, ciclo, seccion = row
                lista_dias = dias.split('-')
                dias_numericos = [dias_semana.get(dia, 0) for dia in lista_dias]
                es_dia_valido = dia_actual in dias_numericos

                hora_inicio_str, hora_fin_str = hora.split('-')
                hora_inicio = time.fromisoformat(hora_inicio_str)
                hora_fin = time.fromisoformat(hora_fin_str)

                asistencia_valida = es_dia_valido and (hora_inicio <= hora_actual.time() <= hora_fin)

                data.append({
                    'Carnet': carnet,
                    'Aula': aula_result,
                    'Dias': dias,
                    'Hora': hora,
                    'CodMat': codmat,
                    'Ciclo': ciclo,
                    'Seccion': seccion,
                    'DiaValido': es_dia_valido,
                    'AsistenciaValida': asistencia_valida
                })

                if asistencia_valida:
                    try:
                        client = MongoClient(settings.DATABASES['mongodb']['CLIENT']['host'], settings.DATABASES['mongodb']['CLIENT']['port'])
                        db = client[settings.DATABASES['mongodb']['NAME']]
                        collection = db['mdb_asistencia']

                        documento = collection.find_one({'_id': carnet})
                        if documento is None or 'asistencias' not in documento or not isinstance(documento['asistencias'], list):
                            nuevo_documento = {
                                '_id': carnet,
                                'asistencias': [
                                    {
                                        'carnet': carnet,
                                        'ciclo': ciclo,
                                        'codMat': codmat,
                                        'seccion': seccion,
                                        'fechas': [hora_actual_str]
                                    }
                                ]
                            }
                            collection.replace_one({'_id': carnet}, nuevo_documento, upsert=True)
                        else:
                            existe_asistencia = any(
                                asistencia.get('ciclo') == ciclo and asistencia.get('codMat') == codmat and asistencia.get('seccion') == seccion
                                for asistencia in documento['asistencias']
                            )

                            if not existe_asistencia:
                                collection.update_one(
                                    {'_id': carnet},
                                    {'$push': {'asistencias': {'carnet': carnet, 'ciclo': ciclo, 'codMat': codmat, 'seccion': seccion, 'fechas': [hora_actual_str]}}}
                                )
                            else:
                                collection.update_one(
                                    {'_id': carnet, 'asistencias.ciclo': ciclo, 'asistencias.codMat': codmat, 'asistencias.seccion': seccion},
                                    {'$addToSet': {'asistencias.$.fechas': hora_actual_str}}
                                )

                        rsmdb = True

                    except Exception as e:
                        return JsonResponse({'error': f'Error al insertar en MongoDB: {str(e)}'}, status=500)

            return JsonResponse({'results': data, 'RSMDB': rsmdb}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'El cuerpo de la solicitud no es un JSON válido.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método no permitido.'}, status=405)