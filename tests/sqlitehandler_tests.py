import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logger.sqlite_handler import SQLiteHandler


class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        self.handler = SQLiteHandler('test_db.sqlite3')

    def test_add_line(self):
        cursor = self.handler.get_cursor()

        self.handler.add_msg('irc.freenode.net', '#yychat', 'nickname',
                             'hi friends')

        cursor.execute('SELECT COUNT(*) from message;')
        num_rows = cursor.fetchone()[0]
        self.assertEqual(num_rows, 1)

        self.handler.remove()

if __name__ == '__main__':
    unittest.main()
