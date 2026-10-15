#!/usr/bin/env python3
"""Generate the small example dataset used in the benchmarking exercise.

The dataset is a CSV file of random 3D points (id,x,y,z) inside the unit cube.
It is deliberately small (a few hundred kB) -- the cost of the exercise comes
from the algorithm, not from the size of the data.

Usage:
    python make_points.py                    # 8000 points -> points.csv
    python make_points.py --n 8000 --seed 1  # explicit options
"""
import argparse
import random


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=8000, help="number of points")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--output", default="points.csv", help="output CSV file")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    with open(args.output, "w") as f:
        f.write("id,x,y,z\n")
        for i in range(args.n):
            f.write("%d,%.6f,%.6f,%.6f\n" % (i, rng.random(), rng.random(), rng.random()))
    print("Wrote %d points to %s" % (args.n, args.output))


if __name__ == "__main__":
    main()
