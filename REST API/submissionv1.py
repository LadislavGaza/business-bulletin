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
    elif request.method == 'POST':
        return post_metoda(request)

#### get #####################################################################
keys = ('id', 'br_court_name', 'kind_name', 'cin', 'registration_date', 'corporate_body_name', 'br_section', 'br_insertion', 'text', 'street', 'postal_code', 'city')

def_dict = {
    'id' : None,
    'br_court_name' : None,
    'kind_name' : None,
    'registration_date' : None,
    'corporate_body_name' : None,
    'br_section' : None,
    'br_insertion' : None,
    'text' : None,
    'street' : None,
    'postal_code' : None,
    'city' : None,
    'cin' : None,
    'page' : 1,
    'per_page' : 10,
    'registration_date_gte' : None,
    'registration_date_lte' : None,
    'query' : None,
    'order_by' : "id",
    'order_type' : "desc"
}

def get_metoda(request):
    sql_dict = def_dict.copy()

    for key in sql_dict:
        temp = request.GET.get(key)

        if temp is not None:
            if key == 'page' or key == 'per_page' or key == 'id' or key == 'cin':
                temp = validate_int(temp)
                if temp is not None:
                    sql_dict[key] = temp
            elif key == 'registration_date_lte' or key == 'registration_date_gte' or key == 'registration_date':
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

    que_select = "SELECT " + ", ".join(keys) + " FROM ov.or_podanie_issues "
    que_strany = "LIMIT %s OFFSET %s;" % (str(sql_dict['per_page']), str((sql_dict['page'] - 1) * sql_dict['per_page']))

    ##################
    que_where = ""
    que_where_arr = []

    if sql_dict['query'] is not None:
        sql_dict['subquery'] = '%' + sql_dict['query'] + '%' # pre substring , prida subquery do dictionary
        que_where_arr.append("(cast(cin as varchar) ILIKE %(query)s OR city ILIKE %(subquery)s OR corporate_body_name ILIKE %(subquery)s) ")

    if sql_dict['registration_date_lte'] is not None:
        que_where_arr.append("(registration_date <= %(registration_date_lte)s) ")

    if sql_dict['registration_date_gte'] is not None:
        que_where_arr.append("(registration_date >= %(registration_date_gte)s) ")

    if sql_dict['registration_date'] is not None:
        que_where_arr.append("(registration_date = %(registration_date)s) ")

    ################

    if que_where_arr:
        que_where = " AND ".join(que_where_arr)
        que_where = "WHERE " + que_where

    order = "ORDER BY {} {} ".format(sql_dict['order_by'], sql_dict['order_type'])

    que_final = que_select + que_where + order + que_strany

    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM ov.or_podanie_issues " + que_where + ";", sql_dict)
        suma = cursor.fetchone()
        #print("Suma jest ", suma[0])
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



##### post #####################################
povinne_parametre = ('br_court_name', 'kind_name', 'cin', 'registration_date', 'corporate_body_name', 'br_section',
                     'br_insertion', 'text', 'street', 'postal_code', 'city')


def post_metoda(request):
    input = loads(request.body.decode('UTF-8'))

    errory = []
    #print(input)

    for key in povinne_parametre:
        err_temp = None

        if key in input: #ak sa tam polozka nachadza, ocheckuj ci je dobre
            if key == "cin":
                if not isinstance(input[key], int):
                    err_temp = {"field": key, "reasons": ["not_number"]}
            elif key == "registration_date":
                try:
                    input[key] = parser.parse(input[key])
                    rokzinputu = input[key].year
                    aktualnyrok = datetime.utcnow().year
                    if not aktualnyrok == rokzinputu:
                        err_temp = {"field": key, "reasons": ["invalid_range"]}
                except:
                    err_temp = {"field": key, "reasons": ["invalid_range"]}
            else:  # overovac si stringove vstupy su ozaj string????
                if not isinstance(input[key], str):
                    err_temp = {"field": key, "reasons": ["required"]}
        else:  #ak sa tam polozka vobec ani nenachadza
            if key == "cin":
                err_temp = {"field": key, "reasons": ["required", "not_number"]}
            elif key == "registration_date":
                err_temp = {"field": key, "reasons": ["required", "invalid_range"]}
            else:
                err_temp = {"field": key, "reasons": ["required"]}

        if err_temp:
            errory.append(err_temp)

    if errory:
        return JsonResponse(data={'errors': errory}, status=422)

    inputNaOutput = input.copy()  # osetrenie nadbytocneho inputu (uz chcem ist spat)
    for key in inputNaOutput.keys():
        if key not in povinne_parametre:
            input.pop(key)
    inputNaOutput = input.copy()

    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO ov.bulletin_issues(year, number, published_at, created_at, updated_at) "
                       "VALUES  (%d, (SELECT max(number) FROM ov.bulletin_issues WHERE year = %d) +1, "
                       "current_date, current_timestamp, current_timestamp) RETURNING id;" % (aktualnyrok, aktualnyrok))
        output = cursor.fetchone()

        cursor.execute("INSERT INTO ov.raw_issues(bulletin_issue_id, file_name, content, created_at, updated_at) "
                       "VALUES (%d, '-', '-', current_timestamp, current_timestamp) "
                       "RETURNING id, bulletin_issue_id;" % (output[0]))
        output = cursor.fetchone()

        parametre = ", ".join(povinne_parametre) + ", bulletin_issue_id, raw_issue_id, br_mark, br_court_code, " \
                                                   "kind_code, created_at, updated_at, address_line"
        input['bulletin_issue_id'] = output[1]
        input['raw_issue_id'] = output[0]
        input['br_mark'] = "-"
        input['br_count_code'] = "-"
        input['kind_code'] = "-"
        input['created_at'] = datetime.utcnow()
        input['updated_at'] = datetime.utcnow()
        input['address_line'] = "%s, %s %s" % (input['street'], input['postal_code'], input['city'])

        listKlucov = []
        for item in input.keys():
            listKlucov.append("%(" + item + ")s")
        stringKlucov = ", ".join(listKlucov)

        cursor.execute("INSERT INTO ov.or_podanie_issues(%s) VALUES (%s) RETURNING id;" % (parametre, stringKlucov), input)
        output = cursor.fetchone()

    inputNaOutput['id'] = output[0]

    return JsonResponse(data={'response': inputNaOutput}, status=201)


########### delete ##############################
def delete_metoda(request, id):
    if request.method == 'DELETE':
        if validate_int(id) is None:
            return JsonResponse({'error': {'message' : 'Záznam neexistuje'}}, status=404)
        else:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM ov.or_podanie_issues WHERE id = %s;" %id)
                output = cursor.fetchone()
                if output is None:
                    return JsonResponse({'error': {'message': 'Záznam neexistuje'}}, status=404)
                else:
                    cursor.execute("BEGIN TRANSACTION;")
                    cursor.execute("DELETE FROM ov.or_podanie_issues WHERE id = %s "
                                   "RETURNING bulletin_issue_id, raw_issue_id;" %id)
                    output = cursor.fetchone()
                    bulletinid = output[0]
                    rawid = output[1]

                    cursor.execute("SELECT raw_issue_id FROM ov.or_podanie_issues WHERE raw_issue_id = %s;" % rawid)
                    output = cursor.fetchone()
                    if output is None:
                        cursor.execute("DELETE FROM ov.raw_issues WHERE id = %s;" %rawid)
                        cursor.execute("SELECT bulletin_issue_id FROM ov.raw_issues WHERE bulletin_issue_id = %s;" % bulletinid)
                        output1 = cursor.fetchone()
                        cursor.execute("SELECT bulletin_issue_id FROM ov.or_podanie_issues WHERE bulletin_issue_id = %s;" % bulletinid)
                        output2 = cursor.fetchone()
                        if output1 is None and output2 is None:
                            cursor.execute("DELETE FROM ov.bulletin_issues WHERE id = %s;" %bulletinid)
                    cursor.execute("COMMIT TRANSACTION;")
                    return JsonResponse(data={},status=204)
