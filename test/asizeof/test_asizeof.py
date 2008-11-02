
import pympler.asizeof as asizeof
import sys
import unittest

if hasattr(sys, 'getsizeof'):

  class AsizeofTest(unittest.TestCase):

    def _failf(self, fmt, *args):
        self.fail(fmt % args)

    def test_flatsize_vs_getsizeof(self):
        '''Test asizeof.flatsize() vs sys.getsizeof()
        '''
         # make sure test function exists
        f = getattr(asizeof, 'test_flatsize')
        self.assert_(f, msg='no asizeof.test_flatsize')
         # run all the tests, report failures
        n, e = f(failf=self._failf)  # stdf=sys.stderr)
         # no tests ran?
        self.assert_(n, msg='zero tests ran in %r' % f)
         # no unexpected failures?
        self.assert_(not e, msg='%s failures in %s tests' % (e, n))

else:

  class AsizeofTest(unittest.TestCase):

      def test_no_getsizeof(self):
        '''Test skipped: sys.getsizeof() missing
        '''
        pass

if __name__ == '__main__':

    suite = unittest.makeSuite(AsizeofTest, 'test')
  ##suite.addTest(doctest.DocTestSuite())
  ##suite.debug()
    unittest.TextTestRunner(verbosity=1).run(suite)

