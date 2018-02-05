Introduction
============

This recipe installs a `Solr <http://lucene.apache.org/solr/>`_ 
server with buildout.

It's kept as simple as possible and contrary to `collective.recipe.solrinstance`
it does not generate any Solr configuration files. Instead the user can provide
a directory containing custom configuration files. A default set of configuration
files for usage with Plone is provided.

You can use it by adding a part like this::

    [buildout]
    parts = solr

    [solr]
    recipe = ftw.recipe.solr
    cores =
        core1


Supported options
=================

The recipe supports the following options:

host
    Name or IP address of the Solr server. Defaults to ``localhost``.

port
    Server port. Defaults to ``8983``.

cores
    List of cores that should be created.

url
    Url for Solr distribution download.

md5sum
    MD5 checksum of Solr distribution.

jvm-opts
    Can be used to configure JVM options. Defaults to 
    ``-Xms512m -Xmx512m -Xss256k``

conf
    Path to a directory containing Solr configuration files.

conf-egg
    If provided, the path given in `conf` is prepended with the path of the
    given egg.


Links
=====

- Github: https://github.com/4teamwork/ftw.recipe.solr
- Issues: https://github.com/4teamwork/ftw.recipe.solr/issues
- Pypi: http://pypi.python.org/pypi/ftw.recipe.solr
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.recipe.solr


Copyright
=========

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.recipe.solr`` is licensed under GNU General Public License, version 2.