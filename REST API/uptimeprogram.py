from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.db import connection

def uptime_db(arg):
    cursor = connection.cursor()
    cursor.execute("SELECT date_trunc('second', current_timestamp - pg_postmaster_start_time()) as aplikacia;")
    output = cursor.fetchone()
    response = JsonResponse({"pgsql": {"aplikacia": str(output[0]).replace(",", "")}})
    return response