from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from django.conf import settings
import json

@csrf_exempt
def api_fakeinfo(request):
    if request.method == 'POST':
        try:
            # Extraer los datos enviados en la solicitud
            body = json.loads(request.body)
            aula = body.get('aula')
            carnet = body.get('carnet')
            ciclo = body.get('ciclo')
            codmat = body.get('codMat')
            seccion = body.get('seccion')
            fecha = body.get('fecha')

            # Verificar que todos los campos necesarios estén presentes
            if not (aula and carnet and ciclo and codmat and seccion and fecha):
                return JsonResponse({'error': 'Datos incompletos en la solicitud.'}, status=400)

            # Conectar a MongoDB
            client = MongoClient(settings.DATABASES['mongodb']['CLIENT']['host'], settings.DATABASES['mongodb']['CLIENT']['port'])
            db = client[settings.DATABASES['mongodb']['NAME']]
            collection = db['mdb_asistencia']

            # Buscar o insertar en el documento del carnet correspondiente
            filtro_documento = {'_id': carnet}
            actualizacion_asistencia = {
                '$addToSet': {
                    'asistencias.$[asistencia].fechas': fecha
                }
            }
            array_filters = [
                {'asistencia.ciclo': ciclo, 'asistencia.codMat': codmat, 'asistencia.seccion': seccion, 'asistencia.aula': aula}
            ]

            resultado = collection.update_one(
                filtro_documento,
                actualizacion_asistencia,
                array_filters=array_filters
            )

            if resultado.modified_count == 0:
                # Si no existía, crear la estructura completa
                nueva_asistencia = {
                    'carnet': carnet,
                    'ciclo': ciclo,
                    'codMat': codmat,
                    'seccion': seccion,
                    'aula': aula,
                    'fechas': [fecha]
                }
                collection.update_one(
                    filtro_documento,
                    {'$push': {'asistencias': nueva_asistencia}},
                    upsert=True
                )

            return JsonResponse({'success': True}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'El cuerpo de la solicitud no es un JSON válido.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método no permitido.'}, status=405)