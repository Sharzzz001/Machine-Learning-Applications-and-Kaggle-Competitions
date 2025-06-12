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
    
    
    
AdjustedRequestDate = 
VAR OriginalDateTime = 'Table'[Request Date]
VAR OriginalTime = MOD(OriginalDateTime, 1)  -- isolates time
VAR AdjustedDateOnly =
    CALCULATE (
        MIN('Calendar'[Date]),
        FILTER (
            'Calendar',
            'Calendar'[Date] > INT(OriginalDateTime) &&
            'Calendar'[IsWorkingDay]
        )
    )
RETURN
IF (
    'Table'[RequestTime] = TRUE(),
    AdjustedDateOnly + OriginalTime,
    OriginalDateTime
)


SLA_Due_Date = 
VAR StartDate = 'Table'[AdjustedRequestDate]
VAR SLA_Days = IF('Table'[Urgent] = TRUE(), 1, 3)
RETURN
CALCULATE (
    MAX('Calendar'[Date]),
    FILTER (
        'Calendar',
        'Calendar'[Date] >= StartDate &&
        'Calendar'[IsWorkingDay] = TRUE()
    ),
    TOPN(SLA_Days, 'Calendar', 'Calendar'[Date], ASC)
)
+ MOD(StartDate, 1)  -- add time back


SLA_Due_Date = 
VAR StartDate = 'Table'[AdjustedRequestDate]
VAR SLA_Days = IF('Table'[Urgent] = TRUE(), 1, 3)

VAR DueDateOnly =
    CALCULATE (
        MAX('Calendar'[Date]),
        FILTER (
            'Calendar',
            'Calendar'[Date] >= INT(StartDate) &&
            'Calendar'[IsWorkingDay]
        ),
        TOPN(SLA_Days, 'Calendar', 'Calendar'[Date], ASC)
    )

VAR DueDateTime =
    IF (
        NOT ISBLANK(DueDateOnly),
        DueDateOnly + MOD(StartDate, 1),
        BLANK()
    )

RETURN DueDateTime

SLA_Status = 
IF (
    ISBLANK('Table'[Checker Completion Date]),
    BLANK(),  -- Still open, don't flag
    IF (
        'Table'[Checker Completion Date] <= 'Table'[SLA_Due_Date],
        "SLA Met",
        "SLA Breached"
    )
)


BusinessDays_Taken = 
VAR StartDate = 'Table'[AdjustedRequestDate]
VAR EndDate = 'Table'[Checker Completion Date]
RETURN
CALCULATE (
    COUNTROWS('Calendar'),
    FILTER (
        'Calendar',
        'Calendar'[Date] >= StartDate &&
        'Calendar'[Date] <= EndDate &&
        'Calendar'[IsWorkingDay]
    )
)












