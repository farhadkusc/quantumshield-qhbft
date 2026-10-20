# NJIT Wulver job

Heavy run for [Wulver](https://hpc.njit.edu/clusters/get_started_on_Wulver). Output of the lab profile is `lab/njit/results/lab.json`.

The lab profile draws 200,000 quorum pairs at n = 64, 256, 1024, and 4096 and counts pairs that intersect in fewer than f+1 seats. The same job writes the closed-form ML-DSA-87 byte and critical-path grid at one-way delays of 5, 20, and 40 ms.

## Smoke, on any machine

```bash
python3 lab/njit/run_lab.py --profile smoke --workers 2
```

4,000 pairs at n = 16 and n = 64. Output: `lab/njit/results/smoke.json`.

## Submit

From the clone root, on a Wulver login node:

```bash
# Put your UCID on the account line in lab/njit/wulver.sbatch first.
sbatch lab/njit/wulver.sbatch
squeue -u "$USER"
```

The script requests `general` / `standard`, 8 CPUs, 32 GB, and two hours. The n = 4096 draw is the piece that wants the memory. Logs: `lab/njit/logs/`. Result: `lab/njit/results/lab.json`.

Login steps are on the Wulver getting-started page.
