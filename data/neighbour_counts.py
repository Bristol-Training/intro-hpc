#!/usr/bin/env python3
"""Count the neighbours of every point in a 3D point cloud.

For each point, count how many other points lie within a given radius.
Every point is compared with every other point, so the work grows
quadratically with the number of points: doubling the data should take
roughly four times longer.

Only the Python standard library is used, so it runs with any Python >= 3.6.

Examples:
    python neighbour_counts.py points.csv
    python neighbour_counts.py points_2000.csv --radius 0.1
    python neighbour_counts.py points.csv --workers 4              # use 4 processes
    python neighbour_counts.py points.csv --store-neighbours       # uses more memory
"""
import argparse
import csv
import resource
import sys
import time
from multiprocessing import Pool

# Shared by the worker processes (set once per process by init_worker)
POINTS = []
RADIUS2 = 0.0
STORE = False


def load_points(path):
    """Read the x, y, z columns of a CSV file into a list of tuples."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return [(float(r["x"]), float(r["y"]), float(r["z"])) for r in reader]


def init_worker(points, radius, store):
    global POINTS, RADIUS2, STORE
    POINTS = points
    RADIUS2 = radius * radius
    STORE = store


def process_rows(bounds):
    """Process rows start..stop-1: compare each one against all the points."""
    start, stop = bounds
    counts = []
    neighbours = []
    for i in range(start, stop):
        xi, yi, zi = POINTS[i]
        found = 0
        near = []
        for j, (xj, yj, zj) in enumerate(POINTS):
            if j == i:
                continue
            dx = xi - xj
            dy = yi - yj
            dz = zi - zj
            if dx * dx + dy * dy + dz * dz < RADIUS2:
                found += 1
                if STORE:
                    near.append(j)
        counts.append(found)
        if STORE:
            neighbours.append(near)
    return counts, neighbours


def peak_memory_mb():
    """Peak resident memory of this process, in MB (Linux reports kB, macOS bytes)."""
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024.0 * 1024.0) if sys.platform == "darwin" else peak / 1024.0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="CSV file with columns id,x,y,z")
    parser.add_argument("--radius", type=float, default=0.05,
                        help="neighbour radius (default: 0.05)")
    parser.add_argument("--workers", type=int, default=1,
                        help="number of worker processes (default: 1)")
    parser.add_argument("--store-neighbours", action="store_true",
                        help="keep the list of neighbours of every point "
                             "(needs much more memory)")
    args = parser.parse_args()

    t0 = time.perf_counter()
    points = load_points(args.input)
    n = len(points)
    t_load = time.perf_counter() - t0

    # Split the rows into chunks; with one worker this is a single chunk.
    n_chunks = max(1, args.workers * 4)
    size = (n + n_chunks - 1) // n_chunks
    chunks = [(s, min(s + size, n)) for s in range(0, n, size)]

    t1 = time.perf_counter()
    initargs = (points, args.radius, args.store_neighbours)
    if args.workers == 1:
        init_worker(*initargs)
        results = [process_rows(c) for c in chunks]
    else:
        with Pool(args.workers, initializer=init_worker, initargs=initargs) as pool:
            results = pool.map(process_rows, chunks)
    t_compute = time.perf_counter() - t1

    counts = [c for chunk_counts, _ in results for c in chunk_counts]
    stored = sum(len(near) for _, lists in results for near in lists)

    print("points:               %d" % n)
    print("radius:               %g" % args.radius)
    print("workers:              %d" % args.workers)
    print("mean neighbours:      %.2f" % (sum(counts) / n))
    print("max neighbours:       %d" % max(counts))
    print("isolated points:      %d" % sum(1 for c in counts if c == 0))
    if args.store_neighbours:
        print("neighbour entries kept: %d" % stored)
    print("--- timing (reported by the script itself) ---")
    print("load time:            %.2f s" % t_load)
    print("compute time:         %.2f s" % t_compute)
    print("total time:           %.2f s" % (t_load + t_compute))
    print("peak memory (main):   %.1f MB" % peak_memory_mb())


if __name__ == "__main__":
    main()
