#!/usr/bin/env python

 # Copyright, license and disclaimer are at the end of this file.

# This is an enhanced version of the recipe posted earlier at
# <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/546532>
'''
   This script %(argv0)s is a postprocessor for PyChecker, the Python
   source code checker available at 'http://pychecker.sourceforge.net'.

   Usage: %(argv0)s [-no-OKd|-no] [-Cmd|-cmd <path>] [-Debug|-debug] [--] [opts] file.py ...

   where 'opts' are PyChecker options and 'file.py' and any following
   command line arguments are Python source file names.

   First, PyChecker is run on the 'file.py' and subsequent arguments
   using command %(cmd)r.  The output from PyChecker is split into
   two sets of warning messages, OK'd and regular warning messages.

   A warning message is considered OK'd if the Python source line
   causing the warning message ends with a comment  #PYCHOK ... or
   #PYCHECKER ... string*).

   OK'd warning messages can be suppressed entirely by using option
   -no-OKd or -no.

   Make sure that %(cmd)r is in your search PATH or specify the
   path to PyChecker with option -Cmd or -cmd or adjust the source
   code of this file %(argv0)s.

   Option -Debug or -debug produces additional output from %(argv0)s.

   Beware of potential overlap between these and PyChecker option
   names and abbreviations.  PyChecker options --debug and --quiet
   are honored.

   Tested with PyChecker 0.8.17 using Python 2.3.4, 2.4.4 or 2.5.1 on
   RHEL 3u7, CentOS 4.6, MacOS X Tiger (Intel) and Solaris 10.

---
*) Both #PYCHOK and #PYCHECKER are all upper case and there must be
   at least one space between #PYCHOK or #PYCHECKER and the end of
   the Python source line.
'''

__version__ = '2.7 (Oct 26, 2008)'

import os, sys

def _printf(fmt, *args, **kwds):
    '''Formatted print.
    '''
    if kwds:  # either ...
        print(fmt % kwds)
    elif args:  # ... or
        print(fmt % args)
    else:
        print(fmt)

class Processor(object):
    '''Processor to handle suppression of OK'd PyChecker
       warning messages, marked as such in source code.
    '''
    _name = ''  # source file name
    _code = []  # source code lines
    _dirs = ()  # source file directories
    _dbg  = False  # debug print
    _out  = True  # not--quiet
    _OKd  = True  # print OK'd warnings

    OKs   = ('#PYCHOK ', '#PYCHECKER ')  # source markers

    def __init__(self, OKd=True, dbg=False):
        self._OKd = OKd
        self._dbg = dbg

    def debugf(self, fmt, *args):
        '''Debug print.
        '''
        if self._dbg:
            _printf('Debug: %s ' + fmt, sys.argv[0], *args)

    def printf(self, fmt, *args):
        '''Quiet print.
        '''
        if self._out:
            _printf(fmt, *args)

    def dirs(self, *args):
        '''Get all source directories.
        '''
        ds = []
        for f in args:
            if f.startswith('-'):
                 # some PyChecker options
                if f in ('--quiet', '-Q'):
                   self._out = False
                elif f in ('--debug', '-d'):
                   self._dbg = True
            else:
                n = max(f.count(os.path.sep), 1)
                d = os.path.realpath(f)
                while d and n > 0:
                    n -= 1
                    d  = os.path.dirname(d)
                    if d and d not in ds:
                        ds.append(d)
        ds.append('.')
        for d in sys.path:
            if os.path.isdir(d) and d not in ds:
                ds.append(d)
        self._dirs = tuple(ds)

    def get(self, name):
        '''Get source code for given file.
        '''
        self._code = []
        self._name = name
        if name.endswith('.py'):
            self.debugf('looking for file: %s', name)
            if os.path.isabs(name):
                ##assert(os.path.join('', name) == name)
                ds = ('',)
            else:
                ds = self._dirs
            for d in ds:  # find file
                try:
                    t = os.path.join(d, name)
                    f = open(t, 'r')
                    s = f.readlines()
                    f.close()
                    self.debugf('found file: %s (%s lines)', t, len(s))
                    self._code = s
                    break
                except (IOError, OSError, EOFError):
                    pass
            else:
                self.debugf('file not found: %s', name)

    def isOK(self, name, line):
        '''Check whether source line is marked.
        '''
        if name != self._name:
            self.get(name)
        try:  # get source line
            s = self._code[int(line) - 1]
            for OK in self.OKs:
                p = s.find(OK)
                if p > 0:  # line OK'd
                    return s[p:].rstrip()
        except (ValueError, IndexError):
            self.debugf('no line %s in file: %s', line, self._name)
        return ''  # not OK'd, not found, etc.

    def run(self, cmd, *args):
        '''Run PyChecker on args and return output.
        '''
        self.dirs(*args)

         # build cmd, run it and capture output
        c = cmd + ' ' + ' '.join(args)
        self.debugf('running %r ...', c)
        m = os.popen(c, 'r').readlines()
        self.debugf('%s lines of %r output', len(m), cmd)
        return m  # output as lines

    def process(self, output):
        '''Split PyChecker output in OK'd
           and other warning messages.
        '''
        if self._OKd:
            self.printf('Splitting ...')
        if self._dbg:
            self.debugf('source directories ...')
            for t in enumerate(self._dirs):
                _printf('%5d: %r', *t)

        mt = []  # list of 2-tuples (message, OK'd)
        n = t = 0  # number of warnings, not OK'd and total
        for m in output:  # process each output line
            m = m.rstrip()
            if m:  # only non-blank lines
                s, ok =  m.split(':', 2), ''
                if len(s) > 2:  # file name, line number, rest
                    t += 1  # total warnings
                    ok = self.isOK(s[0], s[1])
                    if not ok:
                        n += 1  # non-OK'd warnings
                mt.append((m, ok))

        if self._OKd:  # print OK'd warnings
            self.printf('')
            self.printf("Lines OK'd ...")
            m = [m + ' - ' + ok for m, ok in mt if ok] 
            if m:
                _printf(os.linesep.join(m))
            else:
                self.printf('None')

        m = [m for m, ok in mt if not ok] 
        if m:  # print other warnings (and lines)
            self.printf('')
            _printf(os.linesep.join(m))
            if t > 0 and n == 0:
                self.printf("All %s OK'd", t)

        self.printf('')
        return n  # number of non-OK'd warnings


if __name__ == '__main__':

    OKd, dbg = True, False
    cmd = 'pychecker --limit 0'  # XXX for PyChecker 0.8.17

      # no os.EX_... in Python 2.2
    def _usage(x=getattr(os, 'EX_USAGE', 64), cmd='pychecker'):
        '''Show usage.
        '''
        _printf(__doc__, **{'argv0': sys.argv[0], 'cmd': cmd.split()[0]})
        sys.exit(x)

    if len(sys.argv) < 2:
        _usage(cmd=cmd)

     # get options, avoid conflicts
     # with 'pychecker' options
    a = 0
    while True:
        a += 1
        t  = sys.argv[a]
        if not t.startswith('-'):
            break
        elif t in ('-help', '-h'):
            _usage(0, cmd=cmd)
        elif t in ('-no-OKd', '-no'):
            OKd = False
        elif t in ('-Debug', '-debug'):
            dbg = True
        elif t in ('-Cmd', '-cmd'):
            a += 1
            cmd = sys.argv[a]
        else:
            if t in ('--', '---'):
                a += 1
            break

     # get processor, run PyChecker on all
     # remaining args and split the output
    p = Processor(OKd, dbg)
    w = p.run(cmd, *sys.argv[a:])
    if p.process(w):
         # no os.EX_... in Python 2.2
        sys.exit(getattr(os, 'EX_DATAERR', 65))


# License file from an earlier version of this source file follows:

#---------------------------------------------------------------------
#       Copyright (c) 2002-2008 -- ProphICy Semiconductor, Inc.
#                        All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
# 
# - Neither the name of ProphICy Semiconductor, Inc. nor the names
#   of its contributors may be used to endorse or promote products
#   derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
#---------------------------------------------------------------------

