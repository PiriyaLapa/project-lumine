import sys
import os

# Must be set before any app module is imported so config.py does not raise.
os.environ.setdefault("SECRET_KEY", "test-only-secret-not-for-production")

# Make 'app' importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
