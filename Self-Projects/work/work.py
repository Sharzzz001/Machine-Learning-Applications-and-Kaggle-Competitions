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

SLA_Due_Date =
VAR StartDateTime = 'Table'[AdjustedRequestDate]
VAR StartDate = INT(StartDateTime)  -- removes time
VAR SLA_Days = IF('Table'[Urgent] = TRUE(), 1, 3)

VAR Workdays =
    FILTER (
        'Calendar',
        'Calendar'[Date] > StartDate &&
        'Calendar'[IsWorkingDay] = TRUE()
    )

VAR DueDateRow =
    TOPN(SLA_Days, Workdays, 'Calendar'[Date], ASC)

VAR DueDateOnly =
    MAXX(DueDateRow, 'Calendar'[Date])

RETURN
IF (
    ISBLANK(DueDateOnly),
    BLANK(),
    DueDateOnly + MOD(StartDateTime, 1)  -- restores time
)



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


BusinessDays_Taken =
VAR StartDate = INT('Table'[AdjustedRequestDate])
VAR EndDate = INT('Table'[Checker Completion Date])

VAR DayCount =
    CALCULATE (
        COUNTROWS('Calendar'),
        FILTER (
            'Calendar',
            'Calendar'[Date] >= StartDate &&
            'Calendar'[Date] <= EndDate &&
            'Calendar'[IsWorkingDay] = TRUE()
        )
    )

RETURN
IF (
    ISBLANK(EndDate),
    BLANK(),
    IF(ISBLANK(DayCount), 0, DayCount)
)



Sla 2

AdjustedRequestDateTime =
VAR OriginalDateTime = 'Table'[Request Date]
VAR RequestTimeFlag = 'Table'[RequestTime]
VAR NextWorkday =
    CALCULATE (
        MIN('Calendar'[Date]),
        FILTER (
            'Calendar',
            'Calendar'[Date] > INT(OriginalDateTime) &&
            'Calendar'[IsWorkingDay] = TRUE()
        )
    )
RETURN
IF (
    RequestTimeFlag,
    NextWorkday + MOD(OriginalDateTime, 1),  -- add time back
    OriginalDateTime
)

SLA2_Due_Date =
VAR StartDateTime = 'Table'[AdjustedRequestDateTime]
VAR SLA_Due_Date =
    IF (
        'Table'[Urgent] = TRUE(),
        StartDateTime + TIME(2, 0, 0),           -- 2 hours for urgent
        INT(StartDateTime) + TIME(23, 59, 0)     -- Same day for normal
    )
RETURN SLA_Due_Date


SLA2_Status =
VAR CompletionTime = 'Table'[Checker Completion Date]
VAR SLA_Deadline = 'Table'[SLA2_Due_Date]

RETURN
IF (
    ISBLANK(CompletionTime),
    BLANK(),  -- still open
    IF (
        CompletionTime <= SLA_Deadline,
        "SLA Met",
        "SLA Breached"
    )
)


SLA 3

AdjustedRequestDateTime =
VAR OriginalDateTime = 'Table'[Request Date]
VAR RequestTimeFlag = 'Table'[RequestTime]
VAR NextWorkday =
    CALCULATE (
        MIN('Calendar'[Date]),
        FILTER (
            'Calendar',
            'Calendar'[Date] > INT(OriginalDateTime) &&
            'Calendar'[IsWorkingDay] = TRUE()
        )
    )
RETURN
IF (
    RequestTimeFlag,
    NextWorkday + MOD(OriginalDateTime, 1),  -- preserves time
    OriginalDateTime
)

SLA3_Due_Date =
VAR StartDateTime = 'Table'[AdjustedRequestDateTime]
VAR StartDate = INT(StartDateTime)  -- removes time

VAR SLA_Date =
    IF (
        'Table'[Urgent] = TRUE(),
        StartDate + 7,
        VAR DayOfMonth = DAY(StartDate)
        VAR MonthBase =
            IF(DayOfMonth >= 26,
                EOMONTH(StartDate, 1),  -- next month end
                EOMONTH(StartDate, 0)   -- this month end
            )
        RETURN MonthBase
    )

RETURN
SLA_Date + TIME(23, 59, 59)


SLA3_Status =
VAR CompletionTime = 'Table'[Checker Completion Date]
VAR SLA_Deadline = 'Table'[SLA3_Due_Date]

RETURN
IF (
    ISBLANK(CompletionTime),
    BLANK(),
    IF (
        CompletionTime <= SLA_Deadline,
        "SLA Met",
        "SLA Breached"
    )
)



SLA3_Due_Date =
VAR StartDateTime = 'Table'[AdjustedRequestDateTime]
VAR StartDate = INT(StartDateTime)         -- date part
VAR StartTime = MOD(StartDateTime, 1)      -- time part

VAR SLA_Raw_Date =
    IF (
        'Table'[Urgent] = TRUE(),
        StartDate + 7,
        VAR DayOfMonth = DAY(StartDate)
        VAR MonthBase =
            IF(DayOfMonth >= 26,
                EOMONTH(StartDate, 1),  -- next month end
                EOMONTH(StartDate, 0)   -- same month end
            )
        RETURN MonthBase
    )

-- Find the next non-holiday date if it's a holiday
VAR NextWorkingDate =
    CALCULATE (
        MIN('Calendar'[Date]),  -- assumes Calendar table includes all dates
        FILTER (
            ALL('Calendar'),
            'Calendar'[Date] >= SLA_Raw_Date &&
            NOT 'Calendar'[Date] IN VALUES('PublicHolidays'[Date])
        )
    )

RETURN
NextWorkingDate + StartTime


SLA3_Due_Date =
VAR StartDate = INT('Table'[AdjustedRequestDateTime])  -- remove time
VAR IsUrgent = 'Table'[Urgent]
VAR DayOfMonth = DAY(StartDate)

-- Determine base SLA date (no time yet)
VAR SLA_Base_Date =
    IF (
        IsUrgent,
        StartDate + 7,
        IF (
            DayOfMonth >= 26,
            EOMONTH(StartDate, 1),  -- end of next month
            EOMONTH(StartDate, 0)   -- end of this month
        )
    )

-- Check if base date is a public holiday
VAR IsHoliday =
    CALCULATE (
        COUNTROWS('PublicHolidays'),
        FILTER (
            'PublicHolidays',
            'PublicHolidays'[Date] = SLA_Base_Date
        )
    ) > 0

-- If holiday, push forward to next non-holiday date
VAR Final_Date =
    IF (
        IsHoliday,
        CALCULATE (
            MIN('Calendar'[Date]),
            FILTER (
                'Calendar',
                'Calendar'[Date] > SLA_Base_Date &&
                NOT 'Calendar'[Date] IN VALUES('PublicHolidays'[Date])
            )
        ),
        SLA_Base_Date
    )

RETURN Final_Date + TIME(23,59,59)



SLA_Due_Date =
VAR StartDate = INT('Table'[AdjustedRequestDate])  -- Remove time
VAR SLA_Days = IF('Table'[Urgent] = TRUE(), 1, 3)

-- Filter for working days excluding public holidays
VAR Workdays =
    FILTER (
        'Calendar',
        'Calendar'[Date] > StartDate &&
        'Calendar'[IsWorkingDay] = TRUE() &&
        NOT 'Calendar'[Date] IN VALUES('PublicHolidays'[Date])
    )

-- Get the nth business day from start date
VAR DueDateRow =
    TOPN(SLA_Days, Workdays, 'Calendar'[Date], ASC)

VAR DueDateOnly =
    MAXX(DueDateRow, 'Calendar'[Date])

RETURN
IF (
    ISBLANK(DueDateOnly),
    BLANK(),
    DueDateOnly + TIME(23,59,59)
)

