def test_import_models_smoke():
    from app.models.bookmakers import Bookmaker
    from app.models.selections import Selection
    from app.models.odds import Odds
    from app.models.predictions import Prediction
    from app.models.bets import Bet

    # Rör vid något fält så modulkoden garanterat exekveras
    assert Bookmaker.__tablename__ == "bookmakers"
    assert hasattr(Selection, "selection_id")
    assert hasattr(Odds, "odds_id")
    assert hasattr(Prediction, "prediction_id")
    assert hasattr(Bet, "bet_id")
