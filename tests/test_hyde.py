from hyde import __version__
from hyde import Hyde
import unittest

class TestHydeMethods(unittest.TestCase):
    def test_hyde_find_files(self):
        with mock.patch('os.walk') as mockwalk:
            mockwalk.return_value = [
                ('/foo', ('bar',), ('baz',)),
                ('/foo/bar', (), ('spam', 'eggs')),
            ]
        
        h = Hyde('.')
        h.__find_files


