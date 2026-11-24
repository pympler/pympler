"""Tests for human-readable size formatting."""

import unittest

from pympler import summary
from pympler.util.stringutils import pp


class PrettySizeTest(unittest.TestCase):

    def test_negative_sizes_use_same_units_as_positive_sizes(self):
        for magnitude in (1025, 2048, 2 * 1024 ** 2, 2 * 1024 ** 3,
                          2 * 1024 ** 4):
            for base in (1000, 1024):
                with self.subTest(magnitude=magnitude, base=base):
                    positive = pp(magnitude, base).split()
                    negative = pp(-magnitude, base).split()
                    self.assertEqual(negative[1], positive[1])
                    self.assertEqual(float(negative[0]), -float(positive[0]))

    def test_negative_sizes_preserve_byte_boundary(self):
        for value in (0, -1, -1023, -1024):
            with self.subTest(value=value):
                self.assertEqual(pp(value).split(), [str(value), 'B'])

    def test_negative_infinity_keeps_raising(self):
        import os
        import subprocess
        import sys

        script = '''
from pympler.util.stringutils import pp
try:
    pp(float('-inf'))
except OverflowError:
    pass
else:
    raise RuntimeError('negative infinity must not be formatted')
'''
        env = dict(os.environ, PYTHONPATH=os.getcwd())
        subprocess.run([sys.executable, '-c', script], env=env,
                       check=True, timeout=5)

    def test_format_released_memory_from_summary_diff(self):
        allocation = bytearray(2 * 1024 ** 2)
        before = summary.summarize([allocation])
        after = summary.summarize([])
        original_before = [row[:] for row in before]
        rows = summary.get_diff(before, after)
        self.assertEqual(rows[0][:2], ['bytearray', -1])
        self.assertLess(rows[0][2], -2 * 1024 ** 2)
        line = list(summary.format_(rows))[-1]
        self.assertEqual(line.split('|')[-1].split(), ['-2.00', 'MB'])
        self.assertEqual(before, original_before)
        self.assertEqual(after, [])


if __name__ == '__main__':
    unittest.main()
