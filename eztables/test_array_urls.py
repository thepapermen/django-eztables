from django.conf.urls import patterns, url

from eztables.demo.views import (
    BrowserDatatablesView,
    FormattedBrowserDatatablesView,
    CustomBrowserDatatablesView,
    SpecialCaseDatatablesView,
)
from eztables.tests import (
    ExtraBrowserDatatablesViewAll,
    ExtraBrowserDatatablesViewRow,
    UserFormatRowBrowserDatatablesView,
    FilterFunctionBrowserDatatablesView,
    FilterListBrowserDatatablesView,
    FilterDictBrowserDatatablesView,
    FilterSetBrowserDatatablesView,
)


urlpatterns = patterns('',
    url(r'^$', BrowserDatatablesView.as_view(), name='browsers'),
    url(r'^formatted/$', FormattedBrowserDatatablesView.as_view(), name='formatted-browsers'),
    url(r'^custom/$', CustomBrowserDatatablesView.as_view(), name='custom-browsers'),
    url(r'^special/$', SpecialCaseDatatablesView.as_view(), name='special'),
    url(r'^extra/$', ExtraBrowserDatatablesViewAll.as_view(), name='extra'),
    url(r'^extra_row/$', ExtraBrowserDatatablesViewRow.as_view(),
        name='extra_row'),
    url(r'^format_row/$', UserFormatRowBrowserDatatablesView.as_view(),
        name='format_row'),
    url(r'^filter_function/$', FilterFunctionBrowserDatatablesView.as_view(),
        name='filter_function'),
    url(r'^filter_list/$', FilterListBrowserDatatablesView.as_view(),
        name='filter_list'),
    url(r'^filter_dict/$', FilterDictBrowserDatatablesView.as_view(),
        name='filter_dict'),
    url(r'^filter_set/$', FilterSetBrowserDatatablesView.as_view(),
        name='filter_set'),
)
