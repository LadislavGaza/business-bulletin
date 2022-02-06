from django.db.models import Q, F, Max
from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.db import connection
from math import ceil
from dateutil import parser
from datetime import datetime
from json import loads
from aplikacia.models import OrPodanieIssues, BulletinIssues, RawIssues
from django.core.paginator import Paginator


def krizovatka(request):
    if request.method == 'GET':
        return get_metoda(request)
    elif request.method == 'POST':
        return post_metoda(request)


def dvojkrizovatka(request, reqid):
    if request.method == 'DELETE':
        return delete_metoda(reqid)
    if request.method == 'PUT':
        return put_metoda(request, reqid)
    if request.method == 'GET':
        return speciget_metoda(reqid)


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

    selected = OrPodanieIssues.objects.all()

    if sql_dict['query'] is not None:
        if validate_int(sql_dict['query']) is not None:
            selected = selected.filter(
                Q(corporate_body_name__icontains=sql_dict['query']) |
                Q(city__icontains=sql_dict['query']) |
                Q(cin=int(sql_dict['query']))
            )
        else:
            selected = selected.filter(
                Q(corporate_body_name__icontains=sql_dict['query']) |
                Q(city__icontains=sql_dict['query'])
            )

    if sql_dict['registration_date_lte'] is not None:
        selected = selected.filter(registration_date__lte=sql_dict['registration_date_lte'].date())

    if sql_dict['registration_date_gte'] is not None:
        selected = selected.filter(registration_date__gte=sql_dict['registration_date_gte'].date())

    if sql_dict['registration_date'] is not None:
        selected = selected.filter(registration_date__exact=sql_dict['registration_date'].date())

    ################

    # nulls last nemusi byt pri id
    if (sql_dict['order_type']).lower() == "desc":
        if sql_dict['order_by'] == "id":
            selected = selected.order_by('-'+sql_dict['order_by'])
        else:
            selected = selected.order_by(F(sql_dict['order_by']).desc(nulls_last=True))
    else:
        if sql_dict['order_by'] == "id":
            selected = selected.order_by(sql_dict['order_by'])
        else:
            selected = selected.order_by(F(sql_dict['order_by']).asc(nulls_last=True))

    # page_start = (sql_dict['page'] - 1) * sql_dict['per_page']
    # page_end = page_start + sql_dict['per_page']

    zastrankovane = Paginator(selected, sql_dict['per_page'])
    strana = zastrankovane.get_page(sql_dict['page'])
    listobjekov = strana.object_list

    # serializovanie pre json
    outputdata = []
    for obj in listobjekov:
        outputdata.append({
            'id': obj.id,
            "br_court_name": obj.br_court_name,
            "kind_name": obj.kind_name,
            "cin": obj.cin,
            "registration_date": obj.registration_date,
            "corporate_body_name": obj.corporate_body_name,
            "br_section": obj.br_section,
            "br_insertion": obj.br_insertion,
            "text": obj.text,
            "street": obj.street,
            "postal_code": obj.postal_code,
            "city": obj.city
        })

    pocet = selected.count()
    metadata_dict = {
        'page' : sql_dict['page'],
        'per_page' : sql_dict['per_page'],
        'pages' : ceil(pocet/sql_dict['per_page']),
        'total' : pocet
    }

    return JsonResponse(data={"items": outputdata, "metadata": metadata_dict}, json_dumps_params={'indent': 2, 'ensure_ascii': False})


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

    bulletmax = BulletinIssues.objects.filter(year=datetime.now().year).aggregate(Max('number'))['number__max']
    bullet = BulletinIssues(year=datetime.now().year, number=bulletmax+1,
                            published_at=datetime.utcnow(), created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    bullet.save()

    raw = RawIssues(bulletin_issue_id=bullet.id, file_name='-', content='-', created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    raw.save()

    input['bulletin_issue_id'] = bullet.id
    input['raw_issue_id'] = raw.id
    input['br_mark'] = "-"
    input['br_court_code'] = "-"
    input['kind_code'] = "-"
    input['created_at'] = datetime.utcnow()
    input['updated_at'] = datetime.utcnow()
    input['address_line'] = "%s, %s %s" % (input['street'], input['postal_code'], input['city'])

    podanie = OrPodanieIssues(bulletin_issue_id=input['bulletin_issue_id'],
                               raw_issue_id=input['raw_issue_id'],
                               br_mark=input['br_mark'],
                               br_court_code=input['br_court_code'],
                               br_court_name=input['br_court_name'],
                               kind_code=input['kind_code'],
                               kind_name=input['kind_name'],
                               cin=input['cin'],
                               registration_date=input['registration_date'],
                               corporate_body_name=input['corporate_body_name'],
                               br_section=input['br_section'],
                               br_insertion=input['br_insertion'],
                               text=input['text'],
                               created_at=datetime.utcnow(),
                               updated_at=datetime.utcnow(),
                               address_line=input['address_line'],
                               street=input['street'],
                               postal_code=input['postal_code'],
                               city=input['city'])
    podanie.save()

    inputNaOutput['id'] = podanie.id

    return JsonResponse(data={'response': inputNaOutput}, status=201)


########### delete ##############################
def delete_metoda(reqid):
    if validate_int(reqid) is None:
        return JsonResponse({'error': {'message': 'Záznam neexistuje'}}, status=404)
    else:

        try:
            podanie = OrPodanieIssues.objects.get(id=int(reqid))
        except:
            return JsonResponse({'error': {'message': 'Záznam neexistuje'}}, status=404)

        raw = podanie.raw_issue
        bullet = podanie.bulletin_issue

        if OrPodanieIssues.objects.filter(raw_issue=raw).count() == 1:
            if RawIssues.objects.filter(bulletin_issue=bullet).count() == 1 and OrPodanieIssues.objects.filter(bulletin_issue=bullet).count() == 1:
                bullet.delete()

            raw.delete()

        podanie.delete()

        return JsonResponse(data={},status=204)


####### put #######################################################
def put_metoda(request, reqid):

    if validate_int(reqid) is None:
        return JsonResponse({}, status=422)
    else:
        try:
            objekt = OrPodanieIssues.objects.get(id=int(reqid))
        except:
            return JsonResponse({}, status=422)


    try:
        input = loads(request.body.decode('UTF-8'))
    except:
        return JsonResponse({}, status=422)

    errory = []
    # print(input)

    upravenie = {
        'id': None,
        "br_court_name": None,
        "kind_name": None,
        "cin": None,
        "registration_date": None,
        "corporate_body_name": None,
        "br_section": None,
        "br_insertion": None,
        "text": None,
        "street": None,
        "postal_code": None,
        "city": None
    }
    nacitaneDaco = False

    for key in povinne_parametre:
        err_temp = None

        if key in input:  # ak sa tam polozka nachadza, ocheckuj ci je dobre
            if key == "cin":
                if not isinstance(input[key], int):
                    err_temp = {"field": key, "reasons": ["not_number"]}
                else:
                    upravenie[key] = input[key]
                    nacitaneDaco = True
            elif key == "registration_date":
                try:
                    input[key] = parser.parse(input[key])
                    rokzinputu = input[key].year
                    aktualnyrok = datetime.utcnow().year
                    if not aktualnyrok == rokzinputu:
                        err_temp = {"field": key, "reasons": ["invalid_range"]}
                    else:
                        upravenie[key] = input[key]
                        nacitaneDaco = True
                except:
                    err_temp = {"field": key, "reasons": ["invalid_range"]}
            else:  # overovac si stringove vstupy su ozaj string
                if not isinstance(input[key], str):
                    err_temp = {"field": key, "reasons": ["not_string"]}
                else:
                    upravenie[key] = input[key]
                    nacitaneDaco = True

        # else:  # ak sa tam polozka vobec ani nenachadza
        #     if key == "cin":
        #         err_temp = {"field": key, "reasons": ["required", "not_number"]}
        #     elif key == "registration_date":
        #         err_temp = {"field": key, "reasons": ["required", "invalid_range"]}
        #     else:
        #         err_temp = {"field": key, "reasons": ["required"]}

        if err_temp:
            errory.append(err_temp)


    if errory:
        return JsonResponse(data={'errors': errory}, status=422)
    if nacitaneDaco is False:
        return JsonResponse(data={}, status=422)

    #setattr ale mam rad bolest
    if upravenie['id'] is not None:
        objekt.id = upravenie['id']
    if upravenie['br_court_name'] is not None:
        objekt.br_court_name = upravenie['br_court_name']
    if upravenie['kind_name'] is not None:
        objekt.kind_name = upravenie['kind_name']
    if upravenie['cin'] is not None:
        objekt.cin = upravenie['cin']
    if upravenie['registration_date'] is not None:
        objekt.registration_date = upravenie['registration_date']
    if upravenie['corporate_body_name'] is not None:
        objekt.corporate_body_name = upravenie['corporate_body_name']
    if upravenie['br_section'] is not None:
        objekt.br_section = upravenie['br_section']
    if upravenie['br_insertion'] is not None:
        objekt.br_insertion = upravenie['br_insertion']
    if upravenie['text'] is not None:
        objekt.text = upravenie['text']
    if upravenie['street'] is not None:
        objekt.street = upravenie['street']
    if upravenie['postal_code'] is not None:
        objekt.postal_code = upravenie['postal_code']
    if upravenie['city'] is not None:
        objekt.city = upravenie['city']

    inputNaOutput = {
        'id': objekt.id,
        'br_court_name': objekt.br_court_name,
        'kind_name': objekt.kind_name,
        'cin': objekt.cin,
        'registration_date': objekt.registration_date,
        'corporate_body_name': objekt.corporate_body_name,
        'br_section': objekt.br_section,
        'br_insertion': objekt.br_insertion,
        'text': objekt.text,
        'street': objekt.street,
        'postal_code': objekt.postal_code,
        'city': objekt.city
    }

    objekt.save()
    return JsonResponse(data={'response': inputNaOutput}, status=201)


######## get s id parametrom #######################################
def speciget_metoda(reqid):
    if validate_int(reqid) is None:
        return JsonResponse({'error': {'message': 'Záznam neexistuje'}}, status=404)
    else:
        try:
            obj = OrPodanieIssues.objects.get(id=int(reqid))
        except:
            return JsonResponse({'error': {'message': 'Záznam neexistuje'}}, status=404)

    outputdata = {
        'id': obj.id,
        "br_court_name": obj.br_court_name,
        "kind_name": obj.kind_name,
        "cin": obj.cin,
        "registration_date": obj.registration_date,
        "corporate_body_name": obj.corporate_body_name,
        "br_section": obj.br_section,
        "br_insertion": obj.br_insertion,
        "text": obj.text,
        "street": obj.street,
        "postal_code": obj.postal_code,
        "city": obj.city
    }

    return JsonResponse(data={"items": outputdata}, json_dumps_params={'indent': 2, 'ensure_ascii': False})
