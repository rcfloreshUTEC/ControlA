import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import connection
from academic.models import CargaAcademica
from datetime import datetime, time
import pytz
from pymongo import MongoClient
from django.conf import settings
logger = logging.getLogger(__name__)

@login_required()
def agregar_asistencia(request):
    materias = CargaAcademica.objects.all()

    context = {
        'materias': materias,
        'page_name': 'Agregar asistencia',
    }

    if request.method == 'POST':
        try:
            # Obtener los datos enviados desde el formulario
            aula = request.POST.get('codMateria')
            carnet = request.POST.get('carnet')
            fecha = request.POST.get('fecha')

            if not aula or not carnet or not fecha:
                messages.error(request, 'Debe proporcionar el aula, el carnet y la fecha.')
                return redirect('agregar_asistencia')

            # Convertir la fecha proporcionada a objeto datetime
            tz = pytz.timezone('America/El_Salvador')
            fecha_proporcionada = datetime.strptime(fecha, "%Y-%m-%d %H:%M")
            fecha_proporcionada = tz.localize(fecha_proporcionada)

            # Obtener la fecha y hora actual en la misma zona horaria
            fecha_actual = datetime.now(tz)

            # Verificar si la fecha proporcionada es futura
            if fecha_proporcionada > fecha_actual:
                messages.error(request, "No se puede agregar asistencia a clases futuras.")
                return redirect('agregar_asistencia')

            hora_actual_str = fecha_proporcionada.isoformat()

            # Realizar la consulta en la base de datos
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

            # Obtener el día de la fecha proporcionada en formato numérico (lunes=1, domingo=7)
            dia_actual = fecha_proporcionada.isoweekday()

            # Diccionario para mapear los nombres cortos de los días a números
            dias_semana = {
                'Lu': 1,
                'Ma': 2,
                'Mie': 3,
                'Jue': 4,
                'Vie': 5,
                'Sab': 6,
                'Dom': 7
            }

            data = []
            rsmdb = False
            for row in results:
                carnet_db, aula_result, dias, hora, codmat, ciclo = row
                # Separar los días en la lista
                lista_dias = dias.split('-')

                # Convertir los días a sus valores numéricos
                dias_numericos = [dias_semana.get(dia, 0) for dia in lista_dias]

                # Verificar si el día actual está en la lista de días numéricos
                es_dia_valido = dia_actual in dias_numericos

                # Separar la hora de inicio y fin
                hora_inicio_str, hora_fin_str = hora.split('-')
                hora_inicio = time.fromisoformat(hora_inicio_str)
                hora_fin = time.fromisoformat(hora_fin_str)

                # Verificar si la hora proporcionada está en el rango de hora_inicio y hora_fin
                asistencia_valida = es_dia_valido and (hora_inicio <= fecha_proporcionada.time() <= hora_fin)

                data.append({
                    'Carnet': carnet_db,
                    'Aula': aula_result,
                    'Dias': dias,
                    'Hora': hora,
                    'CodMat': codmat,
                    'Ciclo': ciclo,
                    'DiaValido': es_dia_valido,
                    'AsistenciaValida': asistencia_valida
                })

            if asistencia_valida:
                try:
                    # Conexión a MongoDB
                    client = MongoClient(settings.DATABASES['mongodb']['CLIENT']['host'],
                                         settings.DATABASES['mongodb']['CLIENT']['port'])
                    db = client[settings.DATABASES['mongodb']['NAME']]
                    collection = db['mdb_asistencia']

                    # Formatear ciclo y sección
                    ciclo_formateado = f"Ciclo {ciclo}"
                    seccion = row[5]  # Ajusta según el índice donde está la sección en tu consulta SQL

                    # Verificar si el documento ya existe
                    documento = collection.find_one({'_id': carnet})

                    # Crear un documento nuevo si no existe
                    if documento is None:
                        nuevo_documento = {
                            '_id': carnet,
                            'asistencias': [
                                {
                                    'carnet': carnet,
                                    'ciclo': ciclo_formateado,
                                    'codMat': codmat,
                                    'seccion': seccion,
                                    'fechas': [hora_actual_str]
                                }
                            ]
                        }
                        collection.insert_one(nuevo_documento)
                    else:
                        # Verificar si existe la asistencia para el ciclo, materia y sección
                        existe_asistencia = any(
                            asistencia.get('ciclo') == ciclo_formateado and
                            asistencia.get('codMat') == codmat and
                            asistencia.get('seccion') == seccion
                            for asistencia in documento['asistencias']
                        )

                        if not existe_asistencia:
                            # Agregar una nueva asistencia
                            collection.update_one(
                                {'_id': carnet},
                                {'$push': {
                                    'asistencias': {
                                        'carnet': carnet,
                                        'ciclo': ciclo_formateado,
                                        'codMat': codmat,
                                        'seccion': seccion,
                                        'fechas': [hora_actual_str]
                                    }
                                }}
                            )
                        else:
                            # Actualizar una asistencia existente agregando la fecha
                            collection.update_one(
                                {'_id': carnet, 'asistencias.ciclo': ciclo_formateado, 'asistencias.codMat': codmat,
                                 'asistencias.seccion': seccion},
                                {'$addToSet': {'asistencias.$.fechas': hora_actual_str}}
                            )

                    rsmdb = True

                except Exception as e:
                    messages.error(request, f'Error al insertar en MongoDB: {str(e)}')
                    return redirect('agregar_asistencia')

            if rsmdb:
                messages.success(request, "Asistencia registrada exitosamente.")
            else:
                messages.warning(request, "No se pudo validar la asistencia.")

            context['results'] = data
            context['RSMDB'] = rsmdb

        except Exception as e:
            messages.error(request, f'Ocurrió un error al procesar la solicitud: {str(e)}')
            logger.error(f'Error al procesar la solicitud: {str(e)}')
            return redirect('agregar_asistencia')

        return redirect('agregar_asistencia')

    return render(request, 'teachers/agregar_asistencia.html', context)