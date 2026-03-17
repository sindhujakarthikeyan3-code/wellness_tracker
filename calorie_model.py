# calorie_model.py

def predict_calories(age, height, weight, steps, sleep):
    """
    Production-safe calorie prediction logic
    Converts all Decimal values to float
    """

    # Convert all values to float (important for PostgreSQL Decimal types)
    age = float(age)
    height = float(height)
    weight = float(weight)
    steps = float(steps)
    sleep = float(sleep)

    # BMR calculation (Mifflin-St Jeor inspired)
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5

    # Activity burn from steps
    activity_burn = steps * 0.04

    # Sleep recovery factor
    sleep_factor = sleep * 5

    predicted_calories = bmr + activity_burn + sleep_factor

    return round(predicted_calories, 2)