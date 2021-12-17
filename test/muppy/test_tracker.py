import gc
import inspect
import os
import sys
import unittest

from pympler import summary, tracker
from pympler.util import compat


class TrackerTest(unittest.TestCase):

    def setUp(self):
        gc.collect()
        # simplify object type representation used for summaries
        # for these tests it is not necessary to work with the extended repr
        def simple_repr(o, verbosity=1):
            return str(type(o))
        self.old_repr = summary._repr
        summary._repr = simple_repr


    def tearDown(self):
        summary._repr = self.old_repr


    def _get_indicator(self):
        """Create an indicator object to track changes between snapshots."""
        class UniqueIndicator(object): pass

        return UniqueIndicator()


    def _contains_indicator(self, summary):
        """How many indicator objects does the summary contain."""
        res = None
        for row in summary:
            if row[0].find('UniqueIndicator')!= -1:
                res = row[1]
        return res


    def test_stracker_diff(self):
        """Test that the diff is computed correctly.

        This includes that
        - newly created objects are listed
        - removed objects are not listed anymore
        - if objects disappear, they should be listed as negatives
        """
        stracker = tracker.SummaryTracker()
        # for now, no object should be listed
        diff = stracker.diff()
        self.assertTrue(self._contains_indicator(diff) == None)
        # now an indicator object should be included in the diff
        o = self._get_indicator()
        diff = stracker.diff()
        self.assertTrue(self._contains_indicator(diff) == 1)
        # now it should be gone again, compared to the
        # previously stored summary
        o = self._get_indicator()
        sn1 = stracker.create_summary()
        o = None
        diff = stracker.diff(summary1=sn1)
        self.assertTrue(self._contains_indicator(diff) == -1)
        # comparing two homemade summaries should work, too
        o = None
        sn1 = stracker.create_summary()
        o = self._get_indicator()
        sn2 = stracker.create_summary()
        diff = stracker.diff(summary1=sn1, summary2=sn2)
        self.assertTrue(self._contains_indicator(diff) == 1)
        # providing summary2 without summary1 should raise an exception
        self.assertRaises(ValueError, stracker.diff, summary2=sn2)


#    def test_stracker_for_leaks_in_tracker(self):
#        """Test if any operations of the tracker leak memory."""
#
#        # test create_summary
#        tmp_tracker = tracker.SummaryTracker()
#        # XXX: TODO
#        self.assertTrue(muppy.get_usage(tmp_tracker.create_summary) == None)
#        self.assertTrue(muppy.get_usage(tmp_tracker.store_summary, 1) == None)
#        # test print_diff
#        self.assertTrue(muppy.get_usage(tmp_tracker.print_diff, [], []) == None)


    @unittest.skipIf(sys.platform.startswith("win"), "Fails on Windows for unknown reasons")
    def test_stracker_create_summary(self):
        """Test that a summary is created correctly.

        This can only be done heuristically, e.g that most recent objects are
        included.
        Also check that summaries managed by the tracker are excluded if
        ignore_self is enabled.

        """
        # at the beginning, there should not be an indicator object listed
        tmp_tracker = tracker.SummaryTracker()
        sn = tmp_tracker.create_summary()
        self.assertEqual(self._contains_indicator(sn), None)
        # now an indicator object should be listed
        o = self._get_indicator()
        sn = tmp_tracker.create_summary()
        self.assertEqual(self._contains_indicator(sn), 1)
        # with ignore_self enabled a second summary should not list the first
        # summary
        sn = tmp_tracker.create_summary()
        sn2 = tmp_tracker.create_summary()
        tmp = summary._sweep(summary.get_diff(sn, sn2))
        self.assertEqual(len(tmp), 0, tmp)
        # but with ignore_self turned off, there should be some difference
        tmp_tracker = tracker.SummaryTracker(ignore_self=False)
        sn = tmp_tracker.create_summary()
        tmp_tracker.new_obj = self._get_indicator()
        sn2 = tmp_tracker.create_summary()
        tmp = summary._sweep(summary.get_diff(sn, sn2))
        self.assertNotEqual(len(tmp), 0)


    def test_stracker_store_summary(self):
        """Test that a summary is stored under the correct key and most
        recent objects are included.

        """
        stracker = tracker.SummaryTracker()
        key = 1
        stracker.store_summary(key)
        s = stracker.summaries[key]
        self.assertTrue(s != None)
        # check that indicator
        key = 2
        tmp = self._get_indicator()
        stracker.store_summary(key)
        s = stracker.summaries[key]
        self.assertEqual(self._contains_indicator(s), 1)


#
# now the tests for the object tracker
#
    def test_otracker_get_objects(self):
        """Test object tracker."""
        otracker = tracker.ObjectTracker()
        o = self._get_indicator()
        # indicator object should be in result set
        res = compat.object_in_list(o, otracker._get_objects())
        self.assertTrue(res)
        # indicator object should not be in result set
        res = compat.object_in_list(o, otracker._get_objects(ignore=(o,)))
        self.assertFalse(res)


    def test_otracker_diff(self):
        """Test object tracker diff."""
        # This test regularly times out when run under coverage.
        if os.environ.get('COVERAGE'):
            sys.stderr.write("(disabled) ")
            return
        # indicator object should be listed in diff
        otracker = tracker.ObjectTracker()
        o = self._get_indicator()
        diff = otracker.get_diff()
        self.assertTrue(o in diff['+'])
        # indicator should not be listed in diff, i.e. no new and no gone
        # indicator object
        diff = otracker.get_diff(ignore=(inspect.currentframe(),))
        found = False
        tmp = self._get_indicator()
        for i in diff['+']:
            if isinstance(i, type(tmp)):
                found = True
        self.assertTrue(not found)
        for i in diff['-']:
            if isinstance(i, type(tmp)):
                found = True
        self.assertTrue(not found)


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TrackerTest)


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

