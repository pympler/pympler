"""
Check the measured process sizes. If we are on a platform which supports
multiple measuring facilities (e.g. Linux), check if the reported sizes match.

This should help to protect against scaling errors (e.g. Byte vs KiB) or using
the wrong value for a different measure (e.g. resident in physical memory vs
virtual memory size).
"""

import sys
import unittest

from pympler import process


class ProcessMemoryTests(unittest.TestCase):

    def _match_sizes(self, pi1, pi2, ignore=[]):
        """
        Match sizes by comparing each set field. Process size may change
        inbetween two measurements.
        """
        if pi1.available and pi2.available:
            for arg in ('vsz', 'rss', 'data_segment', 'shared_segment',
                        'stack_segment', 'code_segment'):
                if arg in ignore:
                    continue
                size1 = getattr(pi1, arg)
                size2 = getattr(pi2, arg)
                if size1 and size2:
                    delta = abs(size1 - size2)
                    # Allow for a difference of the size of two pages or 5%
                    if delta > pi1.pagesize * 2 and delta > size1 * 0.05:
                        self.fail("%s mismatch: %d != %d" % (arg, size1, size2))
            if pi1.pagefaults and pi2.pagefaults:
                # If both records report pagefaults compare the reported
                # number. If a pagefault happens after taking the first
                # snapshot and before taking the second the latter will show a
                # higher pagefault number. In that case take another snapshot
                # with the first variant and check it's now reporting a higher
                # number as well. We assume pagefaults statistics are
                # monotonic.
                if pi1.pagefaults < pi2.pagefaults:
                    pi1.update()
                    if pi1.pagefaults < pi2.pagefaults:
                        pf1 = pi1.pagefaults
                        pf2 = pi2.pagefaults
                        self.fail("Pagefault mismatch: %d != %d" % (pf1, pf2))
                else:
                    self.assertEqual(pi1.pagefaults, pi2.pagefaults)
            if pi1.pagesize and pi2.pagesize:
                self.assertEqual(pi1.pagesize, pi2.pagesize)


    def test_ps_vs_proc_sizes(self):
        '''Test process sizes match: ps util vs /proc/self/stat
        '''
        psinfo = process._ProcessMemoryInfoPS()
        procinfo = process._ProcessMemoryInfoProc()
        self._match_sizes(psinfo, procinfo)


    def test_ps_vs_getrusage(self):
        '''Test process sizes match: ps util vs getrusage
        '''
        psinfo = process._ProcessMemoryInfoPS()
        try:
            resinfo = process._ProcessMemoryInfoResource()
        except AttributeError:
            pass
        else:
            self._match_sizes(psinfo, resinfo, ignore=['rss'])
            if psinfo.available and resinfo.available:
                self.assert_(resinfo.rss >= psinfo.rss)


    def test_proc_vs_getrusage(self):
        '''Test process sizes match: /proc/self/stat util vs getrusage
        '''
        procinfo = process._ProcessMemoryInfoProc()
        try:
            resinfo = process._ProcessMemoryInfoResource()
        except AttributeError:
            pass
        else:
            self._match_sizes(procinfo, resinfo, ignore=['rss'])
            if procinfo.available and resinfo.available:
                self.assert_(resinfo.rss >= procinfo.rss)


    def test_get_current_threads(self):
        '''Test thread info is extracted.'''
        tinfos = process.get_current_threads()
        for tinfo in tinfos:
            self.assertEqual(type(tinfo.ident), int)
            self.assertEqual(type(tinfo.name), type(''))
            self.assertEqual(type(tinfo.daemon), type(True))
            self.failIfEqual(tinfo.ident, 0)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [ ProcessMemoryTests, ]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
