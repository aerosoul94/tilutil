from til.tilfile import TypeString
from unittest import TestCase


class TestTypeString(TestCase):
    def test_peek(self):
        ts = TypeString(b'\x01\x02\x03\x04')
        self.assertEqual(ts.peek(1), b'\x01')
        self.assertEqual(ts.peek_db(), 0x01)

    def test_read(self):
        ts = TypeString(b'\x01\x02\x03\x04\x05\x06\x07\x08')
        self.assertEqual(ts.read(1), b'\x01')
        self.assertEqual(ts.read_db(), 0x02)

    def test_len(self):
        ts = TypeString(b'\x01\x02\x03\x04\x05')
        self.assertEqual(len(ts), 5)

    def test_seek(self):
        ts = TypeString(b'\x01\x02\x03\x04')
        ts.seek(3)
        self.assertEqual(ts.pos(), 3)
        self.assertEqual(ts.peek_db(), 0x04)

