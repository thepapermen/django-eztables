.. _serverside:

Server-side processing
======================


Django ezTable provide a single view to implement server-side pagination: :class:`eztables.views.DatatablesView`.

It follows the `Django Class-based Views pattern <https://docs.djangoproject.com/en/dev/topics/class-based-views/>`_ and can render Array-based or Object-based JSON.

As it extends :class:`django.views.generic.list.MultipleObjectMixin` it expects the ``model`` attribute to be set in both case.

Both modes expect a ``fields`` attribute that can optionnaly contains format patterns.

The example will use the same models as the demo:

.. code-block:: python

    from django.db import models


    class Engine(models.Model):
        name = models.CharField(max_length=128)
        version = models.CharField(max_length=8, blank=True)
        css_grade = models.CharField(max_length=3)

        def __unicode__(self):
            return '%s %s (%s)' % (self.name, self.version or '-', self.css_grade)


    class Browser(models.Model):
        name = models.CharField(max_length=128)
        platform = models.CharField(max_length=128)
        version = models.CharField(max_length=8, blank=True)
        engine = models.ForeignKey(Engine)

        def __unicode__(self):
            return '%s %s' % (self.name, self.version or '-')


Array-based JSON
----------------

To render an array-based JSON, you must provide ``fields`` as a  ``list`` or a ``tuple`` containing the field names.

.. code-block:: python

    from eztables.views import DatatablesView
    from myapp.models import Browser

    class BrowserDatatablesView(DatatablesView):
        model = Browser
        fields = (
            'engine__name',
            'name',
            'platform',
            'engine__version',
            'engine__css_grade',
        )


You can simply instantiate your datatable with:

.. code-block:: javascript

    $(function(){
        $('#browser-table').dataTable({
            "bPaginate": true,
            "sPaginationType": "bootstrap",
            "bProcessing": true,
            "bServerSide": true,
            "sAjaxSource": Django.url('dt-browsers-default')
        });
    });


Object-based JSON
-----------------

To render an array-based JSON, you must provide ``fields`` as a ``dict`` containing the mapping between the JSON fields names and the model fields.

.. code-block:: python

    from eztables.views import DatatablesView
    from myapp.models import Browser

    class ObjectBrowserDatatablesView(DatatablesView):
        model = Browser
        fields = {
            'name': 'name',
            'engine': 'engine__name',
            'platform': 'platform',
            'engine_version': 'engine__version',
            'css_grade': 'engine__css_grade',
        }


You need to use the ``aoColumns`` properties in the DataTables initialization:

.. code-block:: javascript

    $(function(){
        $('#browser-table').dataTable({
            "bPaginate": true,
            "sPaginationType": "bootstrap",
            "bProcessing": true,
            "bServerSide": true,
            "sAjaxSource": Django.url('dt-browsers-objects'),
            "aoColumns": [
                { "mData": "engine" },
                { "mData": "name" },
                { "mData": "platform" },
                { "mData": "engine_version" },
                { "mData": "css_grade" }
            ]
        });
    });


Formatting
----------

There are two main ways to format the data:

Format patterns
~~~~~~~~~~~~~~~

You can optionally provide some format patterns in the field definition:

.. code-block:: python

    from eztables.views import DatatablesView
    from myapp.models import Browser

    class FormattedBrowserDatatablesView(DatatablesView):
        model = Browser
        fields = (
            'engine__name',
            '{name} {version}',
            'platform',
            'engine__version',
            'engine__css_grade',
        )

    class FormattedObjectBrowserDatatablesView(DatatablesView):
        model = Browser
        fields = {
            'name': '{name} {version}',
            'engine': 'engine__name',
            'platform': 'platform',
            'engine_version': 'engine__version',
            'css_grade': 'engine__css_grade',
        }

Format functions
~~~~~~~~~~~~~~~~

You can define your own format function (class method) in your DataTablesView
class.  By default, Django ezTables will look for one of the following function
and call it, if it exists:

.. code-block:: python

    def format_data_rows(self, rows)
    def format_data_row(self, row)

The first method reads a list of table rows (which will be in ``tuple`` or
``dict`` format, depending on your ``fields`` format) and should return a
formatted list of table rows.  The second method is called for every row of the
data and should return a formatted table row.


Custom sort
-----------

You can implement a custom sort method.
It have to be named ``sort_col_X`` where ``X`` should be the index given by the datatables request (correspond to the filtered column).

It takes the requested direction (``''`` or ``'-'``) as a parameter and should return one or more `Django order statement <https://docs.djangoproject.com/en/dev/ref/models/querysets/#order-by>`_.

.. code-block:: python

    class CustomSortBrowserDatatablesView(BrowserDatatablesView):

        def sort_col_1(self, direction):
            '''Sort on version instead of name'''
            return '%sversion' % direction

        def sort_col_2(self, direction):
            '''Sort on name and platform instead of platform'''
            return ('%sname' % direction, '%splatform' % direction)

Custom Column search
--------------------

You can implement a custom column search method.
It has to be named ``search_col_X`` where ``X`` should be the index given by the datatables request (correspond to the filtered column).

It takes the search term and the queryset to filter as a parameter and should return the filtered queryset.

.. code-block:: python

    class CustomSearchBrowserDatatablesView(BrowserDatatablesView):

        def search_col_1(self, search, queryset):
            '''Search on version instead of name'''
            return queryset.filter(version__icontains=search)

Custom filters
--------------

The user can add his/her own filter classes in the ``filters`` field of the
DatatablesView class or define one or more ``filter_*`` methods in this class.
The latter way is similar to the custom sorting approach.

The former way is a bit more flexible and can integrate with the popular
`django-filter <https://github.com/alex/django-filter>`_ plugin. More
specifically, filters added in the `filters` field must have one of the
following formats:

* List format: [filter1, filter2, filter3]
    Note that this format requires that the filters have a `name`
    attribute and a `filter` method.

    .. code-block:: python

        class Filter(object):
            name = "platform"
            def filter(self, search, queryset)
                return queryset.filter(platform__icontaints=search)
        filter_platform = Filter()

        class BrowserDatatablesView(DatatablesView):
            model = Browser
            fields = (
                'engine__name',
                'name',
                'platform',
                'engine__version',
                'engine__css_grade',
            )
            filters = [filter_platform]

* Dict format: {'name1': filter1, 'name2': filter2, 'name3': filter3}
    Note that this format requires that the filters have a `filter`
    method.

    .. code-block:: python

        class Filter(object):
            def filter(self, search, queryset)
                return queryset.filter(platform__icontaints=search)
        filter_platform = Filter()

        class BrowserDatatablesView(DatatablesView):
            model = Browser
            fields = (
                'engine__name',
                'name',
                'platform',
                'engine__version',
                'engine__css_grade',
            )
            filters = {'platform': filter_platform}

* Django-filter FilterSet format: Simply a FilterSet class

    .. code-block:: python

        import django_filters

        class BrowserFilterSet(django_filters.FilterSet)
            class Meta:
                model = Browser
                fields = ('platform')

        class BrowserDatatablesView(DatatablesView):
            model = Browser
            fields = (
                'engine__name',
                'name',
                'platform',
                'engine__version',
                'engine__css_grade',
            )
            filters = BrowserFilterSet

In order to trigger a filter, its name must match the asterisk part of a
Datatables "sSearch_*" argument. The value of this argument will be
considered as the query for this filter.

Also, note that all list/dict filters should take as an argument a query and a
queryset and return a filtered queryset.

Extra data
----------

This optional feature allows the user to extract extra data for each table row,
without showing them on the table. Extra data can come in handy when you want
to provide more context/info for each table row, but you don't want to show it
as a main column.

In order to extract extra data for each row, you must define the following
function in your DataTablesView class:

    .. code-block:: python

        def get_extra_data_row(self, instance)

This function will receive a model instance as its only argument. The user can
use this instance to extract more info from it, e.g. fields such as dates,
which are typically large for a table column. The returned info for each row
can be arbitrary, since it's not handled by either DataTables or Django
ezTables, but from the client-side code. The only thing that Django ezTables
will do is add in the standard DataTables JSON response an ``extra`` list,
which will have the produced info for each table row.

SQLite Warnings
---------------

Be carefull some field types are not compatible with regex search on SQLite and will be ignored (filtering will no performed on this fields).

Ignored fields type are:

- BigIntegerField
- BooleanField
- DecimalField
- FloatField
- IntegerField
- NullBooleanField
- PositiveIntegerField
- PositiveSmallIntegerField
- SmallIntegerField
