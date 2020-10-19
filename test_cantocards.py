import mock
import unittest

from cantocards import TaishaneseScraper

class TestTaishaneseScraper(unittest.TestCase):
    
    scraper = TaishaneseScraper()
    
    def test_import_vocab_list(self):
        self.scraper.import_vocab_list("HSK1.txt")