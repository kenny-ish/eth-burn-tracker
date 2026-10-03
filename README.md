# eth-burn-tracker

Adds up the ETH burned in the last N blocks. Each transaction burns `baseFee x gasUsed` and each
blob burns `blobBaseFee x blobGasUsed`.

```bash
python burn.py
python burn.py --blocks 1800        # ~6 hours
```

Data sources:

- `eth_getBlockByNumber` for each block's `baseFeePerGas`, `gasUsed` and `blobGasUsed`
- `eth_feeHistory` for `baseFeePerBlobGas`, the blob base fee of each block after Dencun. That way
  the blob fee formula, whose parameters change with forks, doesn't have to be reimplemented.

It prints the total burned in the window split into execution and blob fees, the burn rate per hour
and per day at that pace, the share of blob fees and the five blocks that burned the most.

This only covers the burn. Issuance happens on the consensus layer and would need a beacon node.

## Tests

```bash
python -m unittest -v
```
