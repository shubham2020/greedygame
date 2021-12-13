from django.db import transaction
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum

from data_tree.models import Country, Device, Metrics


@csrf_exempt
def insert(request):

    data = request.POST
    dims = data.get("dim", None)
    if not dims:
        response = {"status": "error", "data": "Must Provide Dimensions"}
        return JsonResponse(response, status=400)
    dims = json.loads(dims)

    metrics = data.get("metrics", None)
    if not metrics:
        response = {"status": "error", "data": "Must Provide Metrics"}
        return JsonResponse(response, status=400)
    metrics = json.loads(metrics)

    country = None
    device = None
    for dim in dims:
        if dim.get("key") == "country":
            country = dim.get("val")
        if dim.get("key") == "device":
            device = dim.get("val")

    time_spent = None
    web_req = None
    for metric in metrics:
        if metric.get("key") == "timespent":
            time_spent = metric.get("val")
        if metric.get("key") == "webreq":
            web_req = metric.get("val")

    if not country or not device:
        response = {"status": "error", "data": "Must Provide Country and Device"}
        return JsonResponse(response, status=400)

    country_obj = Country.objects.filter(symbol=country).first()
    if not country_obj:
        response = {"status": "error", "data": "Country not found"}
        return JsonResponse(response, status=404)

    device_obj = Device.objects.filter(name=device).first()
    if not device_obj:
        response = {"status": "error", "data": "Device not found"}
        return JsonResponse(response, status=404)

    try:
        if time_spent:
            int(time_spent)
        else:
            time_spent = 0
    except Exception as e:
        response = {"status": "error", "data": "Time Spent Must be an integer"}
        return JsonResponse(response, status=400)

    try:
        if web_req:
            int(web_req)
        else:
            web_req = 0
    except Exception as e:
        response = {"status": "error", "data": "Web Request Count Must be an integer"}
        return JsonResponse(response, status=400)

    try:
        with transaction.atomic():
            metrics, created = Metrics.objects.get_or_create(device=device_obj, country=country_obj,
                                                             defaults={'time_spent': 0, 'web_req': 0})

            metrics.time_spent += int(time_spent)
            metrics.web_req += int(web_req)
            metrics.save()

    except Exception as e:
        return JsonResponse({"status":"error", "data": "Metrics not updated"}, status=500)

    response = {"status": "success", "data": "Successfully Added Metrics"}
    return JsonResponse(response, status=200)


@csrf_exempt
def query(request):
    data = request.POST
    dims = data.get('dim', None)

    if not dims:
        return JsonResponse({"status": "error", "data": "Must provide either Country or Device or Both"},
                            status=400)
    dims = json.loads(dims)

    country = None
    device = None
    for dim in dims:
        if dim.get("key", None) == "country":
            country = dim.get("val")
        if dim.get("key", None) == "device":
            device = dim.get("val")

    q_c = Q()
    if country:
        country_obj = Country.objects.filter(symbol=country).first()
        if not country_obj:
            response = {"status": "error", "data": "Country not found"}
            JsonResponse(response, status=404)
        q_c = Q(country=country_obj)

    q_d = Q()
    if device:
        device_obj = Device.objects.filter(name=device).first()
        if not device_obj:
            response = {"status": "error", "data": "Device not found"}
            JsonResponse(response, status=404)

        q_d = Q(device=device_obj)

    q = Q(q_c & q_d)

    web_req_count = Metrics.objects.filter(q).aggregate(web_req_count=Sum('web_req')).get("web_req_count", 0)
    time_spent_count = Metrics.objects.filter(q).aggregate(time_spent_count=Sum('time_spent')).get("time_spent_count", 0)

    response = {
        "dim": dims,
        "metrics" : [
        {
            "key" : "webreq",
            "val" : web_req_count if web_req_count else 0
        },
        {
            "key" : "timespent",
            "val" : time_spent_count if time_spent_count else 0
        }
    ]
    }

    return JsonResponse(response, status=200)
