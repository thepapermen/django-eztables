Client-side processing
======================

Django ezTables also provides a way for users to grab data from a server, using
the DataTables API, but also defer all processing to the client-side. In order
to do this, the user must still define a DataTables view as in the :ref:`Server-side
processing <serverside>` section, however, he/she must set the DataTables `serverSide
<https://datatables.net/reference/option/serverSide>`_ option to ``false``, or
not set it at all.

**Note:** Users that choose this option can still format and add extra data on
the server side.
