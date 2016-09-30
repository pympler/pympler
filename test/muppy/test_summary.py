import doctest
import sys
import unittest

from sys import getsizeof

from pympler import summary, muppy


class SummaryTest(unittest.TestCase):

    class DevNull(object):
        def write(self, text):
            pass

    def test_repr(self):
        """Test that the right representation is returned. """
        self.assert_(summary._repr(''), "<type 'str'>")
        self.assert_(summary._repr('', 1), "<type 'str'>")
        self.assert_(summary._repr('', verbosity=1), "<type 'str'>")
        self.assert_(summary._repr('', verbosity=100), "<type 'str'>")

    def test_summarize(self):
        """Test summarize method. """
        objects = [1, 'a', 'b', 'a', 5, [], {}]
        expected = [[summary._repr(''), 3, 3*getsizeof('a')],\
                    [summary._repr(1), 2, 2*getsizeof(1)],\
                    [summary._repr([]), 1, getsizeof([])],\
                    [summary._repr({}), 1, getsizeof({})]]
        res = summary.summarize(objects)
        for row_e in res:
            self.assert_(row_e in expected)

    def test_summary_diff(self):
        """Test summary diff. """
        left = [[str(str), 3, 3*getsizeof('a')],\
                [str(int), 2, 2*getsizeof(1)],\
                [str(list), 1, getsizeof([])],\
                [str(dict), 1, getsizeof({})]]
        right = [[str(str), 2, 2*getsizeof('a')],\
                 [str(int), 3, 3*getsizeof(1)],\
                 [str(list), 1, getsizeof([1,2,3])],\
                 [str(dict), 1, getsizeof({})],
                 [str(tuple), 1, getsizeof((1,2))]]

        expected = [[str(str), -1, -1*getsizeof('a')],\
                    [str(int), 1, +1*getsizeof(1)],\
                    [str(list), 0, getsizeof([1,2,3]) - getsizeof([])],\
                    [str(dict), 0, 0],
                    [str(tuple), 1, getsizeof((1,2))]]
        res = summary.get_diff(left, right)
        for row_e in res:
            self.assertTrue(row_e in expected)


    def test_print_diff(self):
        """Test summary can be printed."""
        try:
            self._stdout = sys.stdout
            sys.stdout = self.DevNull()
            sum1 = summary.summarize(muppy.get_objects())
            sum2 = summary.summarize(muppy.get_objects())
            sumdiff = summary.get_diff(sum1, sum2)
            summary.print_(sumdiff)
        finally:
            sys.stdout = self._stdout


    def test_subtract(self):
        """Test that a single object's data is correctly subtracted from a summary.
        - result in correct total size and total number of objects
        - if object was not listed before, it should be listed negative
          afterwards
        """

        objects = ['the', 'quick', 'brown', 'fox', 1298, 123, 234, [], {}]
        summ = summary.summarize(objects)
        summary._subtract(summ, 'the')
        summary._subtract(summ, {})
        summary._subtract(summ, (1,))
        # to verify that these rows where actually included afterwards
        checked_str = checked_dict = checked_tuple = False
        for row in summ:
            if row[0] == summary._repr(''):
                totalsize = getsizeof('quick') + getsizeof('brown') +\
                            getsizeof('fox')
                self.assert_(row[1] == 3, "%s != %s" % (row[1], 3))
                self.assert_(row[2] == totalsize, totalsize)
                checked_str = True
            if row[0] == summary._repr({}):
                self.assert_(row[1] == 0)
                self.assert_(row[2] == 0)
                checked_dict = True
            if row[0] == summary._repr((1,)):
                self.assert_(row[1] == -1)
                self.assert_(row[2] == -getsizeof((1,)))
                checked_tuple = True

        self.assert_(checked_str, "no str found in summary")
        self.assert_(checked_dict, "no dict found in summary")
        self.assert_(checked_tuple, "no tuple found in summary")

        summary._subtract(summ, 'quick')
        summary._subtract(summ, 'brown')
        checked_str = False
        for row in summ:
            if row[0] == summary._repr(''):
                self.assert_(row[1] == 1)
                self.assert_(row[2] == getsizeof('fox'))
                checked_str = True
        self.assert_(checked_str, "no str found in summ")

    def test_sweep(self):
        """Test that all and only empty entries are removed from a summary."""
        objects = ['the', 'quick', 'brown', 'fox', 1298, 123, 234, [], {}]
        summ = summary.summarize(objects)
        # correct removal of rows when sizes are empty
        summary._subtract(summ, {})
        summary._subtract(summ, [])
        summ = summary._sweep(summ)
        found_dict = found_tuple = False
        for row in summ:
            if row[0] == "<type 'dict'>":
                found_dict = True
            if row[0] == "<type 'tuple'>":
                found_tuple = True
        self.assert_(found_dict == False)
        self.assert_(found_tuple == False)
        # do not remove row if one of the sizes is not empty
        # e.g. if the number of objects of a type did not change, but the
        # total size did
        summ = summary._subtract(summ, 'the')
        summ = summary._subtract(summ, 'quick')
        summ = summary._subtract(summ, 'brown')
        summ = summary._subtract(summ, '42')
        summ = summary._sweep(summ)
        found_string = False
        for row in summ:
            if row[0] == summary._repr(''):
                found_string = True
                self.assert_(row[1] == 0)
                totalsize = getsizeof('fox') - getsizeof('42')
                self.assert_(row[2] == totalsize)
        self.assert_(found_string == True)

    def test_traverse(self):
        """Test that all objects of a summary are traversed."""
        touched = []
        def remember(o, touched):
            touched.append(o)

        s = [['row1', 1, 2], ['row2', 3, 4], ['row3', 5, 6]]
        summary._traverse(s, remember, touched)

        self.assert_(s in touched)
        for row in s:
            self.assert_(row in touched)
            for item in row:
                self.assert_(item in touched)



test_print_ = """
>>> objects = [1,2,3,4,5L, 33000L, "a", "ab", "abc", [], {}, {10: "t"}, ]

At first the default values.
>>> summary.print_(objects)
          types |   # objects |   total size
=============== | =========== | ============
  <type 'dict'> |           2 |          560
   <type 'str'> |           3 |          126
   <type 'int'> |           4 |           96
  <type 'long'> |           2 |           66
  <type 'list'> |           1 |           40

Next, we try it sorted by object number
>>> summary.print_(objects, sort='#')
          types |   # objects |   total size
=============== | =========== | ============
   <type 'int'> |           4 |           96
   <type 'str'> |           3 |          126
  <type 'long'> |           2 |           66
  <type 'dict'> |           2 |          560
  <type 'list'> |           1 |           40

Now, object number and with ascending order
>>> summary.print_(objects, sort='#', order='ascending')
          types |   # objects |   total size
=============== | =========== | ============
  <type 'list'> |           1 |           40
  <type 'long'> |           2 |           66
  <type 'dict'> |           2 |          560
   <type 'str'> |           3 |          126
   <type 'int'> |           4 |           96

Let's limit the output to two rows
>>> summary.print_(objects, limit=2, sort='#', order='ascending')
          types |   # objects |   total size
=============== | =========== | ============
  <type 'list'> |           1 |           40
  <type 'long'> |           2 |           66

Finally, sorted by size with descending order
>>> summary.print_(objects, sort='size', order='descending')
          types |   # objects |   total size
=============== | =========== | ============
  <type 'dict'> |           2 |          560
   <type 'str'> |           3 |          126
   <type 'int'> |           4 |           96
  <type 'long'> |           2 |           66
  <type 'list'> |           1 |           40
"""

test_print_table = """

The _print_table function should print a nice, clean table.

>>> r1 = ["types", "#objects", "total size"]
>>> r2 = [str, 17, 442]
>>> r3 = [dict, 4, 9126]
>>> r4 = [list, 11, 781235]
>>> muppy._print_table([r1, r2, r3, r4])
          types |   #objects |   total size
=============== | ========== | ============
   <type 'str'> |         17 |          442
  <type 'dict'> |          4 |         9126
  <type 'list'> |         11 |       781235
"""

#__test__ = {"test_print_table": test_print_table,\
#            "test_print_": test_print_}

def suite():
    suite = unittest.makeSuite(SummaryTest,'test')
    suite.addTest(doctest.DocTestSuite())
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
