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

    def test_encrypt_decrypt_none(self):
        self.assertEqual(Utility.encrypt(None), '')
        self.assertEqual(Utility.decrypt(None), '')

    def test_encrypt_decrypt_empty(self):
        self.assertEqual(Utility.encrypt(''), '')
        self.assertEqual(Utility.decrypt(''), '')

    def test_encrypt_decrypt_space(self):
        self.assertEqual(Utility.encrypt('   \t  '), '')
        self.assertEqual(Utility.decrypt('  \t   \t'), '')
