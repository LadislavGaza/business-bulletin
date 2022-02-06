from django.core.paginator import Paginator
from django.db.models import Q, F, Count
from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.db import connection
from math import ceil
from dateutil import parser
from datetime import datetime
from json import loads
from aplikacia.models import Companies


def krizovatka(request):
    if request.method == 'GET':
        return get_metoda(request)


#### get #####################################################################
keys = ('cin', 'name', 'br_section', 'address_line', 'last_update', 'or_podanie_issues_count',
        'znizenie_imania_issues_count', 'likvidator_issues_count', 'konkurz_vyrovnanie_issues_count',
        'konkurz_restrukturalizacia_actors_count')

def_dict = {
    'cin': None,
    'name': None,
    'br_section': None,
    'address_line': None,
    'last_update': None,
    'or_podanie_issues_count': None,
    'znizenie_imania_issues_count': None,
    'likvidator_issues_count': None,
    'konkurz_vyrovnanie_issues_count': None,
    'konkurz_restrukturalizacia_actors_count': None,
    'page': 1,
    'per_page': 10,
    'last_update_gte': None,
    'last_update_lte': None,
    'query': None,
    'order_by': None,
    'order_type': "desc"
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
            elif key == 'last_update_lte' or key == 'last_update_gte':  # aj last update cisty??
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

    # que_select = "SELECT " + ", ".join(keys) + " FROM ov.companies "
    # que_strany = "LIMIT %s OFFSET %s;" % (str(sql_dict['per_page']), str((sql_dict['page'] - 1) * sql_dict['per_page']))

    selected = Companies.objects.all()

    if sql_dict['query'] is not None:
        selected = selected.filter(
            Q(name__icontains=sql_dict['query']) |
            Q(address_line__icontains=sql_dict['query'])
        )

    if sql_dict['last_update_lte'] is not None:
        selected = selected.filter(last_update__lte=sql_dict['last_update_lte'].date())

    if sql_dict['last_update_gte'] is not None:
        selected = selected.filter(last_update__gte=sql_dict['last_update_gte'].date())

    #########################

    selected = selected.annotate(or_podanie_issues_count=Count('orpodanieissues', distinct=True))\
        .annotate(znizenie_imania_issues_count=Count('znizenieimaniaissues', distinct=True)) \
        .annotate(likvidator_issues_count=Count('likvidatorissues', distinct=True)) \
        .annotate(konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues', distinct=True)) \
        .annotate(konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors', distinct=True))

    #########################
    numbers = ('cin', 'or_podanie_issues_count', 'znizenie_imania_issues_count', 'likvidator_issues_count',
               'konkurz_vyrovnanie_issues_count', 'konkurz_restrukturalizacia_actors_count')

    # nulls last nemusi byt pri cin lebo primary key not null
    if sql_dict['order_by'] is not None:
        if (sql_dict['order_type']).lower() == "desc":
            if sql_dict['order_by'] in numbers:
                selected = selected.order_by('-' + sql_dict['order_by'])
            else:
                selected = selected.order_by(F(sql_dict['order_by']).desc(nulls_last=True))
        else:
            if sql_dict['order_by'] in numbers:
                selected = selected.order_by(sql_dict['order_by'])
            else:
                selected = selected.order_by(F(sql_dict['order_by']).asc(nulls_last=True))

    ###############

    zastrankovane = Paginator(selected, sql_dict['per_page'])
    strana = zastrankovane.get_page(sql_dict['page'])
    listobjekov = strana.object_list

    # serializovanie pre json
    outputdata = []
    for obj in listobjekov:
        outputdata.append({
            "cin": obj.cin,
            "name": obj.name,
            "br_section": obj.br_section,
            "address_line": obj.address_line,
            "last_update": obj.last_update,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            'or_podanie_issues_count': obj.or_podanie_issues_count,
            'znizenie_imania_issues_count': obj.znizenie_imania_issues_count,
            'likvidator_issues_count': obj.likvidator_issues_count,
            'konkurz_vyrovnanie_issues_count': obj.konkurz_vyrovnanie_issues_count,
            'konkurz_restrukturalizacia_actors_count': obj.konkurz_restrukturalizacia_actors_count
        })

    pocet = selected.count()
    metadata_dict = {
        'page': sql_dict['page'],
        'per_page': sql_dict['per_page'],
        'pages': ceil(pocet / sql_dict['per_page']),
        'total': pocet
    }

    return JsonResponse({"items": outputdata, "metadata": metadata_dict},
                            json_dumps_params={'indent': 2, 'ensure_ascii': False})


def validate_int(numb):
    try:
        numb = int(numb)
        if numb < 1:
            return None
    except:
        return None
    return numb
