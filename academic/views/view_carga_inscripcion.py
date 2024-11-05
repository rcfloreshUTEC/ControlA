import csv
import logging
import chardet

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from academic.models.model_carga_inscripcion import CargaInscripcion

logger = logging.getLogger(__name__)

@login_required
def upload_carga_inscripcion(request):
    context = {
        'page_name': 'Carga Inscripción',
    }

    if request.method == 'POST':
        archivo_csv = request.FILES['archivo']

        try:
            raw_data = archivo_csv.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            logger.info(f"Codificación detectada: {encoding}")

            decoded_file = raw_data.decode(encoding, errors='replace').encode('utf-8').decode('utf-8').splitlines()
            reader = csv.reader(decoded_file, delimiter=',')
            next(reader)

            registros_creados = 0


            for row in reader:
                try:
                    Carnet, CodMat, Seccion, CodInscripcion = row

                    CargaInscripcion.objects.create(
                        Carnet=Carnet,
                        CodMat=CodMat,
                        Seccion=Seccion,
                        CodInscripcion=CodInscripcion
                    )
                    registros_creados += 1
                    logger.info(f"Registro creado para {Carnet} con código de materia {CodMat}")
                except Exception as e:
                    logger.error(f"Error al procesar la fila: {row}. Error: {str(e)}")

            if registros_creados > 0:
                messages.success(request, f"Archivo CSV cargado y {registros_creados} registros procesados exitosamente.")
                logger.info(f"{registros_creados} registros creados con éxito.")
            else:
                messages.warning(request, "El archivo CSV no contiene registros válidos o no se pudieron procesar.")
                logger.warning("No se pudo crear ningún registro a partir del archivo CSV.")

        except Exception as e:
            logger.error(f"Error general al procesar el archivo CSV: {str(e)}")
            messages.error(request, "Error al procesar el archivo CSV. Por favor, revise el archivo y vuelva a intentarlo.")

        return redirect('upload_carga_academica')

    return render(request, 'academic/carga_datos_ae.html', context)