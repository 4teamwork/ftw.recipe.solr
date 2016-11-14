We setup an HTTP server that provides the files we want to download:

    >>> import os.path
    >>> testdata = join(os.path.dirname(__file__), 'testdata')
    >>> server_url = start_server(testdata)
    >>> mkdir(sample_buildout, 'downloads')

We'll start by creating a simple buildout that uses our recipe::

    >>> write(sample_buildout, 'buildout.cfg',
    ... """
    ... [buildout]
    ... parts = solr
    ...
    ... [solr]
    ... recipe = ftw.recipe.solr
    ... undertow-url = {server_url}solr-undertow-1.6.2.tgz
    ... undertow-md5sum = 308d1ed8d7440d672a3b00a1e3e55c3a
    ... solr-url = {server_url}solr-6.3.0.tgz
    ... solr-md5sum = 514e1be58defcd11188826af087ff656
    ...
    ... cores = core1
    ... """.format(server_url=server_url))

Running the buildout gives us::

    >>> print system(buildout)
    Installing solr.
    Downloading http://test.server/solr-undertow-1.6.2.tgz
    Downloading http://test.server/solr-6.3.0.tgz
    <BLANKLINE>

We should have a lib directory, the Solr WAR file and the Undertow configuration
file in our parts directory::

    >>> ls(sample_buildout, 'parts', 'solr')
    d lib
    - solr.war
    - undertow.conf

The Undertow configuration file contains the following settings::

    >>> cat(sample_buildout, 'parts', 'solr', 'undertow.conf')
    solr.undertow: {
      httpClusterPort: 8983
      solrHome: "/sample-buildout/var/solr/home"
      solrLogs: "/sample-buildout/var/log/solr"
      tempDir: "/sample-buildout/var/solr/tmp"
      solrVersion: 6.3.0
      solrWarFile: "/sample-buildout/parts/solr/solr.war"
    }

The lib directory contains the Solr Undertow jar files::

    >>> ls(sample_buildout, 'parts', 'solr', 'lib')
    - solr-undertow-1.6.2.jar
    - undertow-core-1.3.18.Final.jar 

We should also have a Solr home and a tmp directory::

    >>> ls(sample_buildout, 'var', 'solr')
    d home
    d tmp

The home directory should contain a directory for the Solr core and two
configuration files::

    >>> ls(sample_buildout, 'var', 'solr', 'home')
    d core1
    - solr.xml
    - zoo.cfg

The core directory should contain a conf directory and core.properties file::

    >>> ls(sample_buildout, 'var', 'solr', 'home', 'core1')
    d conf
    - core.properties

