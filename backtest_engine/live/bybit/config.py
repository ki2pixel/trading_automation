import os

class BybitConfig:
    """Configuration loader for the Bybit API integration."""

    def __init__(self, dotenv_path: str = None):
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
                self.dotenv_path = "/home/kidpixel/trading_automation_v2/.env"
        else:
            self.dotenv_path = dotenv_path

        self._load_dotenv()
        
        self.api_key = os.getenv("BYBIT_API_KEY")
        self.api_secret = os.getenv("BYBIT_API_SECRET")
        self.env = os.getenv("BYBIT_ENV", "testnet").lower()
        self.base_currency = os.getenv("BYBIT_BASE_CURRENCY", "USDC").upper()
        
        self.base_url = os.getenv("BYBIT_BASE_URL")
        if not self.base_url:
            if self.env == "live":
                self.base_url = "https://api.bybit.com"
            else:
                self.base_url = "https://api-demo.bybit.com"

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
        """Validates configuration."""
        if not self.api_key or not self.api_secret:
            print("[BybitConfig] WARNING: Bybit API Key or Secret is missing. Private signed endpoints will fail, but public endpoints (price ingestion) will work.")
