import unittest

from virtual_modi.virtual_bundle import VirtualBundle


class TestVirtualBundle(unittest.TestCase):

    def setUp(self):
        self.vb = VirtualBundle(conn_type='dir', modi_version=1)
        #self.vb.open()

    def tearDown(self):
        #self.vb.close()
        pass

    def test_init(self):
        self.assertEqual('tcp', 'tcp')


if __name__ == "__main__":
    unittest.main()