Calendar = 
ADDCOLUMNS (
    CALENDAR (DATE(2023, 1, 1), DATE(2026, 12, 31)),
    "DayOfWeek", WEEKDAY([Date], 2),
    "IsBusinessDay", IF(WEEKDAY([Date], 2) < 6, TRUE(), FALSE())
)


AdjustedRequestDate =
VAR BaseDate = 'Table'[Request Date]
VAR ShiftNeeded = 'Table'[RequestTime] = TRUE()
RETURN
    IF (
        ShiftNeeded,
        CALCULATE (
            MIN('Calendar'[Date]),
            FILTER (
                'Calendar',
                'Calendar'[Date] > BaseDate &&
                'Calendar'[IsBusinessDay] = TRUE()
            ),
            TOPN(1, 'Calendar', [Date], ASC)
        ),
        BaseDate
    )
    
    
SLA_Days_Allowed = IF('Table'[Urgent] = TRUE(), 1, 3)



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
