import logging
from datetime import datetime, timedelta
from typing import Optional
import pytz
import dateutil.parser

logger = logging.getLogger(__name__)

def parse_datetime_from_details(requested_date_str: Optional[str], 
                                requested_time_str: Optional[str], 
                                service_description: str, 
                                business_timezone_str: str = "America/New_York") -> Optional[datetime]:
    """
    Parses date and time strings into a timezone-aware UTC datetime object.
    Handles relative dates, common time expressions, and explicit timezones.
    """
    if not requested_date_str:
        logger.debug(f"parse_datetime: Date string is missing. Time: '{requested_time_str}'")
        return None

    try:
        business_tz = pytz.timezone(business_timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        logger.error(f"Unknown business timezone: {business_timezone_str}. Defaulting to UTC for parsing localization.")
        business_tz = pytz.utc

    # Establish a consistent, timezone-aware default date for parsing relative terms
    default_parse_date = datetime.now(business_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    logger.debug(f"Using default_parse_date: {default_parse_date.isoformat()} for dateutil.parser")

    parsed_dt = None
    
    try:
        time_keyword_component = None
        is_time_keyword = False

        if requested_time_str:
            time_lower = requested_time_str.lower()
            if "morning" in time_lower:
                time_keyword_component = datetime(year=1, month=1, day=1, hour=9, minute=0).time()
                is_time_keyword = True
            elif "afternoon" in time_lower:
                time_keyword_component = datetime(year=1, month=1, day=1, hour=14, minute=0).time()
                is_time_keyword = True
            elif "evening" in time_lower:
                time_keyword_component = datetime(year=1, month=1, day=1, hour=18, minute=0).time()
                is_time_keyword = True
            elif "noon" in time_lower:
                time_keyword_component = datetime(year=1, month=1, day=1, hour=12, minute=0).time()
                is_time_keyword = True
            elif "midnight" in time_lower:
                time_keyword_component = datetime(year=1, month=1, day=1, hour=0, minute=0).time()
                is_time_keyword = True

        if is_time_keyword:
            logger.debug(f"Time keyword '{requested_time_str}' detected. Parsing date part: '{requested_date_str}' with fuzzy_with_tokens=True and default date.")
            parsed_dt_tuple = dateutil.parser.parse(requested_date_str, default=default_parse_date, fuzzy_with_tokens=True)
            if isinstance(parsed_dt_tuple, tuple):
                parsed_dt = parsed_dt_tuple[0]
            else:
                parsed_dt = parsed_dt_tuple
            
            if parsed_dt is None:
                 raise ValueError(f"Parsing date part '{requested_date_str}' failed before applying time keyword.")
            
            parsed_dt = parsed_dt.replace(hour=time_keyword_component.hour,
                                          minute=time_keyword_component.minute,
                                          second=0, microsecond=0)
            logger.debug(f"Applied time keyword. Intermediate parsed_dt: {parsed_dt}")
        elif requested_time_str:
            datetime_str_to_parse = f"{requested_date_str} {requested_time_str}"
            logger.debug(f"No time keyword. Parsing combined string: '{datetime_str_to_parse}' with fuzzy_with_tokens=True and default date.")
            parsed_dt_tuple = dateutil.parser.parse(datetime_str_to_parse, default=default_parse_date, fuzzy_with_tokens=True)
            if isinstance(parsed_dt_tuple, tuple):
                parsed_dt = parsed_dt_tuple[0]
            else:
                parsed_dt = parsed_dt_tuple
        else: 
            logger.debug(f"No time string provided. Parsing date part: '{requested_date_str}' with fuzzy_with_tokens=True and default date.")
            parsed_dt_tuple = dateutil.parser.parse(requested_date_str, default=default_parse_date, fuzzy_with_tokens=True)
            if isinstance(parsed_dt_tuple, tuple):
                parsed_dt = parsed_dt_tuple[0]
            else:
                parsed_dt = parsed_dt_tuple
            
            if parsed_dt is None:
                raise ValueError(f"Parsing date part '{requested_date_str}' failed when no time string was provided.")

            if parsed_dt.hour == 0 and parsed_dt.minute == 0 and parsed_dt.second == 0:
                logger.debug(f"Parsed date has midnight time. Defaulting to 9 AM business time for: {parsed_dt}")
                parsed_dt = parsed_dt.replace(hour=9, minute=0, second=0, microsecond=0)
        
        if parsed_dt is None:
            raise ValueError(f"Parsing resulted in None. Date: '{requested_date_str}', Time: '{requested_time_str}'.")

        # Timezone handling
        if parsed_dt.tzinfo is None or parsed_dt.tzinfo.utcoffset(parsed_dt) is None:
            localized_dt = business_tz.localize(parsed_dt)
            utc_dt = localized_dt.astimezone(pytz.utc)
            logger.debug(f"Localized naive '{parsed_dt}' to {business_tz.zone} ({localized_dt.isoformat()}), then converted to UTC: {utc_dt.isoformat()}")
        else:
            if parsed_dt.tzinfo == pytz.utc or parsed_dt.utcoffset() == timedelta(0):
                utc_dt = parsed_dt
                logger.debug(f"Parsed datetime is already UTC-aware: {utc_dt.isoformat()}")
            else:
                original_aware_dt_str = parsed_dt.isoformat()
                utc_dt = parsed_dt.astimezone(pytz.utc)
                logger.debug(f"Converted non-UTC aware datetime '{original_aware_dt_str}' to UTC: {utc_dt.isoformat()}")
        
        logger.info(f"Successfully parsed (original date: '{requested_date_str}', original time: '{requested_time_str}') to UTC: {utc_dt.isoformat()} (service: {service_description})")
        return utc_dt
        
    except (dateutil.parser.ParserError, ValueError, TypeError, AttributeError) as e:
        current_datetime_str_being_parsed = requested_date_str
        if not is_time_keyword and requested_time_str:
            current_datetime_str_being_parsed = f"{requested_date_str} {requested_time_str}"
        
        logger.warning(f"Could not parse. String being parsed: '{current_datetime_str_being_parsed}'. Original (date: '{requested_date_str}', time: '{requested_time_str}'). Error: {type(e).__name__}: {e}")
        return None 