"""ETH burned by base fees and blob fees over recent blocks."""
import argparse
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "eth-burn-tracker"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.load(r)
    if "error" in resp:
        raise RuntimeError(resp["error"].get("message"))
    return resp["result"]


def h(v):
    return int(v, 16) if v else 0


def block_burn(block, blob_base_fee):
    """(execution burn, blob burn) in wei for one block."""
    return h(block.get("baseFeePerGas")) * h(block["gasUsed"]), h(block.get("blobGasUsed")) * blob_base_fee


def blob_fees(url, head, n):
    """baseFeePerBlobGas for blocks head-n+1..head, fetched in <=1024-block feeHistory calls."""
    out = {}
    end = head
    while end > head - n:
        count = min(1024, end - (head - n))
        r = rpc(url, "eth_feeHistory", [hex(count), hex(end), []])
        oldest = h(r["oldestBlock"])
        for i, fee in enumerate((r.get("baseFeePerBlobGas") or [])[:count]):
            out[oldest + i] = h(fee)
        end -= count
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blocks", type=int, default=300)
    ap.add_argument("--rpc", default="https://ethereum-rpc.publicnode.com")
    a = ap.parse_args()

    head = h(rpc(a.rpc, "eth_blockNumber", []))
    fees = blob_fees(a.rpc, head, a.blocks)
    numbers = range(head - a.blocks + 1, head + 1)
    with ThreadPoolExecutor(max_workers=8) as pool:
        blocks = list(pool.map(lambda n: rpc(a.rpc, "eth_getBlockByNumber", [hex(n), False]), numbers))

    exec_total = blob_total = 0
    per_block = []
    for b in blocks:
        e, bl = block_burn(b, fees.get(h(b["number"]), 0))
        exec_total += e
        blob_total += bl
        per_block.append((e + bl, h(b["number"]), h(b.get("baseFeePerGas"))))
    seconds = h(blocks[-1]["timestamp"]) - h(blocks[0]["timestamp"]) or 1
    total = exec_total + blob_total

    print(f"blocks {numbers[0]}-{numbers[-1]} ({len(blocks)} blocks, {seconds / 3600:.2f} h)")
    print(f"burned     {total / 1e18:,.4f} ETH")
    print(f"  base fee {exec_total / 1e18:,.4f} ETH")
    print(f"  blobs    {blob_total / 1e18:,.6f} ETH ({blob_total / total:.2%} of burn)" if total else "  blobs    0")
    print(f"rate       {total / 1e18 / seconds * 3600:,.4f} ETH/hour, {total / 1e18 / seconds * 86400:,.2f} ETH/day at this pace")
    print("\nbiggest burners")
    for burn, n, base in sorted(per_block, reverse=True)[:5]:
        print(f"  block {n}  {burn / 1e18:.5f} ETH  (base fee {base / 1e9:.2f} gwei)")


if __name__ == "__main__":
    main()
