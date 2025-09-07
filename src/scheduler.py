from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from tasks.market_scanner import find_common_high_volume_futures, write_candidates


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def job_scan() -> None:
    logging.info("Starting market scan for common USDT futures >= $300k volume on both exchanges")
    try:
        candidates = find_common_high_volume_futures()
        write_candidates("data/candidates.json", candidates)
        logging.info("Scan complete: %d candidates saved", len(candidates))
    except Exception as exc:  # noqa: BLE001
        logging.exception("Scan failed: %s", exc)


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    # Every 10 hours
    scheduler.add_job(job_scan, "interval", hours=10, next_run_time=datetime.now())
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    sched = start_scheduler()
    try:
        import time

        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        sched.shutdown()


