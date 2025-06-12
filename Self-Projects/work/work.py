Calendar = 
ADDCOLUMNS (
    CALENDAR (DATE(2023, 1, 1), DATE(2026, 12, 31)),
    "DayOfWeek", WEEKDAY([Date], 2),
    "IsBusinessDay", IF(WEEKDAY([Date], 2) < 6, TRUE(), FALSE())
)


AdjustedRequestDate = 
VAR RequestDate = 'Table'[Request Date]
VAR Shift = IF('Table'[RequestTime] = TRUE(), 1, 0)
RETURN
    CALCULATE (
        MIN('Calendar'[Date]),
        FILTER (
            'Calendar',
            'Calendar'[Date] >= RequestDate &&
            'Calendar'[IsBusinessDay] = TRUE()
        ),
        OFFSET(Shift)
    )
    
    
BusinessDaysToComplete = 
CALCULATE (
    COUNTROWS('Calendar'),
    FILTER (
        'Calendar',
        'Calendar'[Date] >= 'Table'[AdjustedRequestDate]
            && 'Calendar'[Date] <= 'Table'[Checker Completion Date]
            && 'Calendar'[IsBusinessDay] = TRUE()
    )
)
    
