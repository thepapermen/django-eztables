# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import re

from operator import or_

from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.six import text_type, iteritems
from django.utils.six.moves import reduce, xrange
from django.views.generic import View
from django.views.generic.list import MultipleObjectMixin

from eztables.forms import DatatablesForm, DESC

JSON_MIMETYPE = 'application/json'

RE_FORMATTED = re.compile(r'\{(\w+)\}')

#: SQLite unsupported field types for regex lookups
UNSUPPORTED_REGEX_FIELDS = (
    models.IntegerField,
    models.BooleanField,
    models.NullBooleanField,
    models.FloatField,
    models.DecimalField,
)


def get_real_field(model, field_name):
    '''
    Get the real field from a model given its name.

    Handle nested models recursively (aka. ``__`` lookups)
    '''
    parts = field_name.split('__')
    field = model._meta.get_field(parts[0])
    if len(parts) == 1:
        return model._meta.get_field(field_name)
    elif isinstance(field, models.ForeignKey):
        return get_real_field(field.rel.to, '__'.join(parts[1:]))
    else:
        raise Exception('Unhandled field: %s' % field_name)


class DatatablesView(MultipleObjectMixin, View):
    '''
    Render a paginated server-side Datatables JSON view.

    See: http://www.datatables.net/usage/server-side
    '''
    fields = []
    _db_fields = None
    ServerSide = True
    _formatted_fields = False
    filters = {}

    def post(self, request, *args, **kwargs):
        return self.process_dt_response(request.POST)

    def get(self, request, *args, **kwargs):
        return self.process_dt_response(request.GET)

    def process_dt_response(self, data):
        # Switch between server-side and client-side mode. Given that
        # 'iColumns' is a needed server-side parameter, if it doesn't exist we
        # can safely switch to client-side.
        if 'iColumns' in data:
            self.generate_search_sets(data)
            self.form = DatatablesForm(data)
            if not self.form.is_valid():
                return HttpResponseBadRequest()
        else:
            self.form = None
            self.ServerSide = False
        self.qs = self.get_queryset()
        self.set_object_list()
        return self.render_to_response(self.form)

    def set_object_list(self):
        if isinstance(self.fields, dict):
            self.object_list = self.qs.values(*self.get_db_fields())
        else:
            self.object_list = self.qs.values_list(*self.get_db_fields())

    def get_db_fields(self):
        if not self._db_fields:
            self._db_fields = []
            fields = self.fields.values() if isinstance(self.fields, dict) else self.fields
            for field in fields:
                if RE_FORMATTED.match(field):
                    self._formatted_fields = True
                    self._db_fields.extend(RE_FORMATTED.findall(field))
                else:
                    self._db_fields.append(field)
        return self._db_fields

    @property
    def dt_data(self):
        return self.form.cleaned_data

    def get_field(self, index):
        if isinstance(self.fields, dict):
            return self.fields[self.dt_data['mDataProp_%s' % index]]
        else:
            return self.fields[index]

    def can_regex(self, field):
        '''Test if a given field supports regex lookups'''
        from django.conf import settings
        if settings.DATABASES['default']['ENGINE'].endswith('sqlite3'):
            return not isinstance(get_real_field(self.model, field), UNSUPPORTED_REGEX_FIELDS)
        else:
            return True

    def generate_search_sets(self, request):
        """Generate search sets from DataTables request.

        Search sets are lists of key-value pairs (in tuple format) that define
        the search space for the column search function and custom filter
        functions.  These lists are generated from the DataTables HTTP request
        using the following method:

        * If the request, has an argument that starts with "sSearch_" and whose
          value is not empty, then we decide on which search set it will be
          added.
        * The arguments that are added in the column search set must have as
          suffix a number that corresponds to a table column.
        * All other arguments are added in the filter search set.

        Note: The reason why we use the values of the HTTP request instead of
        the values of form.cleaned_data is because we cannot always know the
        filter name, i.e. what is followed after "sSearch_", which means that
        we cannot create a form field for it.
        """
        self.column_set = []
        self.filter_set = {}

        for param, value in iteritems(request):
            if not param.startswith("sSearch_"):
                continue
            if not value:
                continue

            _, search = param.split("_", 1)
            try:
                column_idx = int(search)
                if column_idx < int(request['iColumns']):
                    self.column_set.append((column_idx, value),)
                else:
                    self.filter_set[search] = value
            except ValueError:
                if '[]' in search:
                    value = request.getlist(param)
                    search = search.replace('[]', '')
                self.filter_set[search] = value

    def get_orders(self):
        '''Get ordering fields for ``QuerySet.order_by``'''
        orders = []
        iSortingCols = self.dt_data['iSortingCols']
        dt_orders = [(self.dt_data['iSortCol_%s' % i], self.dt_data['sSortDir_%s' % i]) for i in xrange(iSortingCols)]
        for field_idx, field_dir in dt_orders:
            direction = '-' if field_dir == DESC else ''
            if hasattr(self, 'sort_col_%s' % field_idx):
                method = getattr(self, 'sort_col_%s' % field_idx)
                result = method(direction)
                if isinstance(result, (bytes, text_type)):
                    orders.append(result)
                else:
                    orders.extend(result)
            else:
                field = self.get_field(field_idx)
                if RE_FORMATTED.match(field):
                    tokens = RE_FORMATTED.findall(field)
                    orders.extend(['%s%s' % (direction, token) for token in tokens])
                else:
                    orders.append('%s%s' % (direction, field))
        return orders

    def global_search(self, queryset):
        '''Filter a queryset with global search'''
        search = self.dt_data['sSearch']
        if search:
            if self.dt_data['bRegex']:
                criterions = [
                    Q(**{'%s__iregex' % field: search})
                    for field in self.get_db_fields()
                    if self.can_regex(field)
                ]
                if len(criterions) > 0:
                    search = reduce(or_, criterions)
                    queryset = queryset.filter(search)
            else:
                for term in search.split():
                    criterions = (Q(**{'%s__icontains' % field: term}) for field in self.get_db_fields())
                    search = reduce(or_, criterions)
                    queryset = queryset.filter(search)
        return queryset

    def column_search(self, queryset):
        '''Filter a queryset with column search'''
        for idx, search in self.column_set:
            if hasattr(self, 'search_col_%s' % idx):
                custom_search = getattr(self, 'search_col_%s' % idx)
                queryset = custom_search(search, queryset)
            else:
                field = self.get_field(idx)
                fields = RE_FORMATTED.findall(field) if RE_FORMATTED.match(field) else [field]
                if self.dt_data['bRegex_%s' % idx]:
                    criterions = [Q(**{'%s__iregex' % field: search}) for field in fields if self.can_regex(field)]
                    if len(criterions) > 0:
                        search = reduce(or_, criterions)
                        queryset = queryset.filter(search)
                else:
                    for term in search.split():
                        criterions = (Q(**{'%s__icontains' % field: term}) for field in fields)
                        search = reduce(or_, criterions)
                        queryset = queryset.filter(search)
        return queryset

    def get_filters(self):
        if hasattr(self, "_filters"):
            return
        if isinstance(self.filters, list):
            self._filters = dict((f.name, f) for f in self.filters)
        # We can't check if the provided type is FilterSet, unless we try to
        # import it, which would not be a clean solution. Therefore, anything
        # that's not a list, will be stored in self._filters.
        else:
            self._filters = self.filters

    def custom_filtering(self, queryset):
        if not self.filter_set:
            return queryset

        self.get_filters()
        # If the following succeeds, then the user has provided as a
        # django-filter FilterSet and we don't actually need to iterate the
        # filters.
        try:
            return self._filters(data=self.filter_set, queryset=queryset).qs
        except TypeError:
            pass

        for attr, query in iteritems(self.filter_set):
            if hasattr(self, "filter_%s" % attr):
                custom_filter = getattr(self, "filter_%s" % attr)
                queryset = custom_filter(queryset, query)
            else:
                try:
                    f = self._filters[attr]
                    queryset = f.filter(queryset, query)
                except KeyError:
                    raise Exception('Unsupported filter: %s' % attr)
        return queryset

    def get_queryset(self):
        '''Apply Datatables sort and search criterion to QuerySet'''
        qs = super(DatatablesView, self).get_queryset()
        # Bail if we are not in server-side mode
        if not self.ServerSide:
            return qs

        # Perform global search
        qs = self.global_search(qs)
        # Perform column search
        qs = self.column_search(qs)
        # Perform custom filtering
        qs = self.custom_filtering(qs)
        # Return the ordered queryset
        return qs.order_by(*self.get_orders())

    def get_page(self, form, object_list):
        '''Get the requested page'''
        page_size = form.cleaned_data['iDisplayLength']
        start_index = form.cleaned_data['iDisplayStart']
        paginator = Paginator(object_list, page_size)
        num_page = (start_index / page_size) + 1
        return paginator.page(num_page)

    def get_rows(self, rows):
        '''Format all rows'''
        if self._formatted_fields:
            return [self.get_row(row) for row in rows]
        else:
            if isinstance(self.fields, dict):
                return [dict((key, row[value])
                             for key, value in iteritems(self.fields))
                        for row in rows]
            else:
                return list(rows)

    def get_row(self, row):
        '''Format a single row (if necessary)'''

        if isinstance(self.fields, dict):
            return dict((key, text_type(value).format(**row)
                         if RE_FORMATTED.match(value) else row[value])
                        for key, value in self.fields.items())
        else:
            row = dict(zip(self._db_fields, row))
            return [text_type(field).format(**row) if RE_FORMATTED.match(field)
                    else row[field]
                    for field in self.fields]

    def format_data_rows(self, rows):
        if hasattr(self, 'format_data_row'):
            rows = [self.format_data_row(row) for row in rows]
        return rows

    def get_extra_data(self, extra_object_list):
        """Map user-defined function on extra object list.

        If the user has not defined a `get_extra_data_row` method, then this
        method has no effect.
        """
        if hasattr(self, 'get_extra_data_row'):
            return [self.get_extra_data_row(row) for row in extra_object_list]

    def add_extra_data(self, data, extra_object_list):
        """Add an 'extra' dictionary to the returned JSON.

        By default, no extra data will be added to the returned JSON, unless
        the user has specified a `get_extra_data_row` method or has overriden
        the existing `get_extra_data` method.
        """
        extra_data = self.get_extra_data(extra_object_list)
        if extra_data:
            data['extra'] = extra_data

    def render_to_response(self, form, **kwargs):
        '''Render Datatables expected JSON format'''
        if self.ServerSide and form.cleaned_data['iDisplayLength'] > 0:
            data_page = self.get_page(form, self.object_list)
            data_rows = self.get_rows(data_page.object_list)
            extra_object_list = self.get_page(form, self.qs).object_list
            data = {
                'iTotalRecords': data_page.paginator.count,
                'iTotalDisplayRecords': data_page.paginator.count,
                'sEcho': form.cleaned_data['sEcho'],
                'aaData': self.format_data_rows(data_rows),
            }
        else:
            data_rows = self.get_rows(self.object_list)
            extra_object_list = self.qs
            data = {
                'aaData': self.format_data_rows(data_rows),
            }
        self.add_extra_data(data, extra_object_list)
        return self.json_response(data)

    def json_response(self, data):
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder),
            mimetype=JSON_MIMETYPE
        )
