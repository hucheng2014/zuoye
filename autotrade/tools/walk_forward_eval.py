from __future__ import annotations

import argparse
import copy
import csv
import json
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean


PROJECT_DIR = Path(__file__).resolve().parents[1]
USER_DATA_DIR = PROJECT_DIR / "user_data"
BASE_CONFIG_PATH = USER_DATA_DIR / "config.json"
RESULTS_ROOT = USER_DATA_DIR / "backtest_results" / "walk_forward"
TEMP_CONFIG_PATH = USER_DATA_DIR / "config.walkforward.tmp.json"


@dataclass
class EvalWindow:
    start: date
    end: date

    @property
    def timerange(self) -> str:
        return f"{self.start:%Y%m%d}-{self.end:%Y%m%d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Walk-forward evaluator for the PureRL full-auto bot.")
    parser.add_argument("--start", required=True, help="Window start date, e.g. 2025-10-01")
    parser.add_argument("--end", required=True, help="Window end date, e.g. 2026-03-01")
    parser.add_argument("--step-days", type=int, default=7, help="Walk-forward test window length.")
    parser.add_argument("--seeds", nargs="+", type=int, default=[7, 21, 42])
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=["scratch", "continual"],
        default=["scratch", "continual"],
    )
    parser.add_argument("--max-windows", type=int, default=0, help="0 means all windows.")
    parser.add_argument(
        "--pairs",
        nargs="*",
        default=[],
        help="Optional subset of pairs for faster evaluation.",
    )
    parser.add_argument(
        "--skip-bias-checks",
        action="store_true",
        help="Skip recursive-analysis and lookahead-analysis.",
    )
    parser.add_argument(
        "--run-label",
        default="",
        help="Optional label to isolate eval model identifiers. Defaults to a timestamp.",
    )
    return parser.parse_args()


def build_windows(start: date, end: date, step_days: int, max_windows: int) -> list[EvalWindow]:
    windows: list[EvalWindow] = []
    current = start
    while current < end:
        window_end = min(current + timedelta(days=step_days), end)
        windows.append(EvalWindow(start=current, end=window_end))
        current = window_end
        if max_windows and len(windows) >= max_windows:
            break
    return windows


def load_base_config() -> dict:
    return json.loads(BASE_CONFIG_PATH.read_text(encoding="utf-8"))


def build_eval_config(base_config: dict, mode: str, seed: int, identifier: str) -> dict:
    config = copy.deepcopy(base_config)
    config["dry_run"] = True
    config["api_server"]["enabled"] = False
    config["telegram"]["enabled"] = False
    config["freqai"]["continual_learning"] = mode == "continual"
    config["freqai"]["identifier"] = identifier
    config["freqai"]["save_backtest_models"] = True
    # Freqtrade RL backtesting does not support live-only state augmentation.
    config["freqai"]["rl_config"]["add_state_info"] = False
    config["freqai"]["model_training_parameters"]["seed"] = seed
    return config


def run_command(command: list[str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write("$ " + " ".join(command) + "\n\n")
        process = subprocess.run(
            command,
            cwd=PROJECT_DIR,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return process.returncode


def latest_result_zip(directory: Path) -> Path | None:
    files = sorted(directory.glob("backtest-result-*.zip"))
    return files[-1] if files else None


def parse_backtest_summary(zip_path: Path, strategy_name: str) -> dict[str, float]:
    with zipfile.ZipFile(zip_path) as archive:
        json_name = next(name for name in archive.namelist() if name.endswith(".json") and "_config" not in name)
        payload = json.loads(archive.read(json_name).decode("utf-8"))
        strategy_payload = payload["strategy"][strategy_name]
        return {
            "profit_total": strategy_payload.get("profit_total", 0.0),
            "profit_total_abs": strategy_payload.get("profit_total_abs", 0.0),
            "winrate": strategy_payload.get("winrate", 0.0),
            "max_drawdown_account": strategy_payload.get("max_drawdown_account", 0.0),
            "profit_factor": strategy_payload.get("profit_factor", 0.0),
            "sharpe": strategy_payload.get("sharpe", 0.0),
            "sortino": strategy_payload.get("sortino", 0.0),
            "expectancy_ratio": strategy_payload.get("expectancy_ratio", 0.0),
            "total_trades": strategy_payload.get("total_trades", 0.0),
            "trades_per_day": strategy_payload.get("trades_per_day", 0.0),
        }


def write_temp_config(config: dict) -> None:
    TEMP_CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def to_container_path(path: Path) -> str:
    relative_path = path.resolve().relative_to(PROJECT_DIR.resolve())
    return (Path("/freqtrade") / relative_path).as_posix()


def run_bias_checks(timerange: str, pairs: list[str], mode: str, seed: int, output_dir: Path) -> None:
    pair_args = ["-p", *pairs] if pairs else []
    recursive_log = output_dir / f"{mode}_seed{seed}_recursive.log"
    lookahead_log = output_dir / f"{mode}_seed{seed}_lookahead.log"
    lookahead_csv = output_dir / f"{mode}_seed{seed}_lookahead.csv"

    recursive_cmd = [
        "docker",
        "compose",
        "run",
        "--rm",
        "freqtrade",
        "recursive-analysis",
        "--config",
        "/freqtrade/user_data/config.walkforward.tmp.json",
        "--strategy",
        "PureRL_FullAuto",
        "--freqaimodel",
        "MyRLEnv_FullAuto",
        "--timerange",
        timerange,
        "--startup-candle",
        "600",
        "900",
        "1200",
        *pair_args,
    ]
    lookahead_cmd = [
        "docker",
        "compose",
        "run",
        "--rm",
        "freqtrade",
        "lookahead-analysis",
        "--config",
        "/freqtrade/user_data/config.walkforward.tmp.json",
        "--strategy",
        "PureRL_FullAuto",
        "--freqaimodel",
        "MyRLEnv_FullAuto",
        "--timerange",
        timerange,
        "--lookahead-analysis-exportfilename",
        to_container_path(lookahead_csv),
        *pair_args,
    ]

    run_command(recursive_cmd, recursive_log)
    run_command(lookahead_cmd, lookahead_log)


def aggregate(rows: list[dict]) -> list[dict]:
    output: list[dict] = []
    grouped: dict[tuple[str, int], list[dict]] = {}
    for row in rows:
        if row["status"] != "ok":
            continue
        grouped.setdefault((row["mode"], row["seed"]), []).append(row)

    for (mode, seed), group in grouped.items():
        output.append(
            {
                "mode": mode,
                "seed": seed,
                "windows": len(group),
                "avg_profit_total": mean(item["profit_total"] for item in group),
                "avg_winrate": mean(item["winrate"] for item in group),
                "avg_max_drawdown_account": mean(item["max_drawdown_account"] for item in group),
                "avg_profit_factor": mean(item["profit_factor"] for item in group),
                "avg_sharpe": mean(item["sharpe"] for item in group),
                "avg_sortino": mean(item["sortino"] for item in group),
                "avg_expectancy_ratio": mean(item["expectancy_ratio"] for item in group),
                "avg_total_trades": mean(item["total_trades"] for item in group),
                "avg_trades_per_day": mean(item["trades_per_day"] for item in group),
            }
        )
    return output


def main() -> int:
    args = parse_args()
    start = datetime.fromisoformat(args.start).date()
    end = datetime.fromisoformat(args.end).date()
    run_label = args.run_label.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    windows = build_windows(start, end, args.step_days, args.max_windows)
    if not windows:
        print("No evaluation windows were generated.", file=sys.stderr)
        return 1

    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    base_config = load_base_config()
    identifier_prefix = base_config.get("freqai", {}).get("identifier", "pure_rl_fullauto_eval")
    rows: list[dict] = []

    for mode in args.modes:
        for seed in args.seeds:
            mode_root = RESULTS_ROOT / f"{mode}_seed{seed}"
            mode_root.mkdir(parents=True, exist_ok=True)
            base_identifier = f"{identifier_prefix}_wf_{run_label}_{mode}_seed{seed}"

            for index, window in enumerate(windows):
                identifier = (
                    base_identifier
                    if mode == "continual"
                    else f"{base_identifier}_window{index:02d}"
                )
                run_name = f"{mode}_seed{seed}_window{index:02d}_{window.timerange}"
                run_root = mode_root / run_name
                if run_root.exists():
                    shutil.rmtree(run_root)
                run_root.mkdir(parents=True, exist_ok=True)

                config = build_eval_config(base_config, mode, seed, identifier)
                if args.pairs:
                    config["exchange"]["pair_whitelist"] = args.pairs
                write_temp_config(config)

                if index == 0 and not args.skip_bias_checks:
                    run_bias_checks(window.timerange, args.pairs, mode, seed, mode_root)

                backtest_cmd = [
                    "docker",
                    "compose",
                    "run",
                    "--rm",
                    "freqtrade",
                    "backtesting",
                    "--config",
                    "/freqtrade/user_data/config.walkforward.tmp.json",
                    "--strategy",
                    "PureRL_FullAuto",
                    "--freqaimodel",
                    "MyRLEnv_FullAuto",
                    "--timerange",
                    window.timerange,
                    "--cache",
                    "none",
                    "--export",
                    "trades",
                    "--backtest-directory",
                    to_container_path(run_root),
                ]
                if args.pairs:
                    backtest_cmd.extend(["-p", *args.pairs])

                log_path = run_root / "backtest.log"
                return_code = run_command(backtest_cmd, log_path)

                row = {
                    "mode": mode,
                    "seed": seed,
                    "timerange": window.timerange,
                    "status": "ok" if return_code == 0 else "failed",
                    "result_zip": "",
                    "profit_total": 0.0,
                    "profit_total_abs": 0.0,
                    "winrate": 0.0,
                    "max_drawdown_account": 0.0,
                    "profit_factor": 0.0,
                    "sharpe": 0.0,
                    "sortino": 0.0,
                    "expectancy_ratio": 0.0,
                    "total_trades": 0.0,
                    "trades_per_day": 0.0,
                }

                result_zip = latest_result_zip(run_root)
                if return_code == 0 and result_zip:
                    row["result_zip"] = str(result_zip)
                    row.update(parse_backtest_summary(result_zip, "PureRL_FullAuto"))

                rows.append(row)

    TEMP_CONFIG_PATH.unlink(missing_ok=True)

    raw_csv = RESULTS_ROOT / "walk_forward_raw.csv"
    with raw_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = aggregate(rows)
    summary_json = RESULTS_ROOT / "walk_forward_summary.json"
    summary_json.write_text(json.dumps(summary_rows, indent=2), encoding="utf-8")

    print(f"Raw results: {raw_csv}")
    print(f"Summary: {summary_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
