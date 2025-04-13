def clean_currency_pair(raw_pair):
    """
    Cleans and validates a currency pair string.
    Returns a standardized 'USD/EUR' format or None if invalid.
    """
    import re
    if not raw_pair:
        return None

    raw_pair = re.sub(r'[^a-zA-Z]', ' ', raw_pair.strip())  # Replace dots, dashes, etc. with space
    parts = raw_pair.upper().split()
    parts = [p for p in parts if p.isalpha()]

    if len(parts) == 2:
        return f"{parts[0]}/{parts[1]}"
    return None
