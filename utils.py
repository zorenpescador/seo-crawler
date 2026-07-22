import pandas as pd


def sanitize_for_display(df: pd.DataFrame, drop_columns=None, max_text_chars: int = 8000) -> pd.DataFrame:
    """Return a DataFrame safe for Streamlit display and export.

    Large text fields such as full HTML are removed or shortened to avoid
    pandas truncation warnings and oversized UI payloads.
    """
    display_df = df.copy()
    drop_columns = set(drop_columns or [])

    for column in list(drop_columns):
        if column in display_df.columns:
            display_df = display_df.drop(columns=[column])

    for column in display_df.columns:
        if not pd.api.types.is_object_dtype(display_df[column]):
            continue

        def _shorten(value):
            if isinstance(value, str) and len(value) > max_text_chars:
                return value[:max_text_chars] + "… [truncated]"
            return value

        display_df[column] = display_df[column].apply(_shorten)

    return display_df
