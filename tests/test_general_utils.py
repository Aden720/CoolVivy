# test_general_utils.py
import unittest
from general_utils import formatMillisecondsToDurationString

class TestGeneralUtils(unittest.TestCase):
    def test_formatMillisecondsToDurationString(self):
        self.assertEqual(formatMillisecondsToDurationString(3600000), '`01:00:00`')
        self.assertEqual(formatMillisecondsToDurationString(3661000), '`01:01:01`')
        self.assertEqual(formatMillisecondsToDurationString(60000), '`01:00`')
        self.assertEqual(formatMillisecondsToDurationString(61000), '`01:01`')
        self.assertEqual(formatMillisecondsToDurationString(1000), '`00:01`')

if __name__ == '__main__':
    unittest.main()