Calendar = 
ADDCOLUMNS (
    CALENDAR (DATE(2022,1,1), DATE(2026,12,31)),  -- adjust range
    "IsWorkingDay", 
        IF (
            WEEKDAY([Date], 2) <= 5,  -- 1 = Monday, 7 = Sunday; weekdays are 1-5
            TRUE(),
            FALSE()
        )
)

AdjustedRequestDate = 
VAR ReqDate = 'YourTable'[Request Date]
RETURN
    IF (
        'YourTable'[RequestTime] = TRUE(),
        CALCULATE (
            MIN('Calendar'[Date]),
            FILTER (
                'Calendar',
                'Calendar'[Date] > ReqDate
                && 'Calendar'[IsWorkingDay] = TRUE()
            )
        ),
        ReqDate
    )