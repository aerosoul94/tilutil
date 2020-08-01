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

    def test_db(self):
        ts = TypeString()
        ts.append_db(0xff)
        self.assertEqual(ts.read_db(), 0xff)

    def test_dt(self):
        ts = TypeString()
        ts.append_dt(0x7ffe)
        self.assertEqual(ts.read_dt(), 0x7ffe)

    def test_de(self):
        ts = TypeString()
        ts.append_de(0xffffffff)
        self.assertEqual(ts.read_de(), 0xffffffff)

    def test_da(self):
        ts = TypeString()
        ts.append_da(0x7fffffff, 0xffffffff)
        self.assertEqual(ts.read_da(), (True, 0x7fffffff, 0xffffffff))

    def test_complex_n(self):
        ts = TypeString()
        ts.append_complex_n(0x7ffe, False)
        self.assertEqual(ts.read_complex_n(), 0x7ffe)

    def test_pstring(self):
        ts = TypeString()
        ts.append_pstring("test")
        self.assertEqual(ts.read_pstring().decode('ascii'), "test")
