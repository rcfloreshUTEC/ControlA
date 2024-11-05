import csv
import logging
import chardet

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from academic.models.model_carga_academica import CargaAcademica

logger = logging.getLogger(__name__)

@login_required
def upload_carga_academica(request):
    context = {
        'page_name': 'Carga Académica',
    }

    if request.method == 'POST':
        archivo_csv = request.FILES['archivo']

        try:
            raw_data = archivo_csv.read()
            result = chardet.detect(raw_data)
            encoding_detected = result['encoding']
            logger.info(f"Codificación detectada inicialmente: {encoding_detected}")

            codificaciones = [encoding_detected, 'ISO-8859-1', 'utf-8']

            for encoding in codificaciones:
                try:
                    decoded_file = raw_data.decode(encoding).splitlines()
                    logger.info(f"Archivo decodificado correctamente con la codificación: {encoding}")
                    break
                except (UnicodeDecodeError, TypeError):
                    logger.warning(f"Fallo al decodificar con la codificación: {encoding}")
                    continue
            else:
                messages.error(request, "No se pudo decodificar el archivo CSV con las codificaciones probadas.")
                return redirect('upload_carga_academica')

            reader = csv.reader(decoded_file, delimiter=',')
            next(reader)

            registros_creados = 0

            for row in reader:
                try:
                    Escuela, CodMat, Nombre, Docente, CodEmp, Seccion, Hora, Dias, Cupo, Inscritos, Aula, Estado, Paralela, Ciclo = row

                    CargaAcademica.objects.create(
                        Escuela=Escuela,
                        CodMat=CodMat,
                        Nombre=Nombre,
                        Docente=Docente,
                        CodEmp=CodEmp,
                        Seccion=Seccion,
                        Hora=Hora,
                        Dias=Dias,
                        Cupo=int(Cupo),
                        Inscritos=int(Inscritos),
                        Aula=Aula,
                        Estado=Estado,
                        Paralela=Paralela,
                        Ciclo=Ciclo
                    )
                    registros_creados += 1
                    logger.info(f"Registro creado para {Nombre} con código de materia {CodMat}")
                except Exception as e:
                    logger.error(f"Error al procesar la fila: {row}. Error: {str(e)}")

            if registros_creados > 0:
                messages.success(request, f"Archivo CSV cargado y {registros_creados} registros procesados exitosamente.")
                logger.info(f"{registros_creados} registros creados con éxito.")
            else:
                messages.warning(request, "El archivo CSV no contiene registros válidos o no se pudieron procesar.")
                logger.warning("No se pudo crear ningún registro a partir del archivo CSV.")

        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar el archivo CSV: {str(e)}")
            logger.error(f"Error general al procesar el archivo CSV: {str(e)}")

        return redirect('upload_carga_academica')

    return render(request, 'academic/carga_datos_ae.html', context)