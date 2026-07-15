import os

class Trading212Config:
    """Configuration loader for the Trading 212 API integration."""

    def __init__(self, dotenv_path: str = None, env: str = None):
        # Try to load using python-dotenv if available
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        if dotenv_path is None:
            if os.path.exists(".env"):
                self.dotenv_path = ".env"
            else:
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                self.dotenv_path = os.path.join(project_root, ".env")
        else:
            self.dotenv_path = dotenv_path

        self._load_dotenv()

        if env is not None:
            self.env = env.lower()
        else:
            self.env = os.getenv("T212_ENV", "demo").lower()

        if self.env == "live":
            self.api_key_id = os.getenv("T212_LIVE_API_KEY_ID") or os.getenv("T212_API_KEY_ID")
            self.api_secret = os.getenv("T212_LIVE_API_SECRET") or os.getenv("T212_API_SECRET")
            self.base_url = "https://live.trading212.com"
        else:
            self.api_key_id = os.getenv("T212_DEMO_API_KEY_ID") or os.getenv("T212_API_KEY_ID")
            self.api_secret = os.getenv("T212_DEMO_API_SECRET") or os.getenv("T212_API_SECRET")
            self.base_url = "https://demo.trading212.com"

        # Try fallbacks for single account keys if any
        if not self.api_key_id:
            self.api_key_id = os.getenv("T212_API_KEY")

    def _load_dotenv(self) -> None:
        """Helper to read .env file and set environment variables if not already set."""
        if os.path.exists(self.dotenv_path):
            with open(self.dotenv_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if k not in os.environ:
                            os.environ[k] = v

    def validate(self) -> None:
        """Validates that credentials are set."""
        if not self.api_key_id or not self.api_secret:
            raise ValueError(
                "Missing Trading 212 credentials. Ensure T212_API_KEY_ID and "
                "T212_API_SECRET are set in environment or .env file."
            )

        # Failsafe check to prevent environment mismatch
        import hashlib
        # Hash api_secret if configured, else api_key_id
        key_to_hash = self.api_secret or self.api_key_id
        key_hash = hashlib.sha256(key_to_hash.encode("utf-8")).hexdigest()
        expected_live_hash = os.getenv("EXPECTED_T212_LIVE_KEY_HASH")
        expected_demo_hash = os.getenv("EXPECTED_T212_DEMO_KEY_HASH")

        if self.env == "live":
            if not expected_live_hash:
                raise ValueError("[Failsafe] CRITICAL: EXPECTED_T212_LIVE_KEY_HASH is not set in a Live environment! This is strictly forbidden.")
            if expected_demo_hash and key_hash == expected_demo_hash:
                raise ValueError("[Failsafe] CRITICAL: Trading 212 Demo API key/secret detected in Live environment! Shutting down immediately.")
            if key_hash != expected_live_hash:
                raise ValueError("[Failsafe] CRITICAL: Trading 212 API key/secret does not match EXPECTED_T212_LIVE_KEY_HASH in Live environment! Shutting down immediately.")
        else:
            if not expected_demo_hash:
                raise ValueError("[Failsafe] CRITICAL: EXPECTED_T212_DEMO_KEY_HASH is not set in a Demo/Testnet environment! This is strictly forbidden.")
            if expected_live_hash and key_hash == expected_live_hash:
                raise ValueError("[Failsafe] CRITICAL: Trading 212 Live API key/secret detected in Demo/Testnet environment! Shutting down immediately.")
            if key_hash != expected_demo_hash:
                raise ValueError("[Failsafe] CRITICAL: Trading 212 API key/secret does not match EXPECTED_T212_DEMO_KEY_HASH in Demo/Testnet environment! Shutting down immediately.")
