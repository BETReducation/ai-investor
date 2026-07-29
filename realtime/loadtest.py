"""Load test for realtime/'s SSE endpoints (docs/scaling-plan.md, Workstream 6).

Opens N concurrent SSE connections against a running realtime/ service and
reports connect latency, time-to-first-message, drop/error counts, and this
process's own memory footprint. This is the client side only — it tells you
whether the realtime/ service (and whatever's in front of it) can hold N
connections and keep delivering, not whether the *server* stayed healthy
doing it. Watch the server's own CPU/memory/connection-count (Railway
metrics, or `docker stats` locally) alongside this run.

Requires a real logged-in session cookie from the main Flask app, since
/stream/prices and /stream/signals both require auth — get one by logging
in through the browser (or curl -i .../api/login) and copying the `session`
cookie value.

Not run against a live deployment yet — nothing is deployed (see
docs/scaling-plan.md's Status section). Use this against a local run first:

    # terminal 1 — main app, with REDIS_URL set
    python app.py

    # terminal 2 — realtime service
    cd realtime && uvicorn main:app --port 8001

    # terminal 3
    pip install aiohttp
    python realtime/loadtest.py --base-url http://localhost:8001 \\
        --cookie "$SESSION_COOKIE" --symbol EURUSD=X --connections 200

Needs aiohttp (`pip install aiohttp`) — deliberately not added to
requirements.txt, since this is a dev-only tool, not something the deployed
service needs at runtime.
"""

import argparse
import asyncio
import os
import statistics
import time

try:
    import aiohttp
except ImportError:
    raise SystemExit("This script needs aiohttp: pip install aiohttp")


async def _one_connection(
    session: "aiohttp.ClientSession",
    url: str,
    hold_seconds: float,
    results: dict,
    conn_id: int,
) -> None:
    connect_start = time.monotonic()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=hold_seconds + 15)) as resp:
            if resp.status != 200:
                results["errors"].append(f"conn {conn_id}: HTTP {resp.status}")
                return
            connected_at = time.monotonic()
            results["connect_seconds"].append(connected_at - connect_start)

            first_message_at = None
            message_count = 0
            deadline = connected_at + hold_seconds
            async for raw_line in resp.content:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line.startswith("data:"):
                    message_count += 1
                    if first_message_at is None:
                        first_message_at = time.monotonic()
                        results["time_to_first_message_seconds"].append(first_message_at - connected_at)
                if time.monotonic() >= deadline:
                    break
            results["message_counts"].append(message_count)
    except asyncio.TimeoutError:
        results["errors"].append(f"conn {conn_id}: timeout")
    except Exception as e:
        results["errors"].append(f"conn {conn_id}: {type(e).__name__}: {e}")


async def run(args: argparse.Namespace) -> None:
    url = f"{args.base_url}/stream/{args.stream}?symbol={args.symbol}"
    if args.stream == "signals":
        url += f"&period={args.period}&interval={args.interval}"

    results = {
        "connect_seconds": [],
        "time_to_first_message_seconds": [],
        "message_counts": [],
        "errors": [],
    }

    connector = aiohttp.TCPConnector(limit=0)  # no artificial cap — we want to see the real ceiling
    cookies = {"session": args.cookie} if args.cookie else {}

    async with aiohttp.ClientSession(connector=connector, cookies=cookies) as session:
        started_at = time.monotonic()
        tasks = []
        for i in range(args.connections):
            tasks.append(asyncio.create_task(_one_connection(session, url, args.hold_seconds, results, i)))
            if args.ramp_up_seconds and args.connections > 1:
                await asyncio.sleep(args.ramp_up_seconds / args.connections)
        await asyncio.gather(*tasks)
        total_seconds = time.monotonic() - started_at

    _report(args, results, total_seconds)


def _report(args: argparse.Namespace, results: dict, total_seconds: float) -> None:
    ok = args.connections - len(results["errors"])
    print(f"\n=== {args.stream} load test: {args.connections} connections, {args.hold_seconds}s hold ===")
    print(f"Total wall time: {total_seconds:.1f}s")
    print(f"Succeeded: {ok}/{args.connections}  Failed: {len(results['errors'])}")
    if results["connect_seconds"]:
        cs = sorted(results["connect_seconds"])
        print(f"Connect latency  p50={cs[len(cs)//2]:.3f}s  p95={cs[int(len(cs)*0.95)]:.3f}s  max={cs[-1]:.3f}s")
    if results["time_to_first_message_seconds"]:
        fm = sorted(results["time_to_first_message_seconds"])
        print(f"Time-to-first-msg p50={fm[len(fm)//2]:.3f}s  p95={fm[int(len(fm)*0.95)]:.3f}s  max={fm[-1]:.3f}s")
    if results["message_counts"]:
        print(f"Messages/conn avg={statistics.mean(results['message_counts']):.1f}  "
              f"min={min(results['message_counts'])}  max={max(results['message_counts'])}")
    if results["errors"]:
        print(f"\nFirst {min(10, len(results['errors']))} errors:")
        for e in results["errors"][:10]:
            print(" -", e)

    try:
        import resource
        rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Linux: KB: /1024=MB
        print(f"\nThis client process's peak RSS: ~{rss_mb:.0f} MB "
              f"(client-side only — check the realtime/ service's own memory separately)")
    except ImportError:
        pass  # resource module is POSIX-only; skip silently on Windows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", required=True, help="e.g. http://localhost:8001")
    parser.add_argument("--cookie", default=os.environ.get("SESSION_COOKIE", ""),
                         help="main app's 'session' cookie value (or set SESSION_COOKIE env var)")
    parser.add_argument("--stream", choices=["prices", "signals"], default="prices")
    parser.add_argument("--symbol", default="EURUSD=X")
    parser.add_argument("--period", default="5d", help="only used for --stream signals")
    parser.add_argument("--interval", default="5m", help="only used for --stream signals")
    parser.add_argument("--connections", type=int, default=100)
    parser.add_argument("--hold-seconds", type=float, default=30.0,
                         help="how long each connection stays open before this script closes it")
    parser.add_argument("--ramp-up-seconds", type=float, default=0.0,
                         help="spread connection starts over this many seconds instead of firing all at once")
    args = parser.parse_args()

    if not args.cookie:
        raise SystemExit("Need a session cookie: --cookie or SESSION_COOKIE env var (log into the main app "
                          "and copy its 'session' cookie value)")

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
