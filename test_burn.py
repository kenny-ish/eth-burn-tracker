import unittest

from burn import block_burn


class BurnTest(unittest.TestCase):
    def test_execution_and_blob_burn(self):
        block = {"baseFeePerGas": hex(2 * 10**9), "gasUsed": hex(15_000_000), "blobGasUsed": hex(3 * 131072)}
        exec_burn, blob_burn = block_burn(block, 10)
        self.assertEqual(exec_burn, 2 * 10**9 * 15_000_000)
        self.assertEqual(blob_burn, 3 * 131072 * 10)

    def test_pre_dencun_block_has_no_blob_fields(self):
        self.assertEqual(block_burn({"baseFeePerGas": hex(1), "gasUsed": hex(5)}, 0), (5, 0))


if __name__ == "__main__":
    unittest.main()
