from django.conf.urls import patterns, url

from eztables.demo.views import (
    ObjectBrowserDatatablesView,
    FormattedObjectBrowserDatatablesView,
    CustomObjectBrowserDatatablesView,
    SpecialCaseDatatablesView,
)
from eztables.tests import (
    ExtraObjectBrowserDatatablesViewAll,
    ExtraObjectBrowserDatatablesViewRow,
    UserFormatRowObjectBrowserDatatablesView,
    FilterFunctionObjectBrowserDatatablesView,
    FilterListObjectBrowserDatatablesView,
    FilterDictObjectBrowserDatatablesView,
    FilterSetObjectBrowserDatatablesView,
)

urlpatterns = patterns('',
    url(r'^$', ObjectBrowserDatatablesView.as_view(), name='browsers'),
    url(r'^formatted/$', FormattedObjectBrowserDatatablesView.as_view(), name='formatted-browsers'),
    url(r'^custom/$', CustomObjectBrowserDatatablesView.as_view(), name='custom-browsers'),
    url(r'^special/$', SpecialCaseDatatablesView.as_view(), name='special'),
    url(r'^extra/$', ExtraObjectBrowserDatatablesViewAll.as_view(),
        name='extra'),
    url(r'^extra_row/$', ExtraObjectBrowserDatatablesViewRow.as_view(),
        name='extra_row'),
    url(r'^format_row/$', UserFormatRowObjectBrowserDatatablesView.as_view(),
        name='format_row'),
    url(r'^filter_function/$',
        FilterFunctionObjectBrowserDatatablesView.as_view(),
        name='filter_function'),
    url(r'^filter_list/$', FilterListObjectBrowserDatatablesView.as_view(),
        name='filter_list'),
    url(r'^filter_dict/$', FilterDictObjectBrowserDatatablesView.as_view(),
        name='filter_dict'),
    url(r'^filter_set/$', FilterSetObjectBrowserDatatablesView.as_view(),
        name='filter_set'),
)
