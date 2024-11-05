from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from django.conf import settings

@csrf_exempt
def get_mongo_data(request):
    try:
        # Conectar a MongoDB
        client = MongoClient(settings.DATABASES['mongodb']['CLIENT']['host'], settings.DATABASES['mongodb']['CLIENT']['port'])
        db = client[settings.DATABASES['mongodb']['NAME']]
        collection = db['mdb_asistencia']

        # Obtener todos los documentos de la colección
        data = list(collection.find({}, {'_id': 0}))

        return JsonResponse({'data': data}, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)