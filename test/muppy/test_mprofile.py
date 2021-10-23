import unittest

from pympler import mprofile

class MProfileTest(unittest.TestCase):

    def test_codepoint_included(self):
        """Test that only valid codepoints are returned."""
        prof = mprofile.MProfiler()
        # test single pre-defined codepoints
        prof.codepoints = [(None, None, None)]
        self.assertTrue(prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [('foo', 'bar', 42)]
        self.assertTrue(prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [('foo', None, None)]
        self.assertTrue(prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [('bar', None, None)]
        self.assertTrue(not prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [(None, 'bar', None)]
        self.assertTrue(prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [(None, 'foo', None)]
        self.assertTrue(not prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [(None, None, 42)]
        self.assertTrue(prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [(None, None, 0)]
        self.assertTrue(not prof.codepoint_included(('foo', 'bar', 42)))

        prof.codepoints = [('foo', 'bar', None)]
        self.assertTrue(prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [('foo', 'foo', None)]
        self.assertTrue(not prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [('foo', 'foo', 0)]
        self.assertTrue(not prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [('bar', 'foo', 42)]
        self.assertTrue(not prof.codepoint_included(('foo', 'bar', 42)))

        # test multiple pre-defined codepoints
        prof.codepoints = [('foo', 'bar', 42), ('foo', 'baz', 10)]
        self.assertTrue(prof.codepoint_included(('foo', 'bar', 42)))
        prof.codepoints = [('foo', 'bar', 0), ('foo', 'baz', 10)]
        self.assertTrue(not prof.codepoint_included(('foo', 'bar', 42)))


def suite():
    suite = unittest.makeSuite(MProfileTest,'test')
    return suite

if __name__ == '__main__':
    unittest.main()
