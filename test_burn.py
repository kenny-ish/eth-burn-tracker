import contextlib
import io
import unittest
from unittest import mock

import burn
from burn import block_burn, burn_rate


def fake_rpc(head, timestamps):
    # stand-in for burn.rpc serving len(timestamps) blocks ending at head, 1 gwei base fee, 10M gas
    first = head - len(timestamps) + 1

    def rpc(url, method, params):
        if method == "eth_blockNumber":
            return hex(head)
        if method == "eth_feeHistory":
            return {"oldestBlock": hex(first), "baseFeePerBlobGas": [hex(0)] * len(timestamps)}
        if method == "eth_getBlockByNumber":
            n = int(params[0], 16)
            return {"number": hex(n), "timestamp": hex(timestamps[n - first]),
                    "baseFeePerGas": hex(10**9), "gasUsed": hex(10_000_000)}
        raise AssertionError(method)

    return rpc


def run_main(blocks, timestamps):
    out = io.StringIO()
    with mock.patch("burn.rpc", fake_rpc(1000, timestamps)), \
            mock.patch("sys.argv", ["burn.py", "--blocks", str(blocks)]), \
            contextlib.redirect_stdout(out):
        burn.main()
    return out.getvalue()


class BurnTest(unittest.TestCase):
    def test_execution_and_blob_burn(self):
        block = {"baseFeePerGas": hex(2 * 10**9), "gasUsed": hex(15_000_000), "blobGasUsed": hex(3 * 131072)}
        exec_burn, blob_burn = block_burn(block, 10)
        self.assertEqual(exec_burn, 2 * 10**9 * 15_000_000)
        self.assertEqual(blob_burn, 3 * 131072 * 10)

    def test_pre_dencun_block_has_no_blob_fields(self):
        self.assertEqual(block_burn({"baseFeePerGas": hex(1), "gasUsed": hex(5)}, 0), (5, 0))


class BurnRateTest(unittest.TestCase):
    def test_rate_matches_burns_to_intervals(self):
        blocks = [{"timestamp": hex(t)} for t in (100, 112, 124)]
        # three blocks but only two 12 s intervals: the first block's burn is before the window starts
        self.assertEqual(burn_rate(blocks, [1000, 200, 400]), (200 + 400) / 24)

    def test_single_block_has_no_rate(self):
        self.assertIsNone(burn_rate([{"timestamp": hex(100)}], [1000]))

    def test_main_single_block_prints_no_rate(self):
        out = run_main(1, [100])
        self.assertIn("rate       n/a", out)
        self.assertNotIn("ETH/hour", out)

    def test_main_rate_uses_second_block_only(self):
        out = run_main(2, [100, 112])
        # one block of 10M gas at 1 gwei = 0.01 ETH per 12 s = 3 ETH/hour, 72 ETH/day
        self.assertIn("rate       3.0000 ETH/hour, 72.00 ETH/day", out)


if __name__ == "__main__":
    unittest.main()
