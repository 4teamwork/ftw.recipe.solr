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
    ...
    ... [versions]
    ... setuptools = <45.0
    ... Jinja2 = <3.0.0
    ... MarkupSafe = <2.0.0
    ... """.format(server_url=server_url))

Running the buildout gives us::

    >>> print system(buildout)
    Getting distribution for 'zc.recipe.egg>=2.0.6'.
    Got zc.recipe.egg ...
    Installing solr.
    Downloading http://test.server/solr-7.2.1.tgz
    WARNING: The easy_install command is deprecated and will be removed in a future version.
    <BLANKLINE>

We should have a Solr distribution in the parts directory::

    >>> ls(sample_buildout, 'parts', 'solr')
    d contrib
    d dist
    -  log4j2.xml
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

Our custom log4j2.xml file should configure a log file in var/log::

    >>> cat(sample_buildout, 'parts', 'solr', 'log4j2.xml')
    <?xml version="1.0" encoding="UTF-8"?>
    <!--
      Licensed to the Apache Software Foundation (ASF) under one or more
      contributor license agreements.  See the NOTICE file distributed with
      this work for additional information regarding copyright ownership.
      The ASF licenses this file to You under the Apache License, Version 2.0
      (the "License"); you may not use this file except in compliance with
      the License.  You may obtain a copy of the License at
    <BLANKLINE>
          http://www.apache.org/licenses/LICENSE-2.0
    <BLANKLINE>
      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
      See the License for the specific language governing permissions and
      limitations under the License.
      -->
    <BLANKLINE>
    <!-- Configuration for asynchronous logging -->
    <Configuration>
      <Appenders>
    <BLANKLINE>
        <Console name="STDOUT" target="SYSTEM_OUT">
          <PatternLayout>
            <Pattern>
              %maxLen{%d{yyyy-MM-dd HH:mm:ss.SSS} %-5p (%t) [%X{collection} %X{shard} %X{replica} %X{core}] %c{1.} %m%notEmpty{ =>%ex{short}}}{10240}%n
            </Pattern>
          </PatternLayout>
        </Console>
    <BLANKLINE>
        <RollingRandomAccessFile
            name="MainLogFile"
            fileName="/sample-buildout/var/log/solr.log"
            filePattern="/sample-buildout/var/log/solr.log.%i" >
          <PatternLayout>
            <Pattern>
              %maxLen{%d{yyyy-MM-dd HH:mm:ss.SSS} %-5p (%t) [%X{collection} %X{shard} %X{replica} %X{core}] %c{1.} %m%notEmpty{ =>%ex{short}}}{10240}%n
            </Pattern>
          </PatternLayout>
          <Policies>
            <OnStartupTriggeringPolicy />
            <SizeBasedTriggeringPolicy size="50 MB"/>
          </Policies>
          <DefaultRolloverStrategy max="4"/>
        </RollingRandomAccessFile>
    <BLANKLINE>
        <RollingRandomAccessFile
            name="SlowLogFile"
            fileName="/sample-buildout/var/log/solr_slow_requests.log"
            filePattern="/sample-buildout/var/log/solr_slow_requests.log.%i" >
          <PatternLayout>
            <Pattern>
              %maxLen{%d{yyyy-MM-dd HH:mm:ss.SSS} %-5p (%t) [%X{collection} %X{shard} %X{replica} %X{core}] %c{1.} %m%notEmpty{ =>%ex{short}}}{10240}%n
            </Pattern>
          </PatternLayout>
          <Policies>
            <OnStartupTriggeringPolicy />
            <SizeBasedTriggeringPolicy size="50 MB"/>
          </Policies>
          <DefaultRolloverStrategy max="4"/>
        </RollingRandomAccessFile>
    <BLANKLINE>
      </Appenders>
      <Loggers>
        <AsyncLogger name="org.apache.hadoop" level="warn"/>
        <AsyncLogger name="org.apache.solr.update.LoggingInfoStream" level="off"/>
        <AsyncLogger name="org.apache.zookeeper" level="warn"/>
        <AsyncLogger name="org.apache.solr.core.SolrCore.SlowRequest" level="info" additivity="false">
          <AppenderRef ref="SlowLogFile"/>
        </AsyncLogger>
    <BLANKLINE>
        <AsyncRoot level="info">
          <AppenderRef ref="MainLogFile"/>
          <AppenderRef ref="STDOUT"/>
        </AsyncRoot>
      </Loggers>
    </Configuration>


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
    PID_FILE=${PID_FILE:="/sample-buildout/var/solr/solr.pid"}
    <BLANKLINE>
    SOLR_PORT=${SOLR_PORT:="8983"}
    SOLR_HOME=${SOLR_HOME:="/sample-buildout/var/solr"}
    SOLR_INSTALL_DIR=${SOLR_INSTALL_DIR:="/sample-buildout/parts/solr"}
    SOLR_SERVER_DIR=${SOLR_SERVER_DIR:="/sample-buildout/parts/solr/server"}
    <BLANKLINE>
    SOLR_START_OPT=('-server' \
    "${JVM_OPTS[@]}" \
    -Djetty.host=localhost
    -Djetty.port=$SOLR_PORT \
    -Djetty.home=$SOLR_SERVER_DIR \
    -Dsolr.solr.home=$SOLR_HOME \
    -Dsolr.install.dir=$SOLR_INSTALL_DIR \
    -Dsolr.log.dir=/sample-buildout/var/log \
    -Dlog4j2.formatMsgNoLookups=true \
    -Dlog4j2.configurationFile=/sample-buildout/parts/solr/log4j2.xml)
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
            ps -p $pid -f | grep start.jar > /dev/null 2>&1
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
            ps -p $pid -f | grep start.jar > /dev/null 2>&1
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
    ...
    ... [versions]
    ... setuptools = <45.0
    ... Jinja2 = <3.0.0
    ... MarkupSafe = <2.0.0
    ... """.format(server_url=server_url))

Running the buildout gives us::

    >>> print system(buildout)
    Uninstalling solr.
    Installing solr.
    Downloading http://test.server/solr-7.2.1.tgz
    <BLANKLINE>

The conf directory should contain our Solr configuration files::

    >>> ls(sample_buildout, 'var', 'solr', 'core1', 'conf')
    - managed-schema
    - mapping-FoldToASCII.txt
    - solrconfig.xml
    - stopwords.txt
    - synonyms.txt


We can provide a shards whitelist::

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
    ... shards-whitelist = localhost:11130/solr/this,localhost:22230/solr/that
    ...
    ... cores = core1
    ...
    ... [versions]
    ... setuptools = <45.0
    ... Jinja2 = <3.0.0
    ... MarkupSafe = <2.0.0
    ... """.format(server_url=server_url))

Running the buildout gives us::

    >>> print system(buildout)
    Uninstalling solr.
    Installing solr.
    Downloading http://test.server/solr-7.2.1.tgz
    <BLANKLINE>

The solr.xml file contains our whitelisted shards::

    >>> cat(sample_buildout, 'var', 'solr', 'solr.xml')
    <solr>
    <BLANKLINE>
      <solrcloud>
    <BLANKLINE>
        <str name="host">${host:}</str>
        <int name="hostPort">${jetty.port:8983}</int>
        <str name="hostContext">${hostContext:solr}</str>
    <BLANKLINE>
        <bool name="genericCoreNodeNames">${genericCoreNodeNames:true}</bool>
    <BLANKLINE>
        <int name="zkClientTimeout">${zkClientTimeout:30000}</int>
        <int name="distribUpdateSoTimeout">${distribUpdateSoTimeout:600000}</int>
        <int name="distribUpdateConnTimeout">${distribUpdateConnTimeout:60000}</int>
        <str name="zkCredentialsProvider">${zkCredentialsProvider:org.apache.solr.common.cloud.DefaultZkCredentialsProvider}</str>
        <str name="zkACLProvider">${zkACLProvider:org.apache.solr.common.cloud.DefaultZkACLProvider}</str>
    <BLANKLINE>
      </solrcloud>
    <BLANKLINE>
      <shardHandlerFactory name="shardHandlerFactory"
        class="HttpShardHandlerFactory">
        <int name="socketTimeout">${socketTimeout:600000}</int>
        <int name="connTimeout">${connTimeout:60000}</int>
        <str name="shardsWhitelist">localhost:11130/solr/this,localhost:22230/solr/that</str>
      </shardHandlerFactory>
    <BLANKLINE>
    </solr>


We can override the solr settings with a configoverlay:

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
    ... configoverlay =
    ...     {{
    ...         "initParams": {{
    ...             "/update/**,/query,/select,/spell": {{
    ...                 "name":"/update/**,/query,/select,/spell",
    ...                 "path":"/update/**,/query,/select,/spell",
    ...                 "defaults": {{
    ...                     "update.chain":"sync.chain",
    ...                     "df":"SearchableText"
    ...                 }}
    ...             }}
    ...         }}
    ...     }}
    ...
    ... cores = core1
    ...
    ... [versions]
    ... setuptools = <45.0
    ... Jinja2 = <3.0.0
    ... MarkupSafe = <2.0.0
    ... """.format(server_url=server_url))

Running the buildout gives us::

    >>> print system(buildout)
    Uninstalling solr.
    Installing solr.
    Downloading http://test.server/solr-7.2.1.tgz
    <BLANKLINE>

The configoverlay.json file contains our configuration::

    >>> cat(sample_buildout, 'var', 'solr', 'core1', 'conf', 'configoverlay.json')
    {
        "initParams": {
            "/update/**,/query,/select,/spell": {
                "name":"/update/**,/query,/select,/spell",
                "path":"/update/**,/query,/select,/spell",
                "defaults": {
                    "update.chain":"sync.chain",
                    "df":"SearchableText"
                }
            }
        }
    }
