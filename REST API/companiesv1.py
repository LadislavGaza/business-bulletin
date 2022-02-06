from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.db import connection
from math import ceil
from dateutil import parser
from datetime import datetime
from json import loads


def krizovatka(request):
    if request.method == 'GET':
        return get_metoda(request)


#### get #####################################################################
keys = ('cin', 'name', 'br_section', 'address_line', 'last_update', 'or_podanie_issues_count',
        'znizenie_imania_issues_count', 'likvidator_issues_count', 'konkurz_vyrovnanie_issues_count',
        'konkurz_restrukturalizacia_actors_count')

def_dict = {
    'cin' : None,
    'name' : None,
    'br_section' : None,
    'address_line' : None,
    'last_update' : None,
    'or_podanie_issues_count' : None,
    'znizenie_imania_issues_count' : None,
    'likvidator_issues_count' : None,
    'konkurz_vyrovnanie_issues_count' : None,
    'konkurz_restrukturalizacia_actors_count' : None,
    'page' : 1,
    'per_page' : 10,
    'last_update_gte' : None,
    'last_update_lte' : None,
    'query' : None,
    'order_by' : None,
    'order_type' : 'desc'
}

def get_metoda(request):
    sql_dict = def_dict.copy()

    for key in sql_dict:
        temp = request.GET.get(key)

        if temp is not None:
            if key == 'page' or key == 'per_page' or key == 'cin':
                temp = validate_int(temp)
                if temp is not None:
                    sql_dict[key] = temp
            elif key == 'last_update_lte' or key == 'last_update_gte':  #aj last update cisty??
                try:
                    sql_dict[key] = parser.parse(temp)
                except:
                    sql_dict[key] = None
            elif key == 'order_by':
                if temp in keys:
                    sql_dict[key] = temp
            elif key == 'order_type':
                if temp.lower() == "desc" or temp.lower() == "asc":
                    sql_dict[key] = temp
            else:
                sql_dict[key] = temp

    ##################

    que_select = "SELECT " + ", ".join(keys) + " FROM ov.companies "
    que_strany = "LIMIT %s OFFSET %s;" % (str(sql_dict['per_page']), str((sql_dict['page'] - 1) * sql_dict['per_page']))

    ##################
    que_where = ""
    que_where_arr = []

    if sql_dict['query'] is not None:
        sql_dict['subquery'] = '%' + sql_dict['query'] + '%'  # pre substring , prida subquery do dictionary
        que_where_arr.append("(name ILIKE %(subquery)s OR address_line ILIKE %(subquery)s) ")

    if sql_dict['last_update_lte'] is not None:
        que_where_arr.append("(last_update <= %(last_update_lte)s) ")

    if sql_dict['last_update_gte'] is not None:
        que_where_arr.append("(last_update >= %(last_update_gte)s) ")

    ################

    if que_where_arr:
        que_where = " AND ".join(que_where_arr)
        que_where = "WHERE " + que_where

    ###############
    order = ""

    if sql_dict['order_by']:
        order += " ORDER BY {} {} ".format(sql_dict['order_by'], sql_dict['order_type'])

    ###############

    joiny = """
    LEFT JOIN (
        SELECT company_id, COUNT(company_id) as or_podanie_issues_count FROM ov.or_podanie_issues GROUP BY company_id
    )AS podanie ON ov.companies.cin = podanie.company_id
    
    LEFT JOIN (
        SELECT company_id, COUNT(company_id) as znizenie_imania_issues_count FROM ov.znizenie_imania_issues GROUP BY company_id
    )AS imanie ON ov.companies.cin = imanie.company_id
    
    LEFT JOIN (
        SELECT company_id, COUNT(company_id) as likvidator_issues_count FROM ov.likvidator_issues GROUP BY company_id
    )AS likvidator ON ov.companies.cin = likvidator.company_id
    
    LEFT JOIN (
        SELECT company_id, COUNT(company_id) as konkurz_vyrovnanie_issues_count FROM ov.konkurz_vyrovnanie_issues GROUP BY company_id
    )AS vyrovnanie ON ov.companies.cin = vyrovnanie.company_id
    
    LEFT JOIN (
        SELECT company_id, COUNT(company_id) as konkurz_restrukturalizacia_actors_count FROM ov.konkurz_restrukturalizacia_actors GROUP BY company_id
    )AS restauracia ON ov.companies.cin = restauracia.company_id 
    """

    que_final = que_select + joiny + que_where + order + que_strany

    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM ov.companies " + que_where + ";", sql_dict)
        suma = cursor.fetchone()
        # print("Suma jest ", suma[0])
        cursor.close()

    metadata_dict = {
        'page' : sql_dict['page'],
        'per_page' : sql_dict['per_page'],
        'pages' : ceil(suma[0]/sql_dict['per_page']),
        'total' : suma[0]
    }

    with connection.cursor() as cursor:
        #print(que_final)
        cursor.execute(que_final, sql_dict)
        outputlist = cursor.fetchall()
        return JsonResponse({"items": [dict(zip(keys, output)) for output in outputlist], "metadata": metadata_dict},  json_dumps_params={'indent': 2, 'ensure_ascii': False})


def validate_int(numb):
    try:
        numb = int(numb)
        if numb < 1:
            return None
    except:
        return None
    return numb
