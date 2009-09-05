#!/usr/bin/env python

 # Copyright, license and disclaimer are at the end of this file.

 # This is an enhanced version of the recipe posted earlier at
 # <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/546532>
'''
   This script %(argv0)s is a postprocessor for PyChecker, the Python
   source code checker available at 'http://pychecker.sourceforge.net'.

   Usage: %(argv0)s  [-no-OKd|-no]  [-debug|-Debug]  [-cmd|-Cmd <path>]
                    [--|---]  [<opts>]  file.py ...

   where <opts> are PyChecker options and  file.py and any following
   command line arguments are Python source file names.

   First, run PyChecker on  file.py and any subsequent arguments using
   command %(cmd)r.  Then, split the output from PyChecker into two
   sets of warning messages, OK'd and regular warning messages.

   A warning message is considered OK'd if the Python source line
   causing the warning message ends with a comment  #PYCHOK ... or
   #PYCHECKER ... string*).

   OK'd warning messages can be suppressed entirely by using option
   -no-OKd or -no.

   Make sure that %(cmd)r is in your search PATH or specify the
   path to PyChecker with option -cmd or -Cmd (or adjust the source
   code of this file %(argv0)s).

   Option -debug or -Debug produces additional %(argv0)s output.

   Beware of potential overlap between these and PyChecker option
   names and abbreviations.  PyChecker options --debug and --quiet
   are honored.

   Tested with PyChecker 0.8.17 using Python 2.3.4, 2.4.4, 2.5.2 or
   2.6 on RHEL 3u7, CentOS 4.6, MacOS X Tiger (Intel) and Solaris 10.

---
*) Both #PYCHOK and #PYCHECKER are all upper case and there must be
   at least one space between #PYCHOK or #PYCHECKER and the end of
   the Python source line.
'''

__version__ = '2.10 (Nov 28, 2008)'
__all__     = ('Processor', 'main')

import os, sys

 # defaults
_argv0 =  sys.argv[0]
_Cmd   = 'pychecker --limit 0'  # PyChecker 0.8.17
_Debug =  False  # print debug info
_OKd   =  True   # print OK'd warnings
_Out   =  sys.stdout  # output file

try:
    from subprocess import Popen, PIPE
     # see <http://docs.python.org/library/subprocess.html#replacing-os-popen>
     # and <http://bugs.python.org/issue4194> for subprocess.Popen vs os.popen
    def _popen(cmd):  # return stdout
        return Popen(cmd, shell=True, bufsize=-1, stdout=PIPE).stdout

except ImportError:  # no subprocess
    def _popen(cmd):  # return stdout
        return os.popen(cmd, 'r')  # bufsize=-1 by default

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
    OKs = ('#PYCHOK ', '#PYCHECKER ')  # source markers

    _code = []  # source code lines
    _dirs = ()  # source file directories
    _name = ''  # source file name

    _debug = _Debug  # print debug output
    _OKd   = _OKd    # print OK'd warnings
    _out   = _Out    # output file, None for quiet

    def __init__(self, OKd=_OKd, debug=_Debug, out=_Out):
        self._debug = debug
        self._OKd   = OKd
        self._out   = out

    def debugf(self, fmt, *args):
        '''Debug print.
        '''
        if self._debug:
            self.printf('Debug: %s ' + fmt, _argv0, *args)

    def dirs(self, *args):
        '''Get all source directories.
        '''
        ds = []
        for f in args:
            if f.startswith('-'):
                 # some PyChecker options
                if f in ('--quiet', '-Q'):
                    pass
                    #self._out = None
                elif f in ('--debug', '-d'):
                    self._debug = True
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
        if name[-3:].lower() == '.py':
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
                    self._code = s
                    self.debugf('found file: %s (%s lines)', t, len(s))
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

    def printf(self, fmt, *args):
        '''Formatted print.
        '''
        if self._out:
            if args:
                t = fmt % args
            else:
                t = fmt
            if t:
                self._out.write(t + os.linesep)

    def process(self, output):
        '''Split PyChecker output in OK'd
           and other warning messages.
        '''
        if self._OKd:
            self.printf('Splitting ...')
        if self._debug:
            self.debugf('source directories ...')
            for t in enumerate(self._dirs):
                self.printf('%5d: %r', *t)

        mt = []  # list of 2-tuples (message, OK'd)
        n = t = 0  # number of warnings, not OK'd and total
        for m in output:  # process each output line
            m = m.rstrip()
            if m:  # only non-blank lines
                ok, s = '', m.split(':', 2)
                if len(s) > 2:  # file name, line number, rest
                    ok = self.isOK(s[0], s[1])
                    if not ok:
                        n += 1  # non-OK'd warnings
                    t += 1  # total warnings
                mt.append((m, ok))

        if self._out:
            self.printf('')
            if self._OKd:  # print OK'd warnings
                self.printf("Lines OK'd ...")
                m = [m + ' - ' + ok for m, ok in mt if ok]
                self.printf(os.linesep.join(m) or 'None')
                self.printf('')
             # print other warnings (and lines)
            m = [m for m, ok in mt if not ok]
            self.printf(os.linesep.join(m))
            if t > 0 and n == 0 and self._OKd:
                self.printf("All %s OK'd", t)
            self.printf('')

        return n  # number of non-OK'd warnings

    def run(self, cmd, *args):
        '''Run PyChecker on args and return output.
        '''
        self.dirs(*args)

         # build cmd, run it and capture output
        c = cmd + ' ' + ' '.join(args)
        self.debugf('running %r ...', c)
        m = _popen(c).readlines()
        self.debugf('%s lines of %r output', len(m), cmd)
        return m  # output as lines

def main(args, OKd=_OKd, debug=_Debug, cmd=_Cmd, out=_Out):
    '''Get a postprocessor, run PyChecker on the
       given arguments, split the output and return
       the number of non-OK'd PyChecker warnings.
    '''
    p = Processor(OKd, debug, out=out)
    w = p.run(cmd, *args)
    return p.process(w)


if __name__ == '__main__':

      # no os.EX_... in Python 2.2
    def _usage(x=getattr(os, 'EX_USAGE', 64), cmd=_Cmd):
        '''Show usage.
        '''
        _printf(__doc__, argv0=_argv0, cmd=cmd.split()[0])
        sys.exit(x)

    OKd, debug, cmd = _OKd, _Debug, _Cmd

    argc = len(sys.argv)
    if argc < 2:
        _usage(cmd=cmd)

     # get options, avoid conflicts
     # with 'pychecker' options
    i = 1
    while i < argc:
        t = sys.argv[i]
        if not t.startswith('-'):
            break
        elif t in ('-help', '-h'):
            _usage(0, cmd=cmd)
        elif t in ('-no-OKd', '-no'):
            OKd = False  # don't print OK'd warnings
        elif t in ('-debug', '-Debug'):
            debug = True  # print debug output
        elif t in ('-cmd', '-Cmd'):
            i += 1
            if i < argc:
                cmd = sys.argv[i]  # pychecker cmd
            else:
                _usage(cmd=cmd)
        else:
            if t in ('--', '---'):
                i += 1
            break
        i += 1

    x = 0  # no warnings or all OK'd
    if main(sys.argv[i:], OKd=OKd, debug=debug, cmd=cmd):
         # no os.EX_... in Python 2.2
        x = getattr(os, 'EX_DATAERR', 65)
    sys.exit(x)


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
