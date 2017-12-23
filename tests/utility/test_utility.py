import unittest

from utility.utility import Utility

class UtilityTestCase(unittest.TestCase):

    def test_encrypt_decrypt(self):
        text = 'abcd123'
        encrypt = Utility.encrypt(text)
        self.assertTrue(isinstance(encrypt, str))

        decrypt = Utility.decrypt(encrypt)
        self.assertTrue(isinstance(decrypt, str))
        self.assertEqual(decrypt, text)
