top = '.'
out = 'build'

VERSION = '0.8.0'

import os.path as osp

def options(opt):
    opt.load('compiler_cxx')

def configure(conf):
    conf.load('compiler_cxx')

    conf.env.CXXFLAGS += "-Wall -ansi -pedantic -O2".split()
    conf.env.CXXFLAGS += ['-DASH_VERSION="%s"' % VERSION]
    conf.check_cc(lib='sqlite3', uselib_store='sqlite3', mandatory=True)

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
        etcdir = osp.join(bld.env.PREFIX,'etc/advanced-shell-history')
        bindir = osp.join(bld.env.PREFIX,'bin')
        text = text.replace('/etc/ash', etcdir)
        text = text.replace('/usr/lib/advanced_shell_history', etcdir)
        text = text.replace('/usr/local/bin', bindir)
        text = text.replace('exit 1','return 1') # don't kill shell on sourcing!
        text = text.replace('_ash_log','ash-log')
        tgt.write(text)

    bld(rule=replace_prefix,
        source="man/_ash_log.1", target='man1/ash-log.1')
    bld(rule=replace_prefix,
        source="man/ash_query.1", target='man1/ash-query.1')
    bld.install_files('${PREFIX}/man1',['man1/ash-log.1','man1/ash-query.1'])

    etcfiles = []
    for fname in ['ash.conf', 'queries']:
        tgt = osp.join('etc', fname)
        etcfiles.append(tgt)
        bld(rule = replace_prefix,
            source = osp.join("files/etc/ash", fname),
            target = tgt)
        
    for fname in ['bash', 'zsh', 'common']:
        tgt = osp.join('etc', fname)
        etcfiles.append(tgt)
        bld(rule = replace_prefix,
            source = osp.join("files/usr/lib/advanced_shell_history", fname),
            target = tgt)

    bld.install_files('${PREFIX}/etc/advanced-shell-history',
                      etcfiles)
