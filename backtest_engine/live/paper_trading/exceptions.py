class PaperTradingException(Exception):
    """Base exception for all paper and live trading operations."""
    pass


class SignalExecutionError(PaperTradingException):
    """Raised when signal processing or order execution fails."""
    pass


class PortfolioUpdateError(PaperTradingException):
    """Raised when portfolio state updates, balance syncs, or NAV calculations fail."""
    pass
