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
    -  log4j.properties
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

Our custom log4j.properties file should configure a log file in var/log::

    >>> cat(sample_buildout, 'parts', 'solr', 'log4j.properties')
    # Default Solr log4j config
    # rootLogger log level may be programmatically overridden by -Dsolr.log.level
    log4j.rootLogger=INFO, file, CONSOLE
    <BLANKLINE>
    # Console appender will be programmatically disabled when Solr is started with option -Dsolr.log.muteconsole
    log4j.appender.CONSOLE=org.apache.log4j.ConsoleAppender
    log4j.appender.CONSOLE.layout=org.apache.log4j.EnhancedPatternLayout
    log4j.appender.CONSOLE.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss.SSS} %-5p (%t) [%X{collection} %X{shard} %X{replica} %X{core}] %c{1.} %m%n
    <BLANKLINE>
    #- size rotation with log cleanup.
    log4j.appender.file=org.apache.log4j.RollingFileAppender
    log4j.appender.file.MaxFileSize=50MB
    log4j.appender.file.MaxBackupIndex=4
    <BLANKLINE>
    #- File to log to and log format
    log4j.appender.file.File=/sample-buildout/var/log/solr.log
    log4j.appender.file.layout=org.apache.log4j.EnhancedPatternLayout
    log4j.appender.file.layout.ConversionPattern=%d{yyyy-MM-dd HH:mm:ss.SSS} %-5p (%t) [%X{collection} %X{shard} %X{replica} %X{core}] %c{1.} %m%n
    <BLANKLINE>
    # Adjust logging levels that should differ from root logger
    log4j.logger.org.apache.zookeeper=WARN
    log4j.logger.org.apache.hadoop=WARN
    log4j.logger.org.eclipse.jetty=WARN
    log4j.logger.org.eclipse.jetty.server.Server=INFO
    log4j.logger.org.eclipse.jetty.server.ServerConnector=INFO
    <BLANKLINE>
    # set to INFO to enable infostream log messages
    log4j.logger.org.apache.solr.update.LoggingInfoStream=OFF

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
    <BLANKLINE>
    SOLR_START_OPT=('-server' \
    "${JVM_OPTS[@]}" \
    -Djetty.host=localhost
    -Djetty.port=$SOLR_PORT \
    -Djetty.home=$SOLR_SERVER_DIR \
    -Dsolr.solr.home=$SOLR_HOME \
    -Dsolr.install.dir=$SOLR_INSTALL_DIR \
    -Dsolr.log.dir=/sample-buildout/var/log \
    -Dlog4j.configuration=/sample-buildout/parts/solr/log4j.properties)
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
        exec "$JAVACMD" "${SOLR_START_OPT[@]}" -jar start.jar --module=http
    }
    <BLANKLINE>
    start_console() {
        cd "$SOLR_SERVER_DIR"
        exec "$JAVACMD" "${SOLR_START_OPT[@]}" -Dsolr.log.muteconsole -jar start.jar --module=http
    }
    <BLANKLINE>
    stop() {
        if [ -e $PID_FILE ]; then
            pid=`cat "$PID_FILE"`
            ps -p $pid | grep start.jar > /dev/null 2>&1
            if [ $? -eq 0 ]
            then
                kill -TERM $pid
                rm -f $PID_FILE
                echo "Solr stopped successfully."
            else
                echo "Solr is not running."
            fi
        else
            echo "Solr is not running."
        fi
    }
    <BLANKLINE>
    status() {
        if [ -e $PID_FILE ]; then
            pid=`cat "$PID_FILE"`
            ps -p $pid | grep start.jar > /dev/null 2>&1
            if [ $? -eq 0 ]
            then
                echo "Solr running with pid $pid."
            else
                echo "Solr is not running."
            fi
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
        console)
            start_console
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
        *)
            echo "Usage: `basename "$0"` {start|fg|console|stop|restart|status}" >&2
            exit 1
            ;;
    esac


We can provide the Solr configuration from an egg::

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
    ... conf-egg = ftw.recipe.solr
    ... conf = /ftw/recipe/solr/conf
    ...
    ... cores = core1
    ... """.format(server_url=server_url))

Running the buildout gives us::

    >>> print system(buildout)
    Uninstalling solr.
    Installing solr.
    Downloading http://test.server/solr-7.2.1.tgz
    <BLANKLINE>

The conf direcotry should contain our Solr configuration files::

    >>> ls(sample_buildout, 'var', 'solr', 'core1', 'conf')
    - managed-schema
    - mapping-FoldToASCII.txt
    - solrconfig.xml
    - stopwords.txt
    - synonyms.txt
