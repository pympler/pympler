"""
This module queries process memory allocation metrics from the operating
system. It provides a platform independent layer to get the amount of virtual
and physical memory allocated to the Python process.

Different mechanisms are implemented: The resource module is tried first.  If
the resource module does not report the required information (Linux/Solaris),
try to read the stat file and then to execute the ps command. If the resource
module does not exist, try a fallback for Windows using the win32 module. If all
fails, return 0 for each attribute.

Windows without the win32 module is not supported.

    >>> from pympler.process import ProcessMemoryInfo
    >>> pmi = ProcessMemoryInfo()
    >>> print "Virtual size [Byte]:", pmi.vsz # doctest: +ELLIPSIS
    Virtual size [Byte]: ...
"""

from os import getpid
from subprocess  import Popen, PIPE
from threading import enumerate

try:
    from resource import getpagesize as _getpagesize
except ImportError:
    _getpagesize = lambda : 4096

class _ProcessMemoryInfo(object):
    """Stores information about various process-level memory metrics. The
    virtual size is stored in attribute `vsz`, the physical memory allocated to
    the process in `rss`, and the number of (major) pagefaults in `pagefaults`.
    This is an abstract base class which needs to be overridden by operating
    system specific implementations. This is done when importing the module.
    """

    pagesize = _getpagesize()

    def __init__(self):
        self.pid = getpid()
        self.rss = 0
        self.vsz = 0
        self.pagefaults = 0
        self.os_specific = []
        self.update()

    def update(self):
        """
        Refresh the information using platform instruments. Returns true if this
        operation yields useful values on the current platform.
        """
        return False

ProcessMemoryInfo = _ProcessMemoryInfo

def is_available():
    """
    Convenience function to check if the current platform is supported by this
    module.
    """
    return ProcessMemoryInfo().update()

class _ProcessMemoryInfoPS(_ProcessMemoryInfo):
    def update(self):
        """
        Get virtual and resident size of current process via 'ps'.
        This should work for MacOS X, Solaris, Linux. Returns true if it was
        successful.
        """
        try:
            p = Popen(['/bin/ps', '-p%s' % self.pid, '-o', 'rss,vsz'],
                      stdout=PIPE, stderr=PIPE)
        except OSError:
            pass
        else:
            s = p.communicate()[0].split()
            if p.returncode == 0 and len(s) >= 2:
                self.vsz = int(s[-1]) * 1024
                self.rss = int(s[-2]) * 1024
                return True
        return False


class _ProcessMemoryInfoProc(_ProcessMemoryInfo):

    key_map = {
        'VmPeak'       : 'Peak virtual memory size',
        'VmSize'       : 'Virtual memory size',
        'VmLck'        : 'Locked memory size',
        'VmHWM'        : 'Peak resident set size',
        'VmRSS'        : 'Resident set size',
        'VmStk'        : 'Size of stack segment',
        'VmData'       : 'Size of data segment',
        'VmExe'        : 'Size of code segment',
        'VmLib'        : 'Shared library code size',
        'VmPTE'        : 'Page table entries size',
    }

    def update(self):
        """
        Get virtual size of current process by reading the process' stat file.
        This should work for Linux.
        """
        try:
            stat = open('/proc/self/stat')
            status = open('/proc/self/status')
        except IOError:
            pass
        else:
            stats = stat.read().split()
            self.vsz = int( stats[22] )
            self.rss = int( stats[23] ) * self.pagesize
            self.pagefaults = int( stats[11] )

            for entry in status.readlines():
                key, value = entry.split(':')
                key = self.key_map.get(key)
                if key:
                    self.os_specific.append((key, value.strip()))

            stat.close()
            status.close()
            return True
        return False


try:
    from resource import getrusage, RUSAGE_SELF

    class _ProcessMemoryInfoResource(_ProcessMemoryInfo):
        def update(self):
            """
            Get resident set size of current process through resource module. Only
            available on Unix. Does not work with any platform tested on.
            """
            usage = getrusage(RUSAGE_SELF)
            self.rss = usage.ru_maxrss * self.pagesize
            self.vsz = usage.ru_maxrss * self.pagesize # XXX rss is not vsz
            self.pagefault = usage.ru_majflt
            return self.rss != 0

    if _ProcessMemoryInfoResource().update():
        ProcessMemoryInfo = _ProcessMemoryInfoResource
    elif _ProcessMemoryInfoProc().update():
        ProcessMemoryInfo = _ProcessMemoryInfoProc
    elif _ProcessMemoryInfoPS().update():
        ProcessMemoryInfo = _ProcessMemoryInfoPS

except ImportError:
    try:
        # Requires pywin32
        from win32process import GetProcessMemoryInfo
        from win32api import GetCurrentProcess
    except ImportError:
        # TODO Emit Warning:
        #print "It is recommended to install pywin32 when running pympler on Microsoft Windows."
        pass
    else:
        class _ProcessMemoryInfoWin32(_ProcessMemoryInfo):
            def update(self):
                process_handle = GetCurrentProcess()
                memory_info = GetProcessMemoryInfo( process_handle )
                self.vsz       = memory_info['PagefileUsage']
                self.rss       = memory_info['WorkingSetSize']
                self.pagefault = memory_info['PageFaultCount']
                return True

        ProcessMemoryInfo = _ProcessMemoryInfoWin32


class ThreadInfo(object):
    """Collect information about an active thread."""
    pass


def get_current_threads():
    """Get a list of `ThreadInfo` objects."""
    threads = []
    for thread in enumerate():
        tinfo = ThreadInfo()
        tinfo.ident = thread.ident
        tinfo.name = thread.name
        tinfo.daemon = thread.daemon
        threads.append(tinfo)
    return threads

