from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardViewModel:
    total_matches: int
    wins: int
    losses: int
    win_rate: float
