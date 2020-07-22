from til.tilfile import TypeString
from unittest import TestCase


class TestTypeString(TestCase):
    def test_peek(self):
        ts = TypeString(b'\x01\x02\x03\x04')
        self.assertEqual(ts.peek(1), b'\x01')
        self.assertEqual(ts.peeku8(), 0x01)
        self.assertEqual(ts.peeku16(), 0x0201)
        self.assertEqual(ts.peeku32(), 0x04030201)

    def test_read(self):
        ts = TypeString(b'\x01\x02\x03\x04\x05\x06\x07\x08')
        self.assertEqual(ts.read(1), b'\x01')
        self.assertEqual(ts.readu8(), 0x02)
        self.assertEqual(ts.readu16(), 0x0403)
        self.assertEqual(ts.readu32(), 0x08070605)

    def test_len(self):
        ts = TypeString(b'\x01\x02\x03\x04\x05')
        self.assertEqual(len(ts), 5)

    def test_seek(self):
        ts = TypeString(b'\x01\x02\x03\x04')
        ts.seek(3)
        self.assertEqual(ts.pos(), 3)
        self.assertEqual(ts.peeku8(), 0x04)

