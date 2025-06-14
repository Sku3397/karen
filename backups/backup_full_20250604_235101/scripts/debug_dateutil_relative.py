import dateutil.parser
from datetime import datetime
import pytz

def run_debug():
    print("--- Debugging dateutil.parser.parse for relative terms ---")

    test_strings = ["today", "tomorrow"]
    business_tz_str = "America/New_York"
    business_tz = pytz.timezone(business_tz_str)
    default_dt_aware = datetime.now(business_tz).replace(hour=0, minute=0, second=0, microsecond=0)

    for s in test_strings:
        print(f"\n--- Testing string: '{s}' ---")
        
        # Test 1: No default, no fuzzy
        try:
            parsed = dateutil.parser.parse(s)
            print(f"  1. No default, no fuzzy: {parsed.isoformat() if parsed else 'None'}")
        except Exception as e:
            print(f"  1. No default, no fuzzy: FAILED - {type(e).__name__}: {e}")

        # Test 2: No default, with fuzzy
        try:
            parsed_fuzzy_tuple = dateutil.parser.parse(s, fuzzy_with_tokens=True)
            if isinstance(parsed_fuzzy_tuple, tuple):
                parsed_fuzzy = parsed_fuzzy_tuple[0]
            else:
                parsed_fuzzy = parsed_fuzzy_tuple
            print(f"  2. No default, fuzzy:    {parsed_fuzzy.isoformat() if parsed_fuzzy else 'None'}")
        except Exception as e:
            print(f"  2. No default, fuzzy:    FAILED - {type(e).__name__}: {e}")

        # Test 3: With aware default, no fuzzy
        try:
            parsed_def = dateutil.parser.parse(s, default=default_dt_aware)
            print(f"  3. Aware default, no fuzzy: {parsed_def.isoformat() if parsed_def else 'None'}")
        except Exception as e:
            print(f"  3. Aware default, no fuzzy: FAILED - {type(e).__name__}: {e}")

        # Test 4: With aware default, with fuzzy
        try:
            parsed_def_fuzzy_tuple = dateutil.parser.parse(s, default=default_dt_aware, fuzzy_with_tokens=True)
            if isinstance(parsed_def_fuzzy_tuple, tuple):
                parsed_def_fuzzy = parsed_def_fuzzy_tuple[0]
            else:
                parsed_def_fuzzy = parsed_def_fuzzy_tuple
            print(f"  4. Aware default, fuzzy:    {parsed_def_fuzzy.isoformat() if parsed_def_fuzzy else 'None'}")
        except Exception as e:
            print(f"  4. Aware default, fuzzy:    FAILED - {type(e).__name__}: {e}")

if __name__ == "__main__":
    run_debug() 