import pandas as pd
from pymanifold import Session

from .models import PredictionMarket


TOP_N_MARKETS = 3
MIN_BETTORS = 25
LOOKBACK_WEEKS = 1


def get_recently_closed_markets(
    n_markets: int = TOP_N_MARKETS, lookback_weeks: int = LOOKBACK_WEEKS
) -> list[PredictionMarket]:
    """
    Get the most recently closed prediction markets. Perform some basic to get
    the markets with greatest trading volume and decent number of unique bettors.
    """
    try:
        search_markets = Session("/search-markets")
        params = {"sort": "resolve-date", "limit": "1000"}
        response = search_markets.execute(params=params)
    except Exception as e:
        raise Exception(
            f"An error occurred while searching for prediction markets: {e}"
        )

    df = pd.DataFrame(response)

    df["marketId"] = df.id

    df = df[df["outcomeType"] == "BINARY"]

    df = df[df["uniqueBettorCount"] > MIN_BETTORS]

    # handle datetimes outside the acceptable range
    df["closeTime"] = pd.to_datetime(df["closeTime"], unit="ms", errors="coerce")

    df["createdTime"] = pd.to_datetime(df["createdTime"], unit="ms")
    df["closeTime"] = pd.to_datetime(df["closeTime"], unit="ms")

    time_diff = pd.Timestamp.now() - pd.Timedelta(weeks=lookback_weeks)

    df = df[df["closeTime"] > time_diff]

    # unsophisticated way of getting the most "active" markets
    df = df.sort_values("volume", ascending=False).head(100)
    df = df.sort_values("uniqueBettorCount", ascending=False)
    df = df.head(n_markets)

    return [get_market_details(market_id) for market_id in df["marketId"]]


def get_market_details(market_id: str) -> PredictionMarket:
    """
    Get the details of a prediction market.
    """
    try:
        market = Session("/market/[marketId]")
        response = market.execute(url_params={"marketId": market_id})
    except Exception as e:
        raise Exception(f"An error occurred while getting the market details: {e}")

    return PredictionMarket(
        id=market_id,
        question=response["question"],
        description=response["textDescription"],
        categories=response["groupSlugs"],
        outcome_type=response["outcomeType"],
        probability=response["probability"],
    )
