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

Calendar =
ADDCOLUMNS (
    CALENDAR ( DATE(2024, 1, 1), DATE(2026, 12, 31) ),
    "Year", YEAR([Date]),
    "Month", MONTH([Date]),
    "MonthName", FORMAT([Date], "MMM"),
    "Day", DAY([Date]),
    "Weekday", WEEKDAY([Date], 2),
    "IsWeekend", IF(WEEKDAY([Date], 2) >= 6, TRUE(), FALSE()),
    "IsHoliday", IF([Date] IN VALUES('PublicHolidays'[Date]), TRUE(), FALSE()),
    "IsWorkingDay", IF(WEEKDAY([Date], 2) < 6 && NOT([Date] IN VALUES('PublicHolidays'[Date])), TRUE(), FALSE())
)

FocusList_BusinessDays_Aging =
VAR StartDate = 'Table'[Focus List Entering Date]
VAR EndDate = TODAY()
RETURN
IF (
    ISBLANK(StartDate),
    BLANK(),
    CALCULATE (
        COUNTROWS ( 'Calendar' ),
        FILTER (
            'Calendar',
            'Calendar'[Date] > StartDate &&
            'Calendar'[Date] <= EndDate &&
            'Calendar'[IsWorkingDay] = TRUE()
        )
    )
)

FocusList_Aging_Bucket =
SWITCH(
    TRUE(),
    ISBLANK('Table'[Focus List Entering Date]), "No Date",
    'Table'[FocusList_BusinessDays_Aging] <= 30, "0–30 Business Days",
    'Table'[FocusList_BusinessDays_Aging] <= 45, "31–45 Business Days",
    'Table'[FocusList_BusinessDays_Aging] > 45, "45+ Business Days",
    BLANK()
)

