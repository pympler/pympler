"""
Check the measured process sizes. If we are on a platform which supports
multiple measuring facilities (e.g. Linux), check if the reported sizes match.

This should help to protect against scaling errors (e.g. Byte vs KiB) or using
the wrong value for a different measure (e.g. resident in physical memory vs
virtual memory size).
"""

import sys
import unittest

from unittest import mock
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
                self.assertTrue(resinfo.rss >= psinfo.rss)


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
                self.assertTrue(resinfo.rss >= procinfo.rss)


    def test_get_current_threads(self):
        '''Test thread info is extracted.'''
        tinfos = process.get_current_threads()
        for tinfo in tinfos:
            self.assertEqual(type(tinfo.ident), int)
            self.assertEqual(type(tinfo.name), type(''))
            self.assertEqual(type(tinfo.daemon), type(True))
            self.assertNotEqual(tinfo.ident, 0)


    def test_proc(self):
        '''Test reading proc stats with mock data.'''
        mock_stat = mock.mock_open(read_data='22411 (cat) R 22301 22411 22301 34818 22411 4194304 82 0 0 0 0 0 0 0 20 0 1 0 709170 8155136 221 18446744073709551615 94052544688128 94052544719312 140729623469552 0 0 0 0 0 0 0 0 0 17 6 0 0 0 0 0 94052546816624 94052546818240 94052566347776 140729623473446 140729623473466 140729623473466 140729623478255 0')
        mock_status = mock.mock_open(read_data='Name:  cat\n\nVmData:    2 kB\nMultiple colons: 1:1')
        with mock.patch('builtins.open', new_callable=mock.mock_open) as mock_file:
            mock_file.side_effect = [mock_stat.return_value, mock_status.return_value]
            procinfo = process._ProcessMemoryInfoProc()
        self.assertTrue(procinfo.available)
        self.assertEqual(procinfo.vsz, 8155136)
        self.assertEqual(procinfo.data_segment, 2048)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    tclasses = [ ProcessMemoryTests, ]
    for tclass in tclasses:
        names = unittest.getTestCaseNames(tclass, 'test_')
        suite.addTests(map(tclass, names))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
