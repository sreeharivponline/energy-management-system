from prophet import Prophet # type: ignore
import pandas as pd
from database import EnergyData

def generate_user_predictions(user_id):
    data = EnergyData.query.filter_by(user_id=user_id).all()
    df = pd.DataFrame([(d.date, d.consumption) for d in data], columns=['ds', 'y'])

    if len(df) < 5:  # Prophet needs enough historical cycles to make decent forecasts
        print(f"[DEBUG] Not enough billing records: {len(df)}")
        return None

    df['ds'] = pd.to_datetime(df['ds'])
    df = df.sort_values('ds')

    try:
        model = Prophet()
        model.fit(df)

        # Forecast next 60 days (1 billing cycle)
        future = model.make_future_dataframe(periods=60)
        forecast = model.predict(future)

        # Take the last 60 days (next 2 months)
        prediction = forecast[['ds', 'yhat']].tail(60)
        return prediction.to_dict('records')

    except Exception as e:
        print(f"[Prediction Error] User {user_id}: {str(e)}")
        return None
