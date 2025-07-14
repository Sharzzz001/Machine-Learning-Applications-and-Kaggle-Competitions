Calendar =
ADDCOLUMNS (
    CALENDAR ( DATE(2024, 1, 1), DATE(2026, 12, 31) ),  -- Adjust date range as needed
    "Year", YEAR([Date]),
    "Month", MONTH([Date]),
    "MonthName", FORMAT([Date], "MMM"),
    "Day", DAY([Date]),
    "Weekday", WEEKDAY([Date], 2),  -- 1=Monday, 7=Sunday
    "IsWeekend", IF(WEEKDAY([Date], 2) >= 6, TRUE(), FALSE())
)