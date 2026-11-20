#!/usr/bin/env python3
"""Plot the detailed SCReAM simulator log.

The simulator writes one row when a packet is acknowledged and it is either
the last packet of a frame, CE-marked, or detailed logging is enabled.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Sequence


LOG_COLUMNS = (
    "time",
    "queue_delay",
    "rtt",
    "cwnd",
    "bytes_in_flight",
    "fast_increase",
    "total_tx_rate",
    "stream_id",
    "sequence_number",
    "newly_acked_bytes",
    "newly_ce_bytes",
    "rtp_rate",
    "stream_tx_rate",
    "acked_rate",
    "lost_rate",
    "ce_rate",
    "marker",
    "target_bitrate",
    "rtp_queue_delay",
    "cwnd_i",
    "latency_cwnd_scale",
)


def load_log(path: Path) -> dict[str, list[float]]:
    """Load the simulator's 21-column CSV-like log."""
    data = {column: [] for column in LOG_COLUMNS}
    with path.open(newline="") as log_file:
        reader = csv.reader(log_file, skipinitialspace=True)
        for line_number, row in enumerate(reader, start=1):
            if not row or all(not value.strip() for value in row):
                continue
            if len(row) != len(LOG_COLUMNS):
                raise ValueError(
                    f"{path}:{line_number}: expected {len(LOG_COLUMNS)} columns, "
                    f"found {len(row)}"
                )
            try:
                values = [float(value) for value in row]
            except ValueError as error:
                raise ValueError(
                    f"{path}:{line_number}: contains a non-numeric value"
                ) from error
            for column, value in zip(LOG_COLUMNS, values):
                data[column].append(value)

    if not data["time"]:
        raise ValueError(f"{path}: contains no data rows")
    return data


def plot_log(data: dict[str, list[float]], output: Path | None, show: bool) -> None:
    """Create a SCReAM overview plot and optionally save/display it."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise SystemExit(
            "matplotlib is required; install it with: python3 -m pip install matplotlib"
        ) from error

    time = data["time"]
    rate_scale = 1_000_000
    byte_rate_scale = 1_000

    figure, axes = plt.subplots(
        5,
        1,
        figsize=(12, 12),
        sharex=True,
        constrained_layout=True,
    )
    figure.suptitle("SCReAM V2 simulation")

    axes[0].plot(time, [value / rate_scale for value in data["target_bitrate"]],
                 label="Target bitrate")
    axes[0].plot(time, [value / rate_scale for value in data["stream_tx_rate"]],
                 label="Stream transmit rate")
    axes[0].plot(time, [value / rate_scale for value in data["acked_rate"]],
                 label="ACKed rate")
    axes[0].plot(time, [value / rate_scale for value in data["rtp_rate"]],
                 label="RTP rate", alpha=0.7)
    axes[0].set_ylabel("Rate [Mbps]")
    axes[0].set_title("Throughput and target bitrate")
    axes[0].legend(loc="upper left", ncol=4)
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(time, [value / byte_rate_scale for value in data["cwnd"]],
                 label="CWND")
    axes[1].plot(time, [value / byte_rate_scale for value in data["bytes_in_flight"]],
                 label="Bytes in flight")
    axes[1].plot(time, [value / byte_rate_scale for value in data["cwnd_i"]],
                 label="CWND reference", alpha=0.8)
    axes[1].set_ylabel("Bytes [kB]")
    axes[1].set_title("Congestion window")
    axes[1].legend(loc="upper left")
    axes[1].grid(True, alpha=0.25)

    axes[2].plot(time, [value * 1_000 for value in data["queue_delay"]],
                 label="Estimated network queue delay")
    axes[2].plot(time, [value * 1_000 for value in data["rtt"]],
                 label="RTT")
    axes[2].set_ylabel("Delay [ms]")
    axes[2].set_title("Network delay")
    axes[2].legend(loc="upper left")
    axes[2].grid(True, alpha=0.25)

    axes[3].plot(time, [value * 1_000 for value in data["rtp_queue_delay"]],
                 label="RTP queue delay")
    axes[3].set_ylabel("Delay [ms]")
    axes[3].set_title("Encoder/RTP queue")
    axes[3].legend(loc="upper left")
    axes[3].grid(True, alpha=0.25)

    axes[4].plot(time, [value / rate_scale for value in data["lost_rate"]],
                 label="Lost rate")
    axes[4].plot(time, [value / rate_scale for value in data["ce_rate"]],
                 label="CE-marked rate")
    axes[4].set_ylabel("Rate [Mbps]")
    axes[4].set_xlabel("Simulation time [s]")
    axes[4].set_title("Loss and congestion marking")
    axes[4].legend(loc="upper left")
    axes[4].grid(True, alpha=0.25)

    if output is not None:
        figure.savefig(output, dpi=150)
        print(f"Saved plot to {output}")
    if show:
        plt.show()
    plt.close(figure)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "log",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("log.txt"),
        help="SCReAM log file (default: log.txt next to this script)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output image path, for example scream_plot.png",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="display the plot interactively in addition to saving it",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    data = load_log(args.log)
    output = args.output
    if output is None and not args.show:
        output = args.log.with_name(f"{args.log.stem}_plot.png")
    plot_log(data, output, args.show)


if __name__ == "__main__":
    main()