top = '.'
out = 'build'

VERSION = '0.8.0'

import os.path as osp

def options(opt):
    opt.load('compiler_cxx')
    opt.add_option('--user', action='store_true', default=False,
                   help='Install into user directory.')
    opt.add_option('--with-sqlite', type='string', 
                   help='Give sqlite3 installation location.')

def configure(conf):
    conf.load('compiler_cxx')

    conf.env.CXXFLAGS += "-Wall -ansi -pedantic -O2".split()
    conf.env.CXXFLAGS += ['-DASH_VERSION="%s"' % VERSION]

    sqlite = conf.options.with_sqlite
    if sqlite:
        conf.env.INCLUDES_sqlite3 = [ osp.join(sqlite,'include') ]
        conf.env.LIBPATH_sqlite3 = [ osp.join(sqlite,'lib') ]
    conf.check_cc(lib='sqlite3', uselib_store='sqlite3', mandatory=True)

    conf.env.BINDIR = osp.join(conf.env.PREFIX,'bin')
    conf.env.MANDIR = osp.join(conf.env.PREFIX,'man')
    conf.env.ETCDIR = osp.join(conf.env.PREFIX,'etc/advanced-shell-history')
    if conf.options.user:
        conf.env.ETCDIR = osp.join(conf.env.PREFIX,'.ash')


def build(bld):
    ash_lsrc = ['command', 'config', 'database', 'flags',
                'logger', 'session', 'unix', 'util']
    ash_qsrc = ash_lsrc + ['formatter', 'queries']

    bld.objects(source=["src/%s.cpp"%s for s in ash_lsrc], target='ash_lobj')
    bld.objects(source=["src/%s.cpp"%s for s in ash_qsrc], target='ash_qobj')

    bld.program(source='src/_ash_log.cpp', target='ash-log',
                use='ash_lobj sqlite3')
    bld.program(source='src/ash_query.cpp', target='ash-query',
                use='ash_qobj sqlite3')
        


    # fix up the man pages.  fixme: just edit them to use a token.
    # also, get destdir working.
    def replace_prefix(task):
        src = task.inputs[0]
        tgt = task.outputs[0]
        text = src.read()
        for thing in ['ETCDIR','BINDIR']:
            text = text.replace(thing, getattr(bld.env, thing))
        tgt.write(text)

    bld(rule=replace_prefix,
        source="man/_ash_log.1", target='man1/ash-log.1')
    bld(rule=replace_prefix,
        source="man/ash_query.1", target='man1/ash-query.1')
    bld.install_files('${MANDIR}/man1',['man1/ash-log.1','man1/ash-query.1'])

    etcfiles = []
    etcpath = 'files/usr/local/etc/advanced-shell-history'
    for fname in ['config', 'queries']:
        tgt = osp.join('etc', fname)
        etcfiles.append(tgt)
        bld(rule = replace_prefix,
            source = osp.join(etcpath, fname),
            target = tgt)

    shpath = 'files/usr/local/lib/advanced_shell_history/sh/'
    for fname in ['bash', 'zsh', 'common']:
        tgt = osp.join('etc', fname)
        etcfiles.append(tgt)
        bld(rule = replace_prefix,
            source = osp.join(shpath, fname),
            target = tgt)

    bld.install_files('${ETCDIR}', etcfiles)
