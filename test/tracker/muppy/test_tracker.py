import gc
import sys
import unittest

from pympler.tracker.muppy import summary
from pympler.tracker.muppy import tracker

# used to create an indicattor object to track changes between snapshots
import bz2

class TrackerTest(unittest.TestCase):

    def setUp(self):
        gc.collect()

    def _get_indicator(self):
        """Create an indicattor object to track changes between snashots."""
        return bz2.BZ2Compressor()
        
    def _contains_indicator(self, summary):
        """How many indicator objects does the summary contain."""
        res = None
        for row in summary:
            if row[0].find('bz2.BZ2Compressor')!= -1:
                res = row[1]
        return res
        
    def test_stracker_diff(self):
        """Check that the diff is computed correctly.

        This includes that
        - newly created objects are listed
        - removed objects are not listed anymore
        - if objects disappear, they should be listed as negatives
        """
        stracker = tracker.SummaryTracker()
        # for now, no object should be listed
        diff = stracker.diff()
        self.assert_(self._contains_indicator(diff) == None)
        # now an indicator object should be included in the diff
        o = self._get_indicator()
        diff = stracker.diff()
        self.assert_(self._contains_indicator(diff) == 1)
        # now it should be gone again, compared to the
        # previously stored summary
        o = self._get_indicator()
        sn1 = stracker.create_summary()
        o = None
        diff = stracker.diff(summary1=sn1)
        self.assert_(self._contains_indicator(diff) == -1)
        # comparing two homemade summaries should work, too
        o = None
        sn1 = stracker.create_summary()
        o = self._get_indicator()
        sn2 = stracker.create_summary()
        diff = stracker.diff(summary1=sn1, summary2=sn2)
        self.assert_(self._contains_indicator(diff) == 1)
        # providing summary2 without summary1 should raise an exception
        self.assertRaises(ValueError, stracker.diff, summary2=sn2)

#    def test_stracker_for_leaks_in_tracker(self):
#        """Test if any operations of the tracker leak memory."""
#        
#        # test create_summary
#        tmp_tracker = tracker.SummaryTracker()
#        # XXX: TODO
#        self.assert_(muppy.get_usage(tmp_tracker.create_summary) == None)
#        self.assert_(muppy.get_usage(tmp_tracker.store_summary, 1) == None)
#        # test print_diff
#        self.assert_(muppy.get_usage(tmp_tracker.print_diff, [], []) == None)
        
    def test_stracker_create_summary(self):
        """Check that a summary is created correctly.
        
        This can only be done heuristically, e.g that most recent objects are
        included.
        Also check that summaries managed by the tracker are excluded if
        ignore_self is enabled.

        """
        # at the beginning, there should not be an indicator object listed
        tmp_tracker = tracker.SummaryTracker()
        sn = tmp_tracker.create_summary()
        self.assert_(self._contains_indicator(sn) == None)
        # now an indicator object should be listed
        o = self._get_indicator()
        sn = tmp_tracker.create_summary()
        self.assert_(self._contains_indicator(sn) == 1)
        # with ignore_self enabled a second summary should not list the first
        # summary
        sn = tmp_tracker.create_summary()
        sn2 = tmp_tracker.create_summary()
        tmp = summary._sweep(summary.get_diff(sn, sn2))
        self.assert_(len(tmp) == 0)
        # but with ignore_self turned off, there should be some difference
        tmp_tracker = tracker.SummaryTracker(ignore_self=False)
        sn = tmp_tracker.create_summary()
        sn2 = tmp_tracker.create_summary()
        tmp = summary._sweep(summary.get_diff(sn, sn2))
        self.assert_(len(tmp) != 0)
        
    def test_stracker_store_summary(self):
        """Check that a summary is stored under the correct key and most
        recent objects are included.

        """
        stracker = tracker.SummaryTracker()
        key = 1
        stracker.store_summary(key)
        s = stracker.summaries[key]
        self.assert_(s != None)
        # check that indicator 
        key = 2
        tmp = self._get_indicator()
        stracker.store_summary(key)
        s = stracker.summaries[key]
        self.assert_(self._contains_indicator(s) == 1)

#
# now the tests for the object tracker
#
    def test_otracker_get_objects(self):
        otracker = tracker.ObjectTracker()
        o = self._get_indicator()
        # indicator object should be in result set
        self.assert_(o in otracker._get_objects())
        # indicator object should not be in result set
        self.assert_(o not in otracker._get_objects(ignore=[o]))

    def test_otracker_diff(self):
        import inspect
        # indicator object should be listed in diff
        otracker = tracker.ObjectTracker()
        o = self._get_indicator()
        diff = otracker.get_diff()
        self.assert_(o in diff['+'])
        # indicator should not be listed in diff, i.e. no new and no gone
        # indicator object
        diff = otracker.get_diff(ignore=[inspect.currentframe()])
        found = False
        tmp = self._get_indicator()
        for i in diff['+']:
            if isinstance(i, type(tmp)):
                found = True
        self.assert_(not found)
        for i in diff['-']:
            if isinstance(i, type(tmp)):
                found = True
        self.assert_(not found)

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TrackerTest)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

