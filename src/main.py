def main() -> None:
    from scheduler import start_scheduler

    start_scheduler()
    print("Scheduler started. Press Ctrl+C to stop.")
    try:
        import time

        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()


