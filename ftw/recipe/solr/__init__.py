# -*- coding: utf-8 -*-
from fnmatch import fnmatch
from ftw.recipe.solr.defaults import DEFAULT_OPTIONS
from jinja2 import Environment, PackageLoader
from setuptools import archive_util
from zc.buildout.download import Download
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile
import os
import shutil
import tempfile


class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options

        for k, v in DEFAULT_OPTIONS.items():
            options.setdefault(k, v)

        options.setdefault('destination', os.path.join(
            buildout['buildout']['parts-directory'], self.name))

        options.setdefault('var-dir', os.path.join(
            buildout['buildout']['directory'], 'var', self.name))

        options.setdefault('log-dir', os.path.join(
            buildout['buildout']['directory'], 'var', 'log', self.name))

        options.setdefault('bin-dir', os.path.join(
            buildout['buildout']['directory'], 'bin'))

        self.cores = options.get('cores', '').split()

        self.solr_version = options['solr-url'].split('/')[-1][5:][:-4]
        self.solr_major_version = self.solr_version.split('.')[0]

        self.is_solrcloud = True if (options['zk-host'] or
                                     options['zk-run'] == 'true') else False

        options.setdefault('pid-file', os.path.join(options['var-dir'],
                           '{}.pid'.format(name)))
        options.setdefault('jvm-opts', '')

        options.setdefault('conf-source', os.path.join(
            os.path.dirname(__file__), 'conf', self.solr_major_version))

        self.env = Environment(
            loader=PackageLoader('ftw.recipe.solr', 'templates'),
            trim_blocks=True,
        )

    def download_and_extract(self, url, md5sum, dest, extract_filter, strip_dirs=1):
        path, is_temp = Download(self.buildout['buildout'])(url, md5sum)
        files = []

        def progress_filter(src, dst):
            if fnmatch(src, extract_filter):
                files.append(os.path.join(dest, os.path.join(
                    *os.path.normpath(src).split(os.sep)[strip_dirs:])))
                return files[-1]

        archive_util.unpack_archive(path, dest, progress_filter)
        return files

    def install(self):
        parts = []

        destination = self._create_dir(self.options.get('destination'), parts)

        # Download and extract Solr Undertow
        self.download_and_extract(
            self.options['undertow-url'],
            self.options['undertow-md5sum'],
            os.path.join(destination, 'lib'),
            '*/lib/*',
            strip_dirs=2
        )
        parts.append(os.path.join(destination, 'lib'))

        # Download Solr distribution and create WAR file
        tempdir = tempfile.mkdtemp()
        parts.extend(self.download_and_extract(
            self.options['solr-url'],
            self.options['solr-md5sum'],
            tempdir,
            '*/server/solr-webapp/webapp/*',
            strip_dirs=4
        ))
        with ZipFile(os.path.join(destination, 'solr.war'), 'w',
                     ZIP_DEFLATED) as solr_war:
            for dirpath, dirnames, filenames in os.walk(tempdir):
                for filename in filenames:
                    solr_war.write(
                        os.path.join(dirpath, filename),
                        os.path.join(os.path.relpath(dirpath, tempdir),
                                     filename))
        shutil.rmtree(tempdir)

        # Create Solr data directories
        var_dir = self._create_dir(self.options.get('var-dir'))
        home_dir = self._create_dir(os.path.join(var_dir, 'home'))
        tmp_dir = self._create_dir(os.path.join(var_dir, 'tmp'))
        log_dir = self._create_dir(self.options.get('log-dir'))

        # Create solr.xml
        parts.append(self._create_from_template(
            'solr.xml.tmpl',
            os.path.join(home_dir, 'solr.xml'),
            port=self.options['port'],
            host_context=self.options['host_context'],
        ))

        # Create zoo.cfg
        parts.append(self._create_from_template(
            'zoo.cfg.tmpl',
            os.path.join(home_dir, 'zoo.cfg'),
            zk_data_dir=os.path.join(var_dir, 'zoo_data'),
            zk_port=self.options['zk-port']
        ))

        # Create undertow.conf
        parts.append(self._create_from_template(
            'undertow.conf.tmpl',
            os.path.join(destination, 'undertow.conf'),
            zk_run=self.options['zk-run'],
            zk_host=self.options['zk-host'],
            http_cluster_port=self.options['port'],
            solr_home=home_dir,
            solr_logs=log_dir,
            temp_dir=tmp_dir,
            solr_version=self.solr_version,
            solr_war_file=os.path.join(destination, 'solr.war')
        ))

        # Create cores
        for core in self.cores:
            core_dir = os.path.join(home_dir, core)
            if not os.path.isdir(core_dir):
                os.makedirs(core_dir)

            self._create_from_template(
                'core.properties.tmpl',
                os.path.join(core_dir, 'core.properties'),
                name=core,
            )

            core_conf_dir = os.path.join(core_dir, 'conf')
            if not os.path.isdir(core_conf_dir):
                os.makedirs(core_conf_dir)

            parts.append(self._create_from_template(
                'solrconfig.xml.tmpl',
                os.path.join(core_conf_dir, 'solrconfig.xml'),
                lucene_match_version=self.solr_version,
            ))

            if not os.path.exists(os.path.join(core_conf_dir,
                                               'managed-schema')):
                self._create_from_template(
                    'managed-schema.tmpl',
                    os.path.join(core_conf_dir, 'managed-schema'),
                    unique_key=self.options['unique-key'],
                )

        # Create startup script
        bin_dir = self.options['bin-dir']
        startup_script = os.path.join(bin_dir, self.name)
        parts.append(self._create_from_template(
            'startup.tmpl',
            startup_script,
            solr_jar_path=os.path.join(destination, 'lib'),
            undertow_conf=os.path.join(destination, 'undertow.conf'),
            pid_file=self.options['pid-file'],
            jvm_opts=self.options['jvm-opts'],
        ))
        os.chmod(startup_script, 0755)

        return parts

    def update(self):
        pass

    def _core_option(self, core, option, default=None):
        """Retrieve an option for a core from a subpart falling back to the
           main part."""
        core_part_name = "{}_{}".format(self.name, core)
        if core_part_name in self.buildout:
            if option in self.buildout[core_part_name]:
                return self.buildout[core_part_name][option]
        return self.options.get(option, default)

    def _create_dir(self, path, parts=None):
        if not os.path.isdir(path):
            os.makedirs(path)
            if parts:
                parts.append(path)
        return path

    def _create_from_template(self, template, filename, **kwargs):
        tmpl = self.env.get_template(template)
        with open(filename, 'wb') as f:
            f.write(tmpl.render(**kwargs).encode('utf8'))
        return filename
