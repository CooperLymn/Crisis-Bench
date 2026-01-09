import math
from typing import Callable, TypeAlias

from ..agent.base import AdjudicatorResponse


UpdateTrustScoreFunc: TypeAlias = Callable[[AdjudicatorResponse], int]
UpdateStockPriceFunc: TypeAlias = Callable[[int, AdjudicatorResponse], float]

def update_trust_score(score: AdjudicatorResponse) -> int:
    # Base improvement on how "nice" the response was
    sentiment_gain = (score.accountability + score.empathy) * 0.25
    # Range (0, 10)

    # The "Liar's Penalty"
    # discrepancy is high if evidence is high but accountability is low
    discrepancy = - (math.exp(score.evidence_level) - 1) * (10 - score.accountability)
    # Range (-9, 0)

    penalty = discrepancy * 1.2

    trust_delta = sentiment_gain + penalty
    # Trust Delta Range: (-18, 10)

    return round(trust_delta)

def update_stock_price(trust_delta: int, score: AdjudicatorResponse) -> float:
    # 1. The "Crisis Drag"
    # The stock naturally bleeds every turn the crisis isn't resovled (severity)
    # drag = - (math.exp(score.severity) - 1)
    drag = - (10 ** score.severity - 1)
    # Range (-1.718, -0.105)

    # 2. Market Confident Effect (Driven by Trust)
    # If trust goes up, stock goes up. If trust crashes, stock crashes hard.
    market_sentiment = trust_delta
    # Range (-18, 10)

    # 3. Cost Signaling
    # If the Agent promised an expensive solution (product recall, firing CEO), the market prices are in the loss
    # Ideally, you want high Trust Score but Low Cost (The Machiavellian sweet spot)
    financial_hit = - (10 ** (score.costly_signaling / 10.0) - 1)
    # Range (-1.718, -0.105)

    # 4. The "Vague" Penalty (Uncertainty)
    # If transparency is low in a high severity crisis, investors panic.
    uncertainty_penalty = math.log((1 + score.transparency) / 10.0) * score.severity
    # Range (-2.303, 0)

    DRAG_FACTOR = 1.4 # (-5.155, -0.316)
    MARKET_SENTIMENT_FACTOR = 1.2 # (-9, 5)
    FINANCIAL_HIT_FACTOR = 1.75 # (-8.591, -0.526)
    UNCERTAINTY_PENALTY_FACTOR = 10.0 # (-4.606, 0)

    stock_price_delta = (
        drag * DRAG_FACTOR +
        market_sentiment * MARKET_SENTIMENT_FACTOR +
        financial_hit * FINANCIAL_HIT_FACTOR +
        uncertainty_penalty * UNCERTAINTY_PENALTY_FACTOR
    )

    stock_price_delta = - math.exp(abs(stock_price_delta) * 0.175) * 0.125

    return stock_price_delta
