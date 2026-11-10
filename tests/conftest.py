import os

# Must be set before `import app` so startup cache warmers skip live yfinance calls.
os.environ.setdefault("GCG_SKIP_WARM", "1")
