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
    ... index=https://pypi.python.org/simple/
    ...
    ... [solr]
    ... recipe = ftw.recipe.solr
    ... url = {server_url}solr-7.2.1.tgz
    ... md5sum = 95e828f50d34c1b40e3afa8630138664
    ...
    ... cores = core1
    ... """.format(server_url=server_url))

Running the buildout gives us::

    >>> print system(buildout)
    Installing solr.
    Downloading http://test.server/solr-7.2.1.tgz
    <BLANKLINE>

We should have a Solr distribution in the parts directory::

    >>> ls(sample_buildout, 'parts', 'solr')
    d contrib
    d dist
    d server

We should also have a Solr home directory::

    >>> ls(sample_buildout, 'var')
    d log
    d solr

The home directory should contain a directory for the Solr core and two
configuration files::

    >>> ls(sample_buildout, 'var', 'solr')
    d core1
    - solr.xml
    - zoo.cfg

The core directory should contain a conf directory and core.properties file::

    >>> ls(sample_buildout, 'var', 'solr', 'core1')
    d conf
    - core.properties

The conf direcotry should contain a basic set of Solr configuration files::

    >>> ls(sample_buildout, 'var', 'solr', 'core1', 'conf')
    - managed-schema
    - mapping-FoldToASCII.txt
    - solrconfig.xml
    - stopwords.txt
    - synonyms.txt

We should also have a startup script::

    >>> ls(sample_buildout, 'bin')
    - buildout
    - solr

    >>> cat(sample_buildout, 'bin', 'solr')
    #!/usr/bin/env bash
    <BLANKLINE>
    DEFAULT_JVM_OPTS="-Dfile.encoding=UTF-8"
    JVM_OPTS=(${DEFAULT_JVM_OPTS[@]} -Xms512m -Xmx512m -Xss256k)
    <BLANKLINE>
    JAVACMD="java"
    PID_FILE="/sample-buildout/var/solr/solr.pid"
    <BLANKLINE>
    SOLR_PORT="8983"
    SOLR_HOME="/sample-buildout/var/solr"
    SOLR_INSTALL_DIR="/sample-buildout/parts/solr"
    SOLR_SERVER_DIR="/sample-buildout/parts/solr/server"
    SOLR_LOG_DIR="/sample-buildout/var/log/solr"
    <BLANKLINE>
    <BLANKLINE>
    SOLR_START_OPT=('-server' \
    "${JVM_OPTS[@]}" \
    -Djetty.host=localhost
    -Djetty.port=$SOLR_PORT \
    -Djetty.home=$SOLR_SERVER_DIR \
    -Dsolr.solr.home=$SOLR_HOME \
    -Dsolr.log.dir=$SOLR_LOG_DIR \
    -Dsolr.install.dir=$SOLR_INSTALL_DIR)
    <BLANKLINE>
    <BLANKLINE>
    start() {
        cd "$SOLR_SERVER_DIR"
        nohup "$JAVACMD" "${SOLR_START_OPT[@]}" -Dsolr.log.muteconsole -jar start.jar --module=http >/dev/null 2>&1 &
        echo $! > "$PID_FILE"
        pid=`cat "$PID_FILE"`
        echo "Solr started with pid $pid."
    }
    <BLANKLINE>
    start_fg() {
        cd "$SOLR_SERVER_DIR"
        "$JAVACMD" "${SOLR_START_OPT[@]}" -jar start.jar --module=http
    }
    <BLANKLINE>
    stop() {
        pid=`cat "$PID_FILE"`
        kill -TERM $pid
        echo "Solr stopped successfully."
    }
    <BLANKLINE>
    status() {
        pid=`cat "$PID_FILE"`
        if ps -p $pid > /dev/null 2>&1
        then
            echo "Solr running with pid $pid."
        else
            echo "Solr is not running."
        fi
    }
    <BLANKLINE>
    case "$1" in
        start)
            start
            ;;
    <BLANKLINE>
        fg)
            start_fg
            ;;
    <BLANKLINE>
        stop)
            stop
            ;;
    <BLANKLINE>
        restart)
            stop
            start
            ;;
    <BLANKLINE>
        status)
            status
            ;;
    esac
