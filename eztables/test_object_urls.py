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
)
