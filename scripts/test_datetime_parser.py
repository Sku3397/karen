import sys
import os
from datetime import datetime, timezone, timedelta
import logging
import pytz # Added for timezone-aware test cases
import dateutil.parser

# Adjust path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import the function directly from the new utility module
    from src.datetime_utils import parse_datetime_from_details
except ImportError as e:
    print(f"Error importing datetime_utils: {e}. Make sure you are in the project root or PYTHONPATH is set.")
    sys.exit(1)

# Setup basic logging for this test script
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Use the test script's own logger
# Get the logger used by the utility function to see its debug messages
utils_logger = logging.getLogger("src.datetime_utils")
utils_logger.setLevel(logging.DEBUG)

def run_parser_tests():
    # Test cases: (date_str, time_str, description, expected_iso_utc_or_None_or_True)
    # True means qualitative check for future valid UTC datetime
    # None means parsing is expected to fail and return None
    # String means exact UTC ISO string match expected
    
    # Get current year for relative dates like "September 10"
    current_year = datetime.now().year
    next_year = current_year + 1

    test_cases = [
        # Basic relative dates & times (ET is default business_tz)
        ("tomorrow", "morning", "Test 1: Tomorrow morning (9am ET)", True),
        ("next Tuesday", "3pm", "Test 2: Next Tuesday 3pm ET", True),
        ("today", "evening", "Test 3: Today evening (6pm ET)", True),
        ("next monday", "noon", "Test 4: Next Monday noon (12pm ET)", True),
        
        # Specific dates & times
        (f"July 25th, {current_year}", "2:30 PM", f"Test 5: Specific date/time ({current_year} 2:30pm ET)", f"{current_year}-07-25T18:30:00+00:00"),
        (f"August 5, {current_year}", None, f"Test 6: Date, no time (default 9am ET, {current_year})", f"{current_year}-08-05T13:00:00+00:00"),
        (f"september 10, {current_year}", "10:00", f"Test 7: Sep 10, 10:00 (am ET, {current_year})", f"{current_year}-09-10T14:00:00+00:00"),
        (f"December 25, {current_year}", "afternoon", f"Test 8: Christmas afternoon ({current_year} 2pm ET)", f"{current_year}-12-25T19:00:00+00:00"),
        
        # Invalid / None inputs
        ("blahblah", "10am", "Test 9: Invalid date string (fuzzy might parse time)", True),
        ("tomorrow", "blahblah", "Test 10: Valid date, invalid time keyword", None),
        (None, "10am", "Test 11: No date string", None),
        (f"October 32, {current_year}", "10am", f"Test 12: Invalid day in month ({current_year})", None), # dateutil.parser.parse handles this

        # Timezone handling edge cases
        (f"March 10, {next_year}", "1:30 AM", f"Test 13: Before DST spring forward ({next_year} 1:30am ET)", f"{next_year}-03-10T05:30:00+00:00"),
        (f"November 3, {next_year}", "1:30 AM", f"Test 14: Before DST fall back ({next_year} 1:30am ET - first occurrence)", True),
        (f"{current_year}-07-20T10:00:00Z", None, f"Test 15: Input already UTC ISO string (date only, {current_year})", f"{current_year}-07-20T10:00:00+00:00"),
        (f"{current_year}-07-20", "10:00:00Z", f"Test 16: Input with UTC Z in time part ({current_year})", f"{current_year}-07-20T10:00:00+00:00"),
        (f"{current_year}-07-20T15:00:00+05:00", None, f"Test 17: Input with specific non-UTC offset (date only, {current_year})", f"{current_year}-07-20T10:00:00+00:00"),
        (f"{current_year}-07-20", "15:00:00+05:00", f"Test 18: Input with specific non-UTC offset in time part ({current_year})", f"{current_year}-07-20T10:00:00+00:00"),
        ("today", "8", "Test 19: Ambiguous time '8' (default 8am ET)", True),
        ("last monday", "10am", "Test 20: Past relative date (10am ET)", True), # Should parse to a past date
        (f"July 25, {current_year}", "2:30 PM EST", f"Test 21: Specific date/time with EST ({current_year})", f"{current_year}-07-25T18:30:00+00:00"),
        (f"July 25, {current_year}", "2:30 PM EDT", f"Test 22: Specific date/time with EDT ({current_year})", f"{current_year}-07-25T18:30:00+00:00"),
        (f"October 1, {current_year}", "midnight", f"Test 23: Midnight ({current_year} 12am ET)", f"{current_year}-10-01T04:00:00+00:00"),
    ]

    logger.info("Starting date/time parser tests...")
    passed_all = True
    failed_tests = []

    for i, (date_str, time_str, desc, expected) in enumerate(test_cases):
        test_num = i + 1
        logger.info(f"--- Test Case {test_num}: {desc} ---")
        logger.info(f"Input: date='{date_str}', time='{time_str}'")
        
        result_dt = parse_datetime_from_details(date_str, time_str, desc, business_timezone_str="America/New_York")
        
        test_passed = False
        if result_dt is None:
            if expected is None:
                logger.info(f"PASS: Correctly returned None. Output: None")
                test_passed = True
            else:
                logger.error(f"FAIL: Expected a datetime object or specific string, but got None.")
        elif expected is True: 
            logger.info(f"INFO (Qualitative Check): Got {result_dt.isoformat()}. Expected a valid UTC datetime.")
            if result_dt.tzinfo != timezone.utc and result_dt.tzinfo != pytz.utc:
                 logger.error(f"FAIL: Result datetime {result_dt.isoformat()} is not UTC. tzinfo: {result_dt.tzinfo}")
            else:
                logger.info(f"PASS (Qualitative): Result is UTC and seems valid.")
                test_passed = True
                if date_str and any(term in date_str.lower() for term in ["tomorrow", "next", "today"]):
                    if result_dt < datetime.now(pytz.utc) - timedelta(days=1):
                        logger.warning(f"WARN (Qualitative): Relative future date '{date_str}' resulted in past time: {result_dt.isoformat()}")
                elif date_str and "last" in date_str.lower():
                    if result_dt > datetime.now(pytz.utc) + timedelta(hours=1):
                         logger.warning(f"WARN (Qualitative): Relative past date '{date_str}' resulted in future time: {result_dt.isoformat()}")
        elif isinstance(expected, str):
            iso_result = result_dt.isoformat()
            expected_dt_obj = dateutil.parser.isoparse(expected) # Parse expected for direct comparison
            
            # Compare the datetime objects directly for equality (handles Z vs +00:00 diffs)
            if result_dt == expected_dt_obj:
                logger.info(f"PASS: Output '{iso_result}' is equivalent to expected '{expected}'.")
                test_passed = True
            else:
                logger.error(f"FAIL: Expected '{expected}' (parsed as {expected_dt_obj.isoformat()}), but got '{iso_result}'.")
        else:
            logger.error(f"FAIL (Test Case Error): Unexpected result type or expectation. Got {result_dt.isoformat() if result_dt else 'None'}, Expected type {type(expected)}.")
        
        if not test_passed:
            passed_all = False
            failed_tests.append(f"Test {test_num}: {desc}")
        logger.info("---")

    if passed_all:
        logger.info("All date/time parser tests passed (or passed qualitatively where applicable)!")
    else:
        logger.error(f"Some date/time parser tests FAILED. Failures: {len(failed_tests)}")
        for failed_test in failed_tests:
            logger.error(f"  - {failed_test}")

if __name__ == "__main__":
    run_parser_tests() 