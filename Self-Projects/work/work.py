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


Calendar = 
ADDCOLUMNS (
    CALENDAR (DATE(2023,1,1), DATE(2026,12,31)),
    "IsWeekend", WEEKDAY([Date], 2) >= 6,  -- Saturday=6, Sunday=7
    "IsHoliday", FALSE(),  -- You can manually flag holidays later if needed
    "IsBusinessDay", IF(WEEKDAY([Date], 2) < 6, TRUE, FALSE)
)



LCO

Calendar = 
ADDCOLUMNS (
    CALENDAR (DATE(2023, 1, 1), DATE(2026, 12, 31)),
    "IsBusinessDay", 
        IF (
            WEEKDAY([Date], 2) < 6 
            && NOT([Date] IN VALUES(Holidays[Date])), 
            TRUE(), 
            FALSE()
        )
)

Calendar = 
ADDCOLUMNS (
    CALENDAR (DATE(2023, 1, 1), DATE(2026, 12, 31)),
    "IsBusinessDay", 
        IF ( WEEKDAY([Date], 2) < 6, TRUE(), FALSE() )
)


Adjusted Start Date = 
VAR ApprovedDate = 'Table'[Approved Date]
VAR IsNextDay = 'Table'[RequestTime] = TRUE
RETURN
    IF(
        IsNextDay,
        CALCULATE (
            MIN ( 'Calendar'[Date] ),
            FILTER (
                'Calendar',
                'Calendar'[Date] > DATEVALUE(ApprovedDate)
                && 'Calendar'[IsBusinessDay] = TRUE
            )
        ),
        DATEVALUE(ApprovedDate)
    )
    
    
SLA Due DateTime = 
VAR StartDate = [Adjusted Start Date]
VAR SLA_Days = 3
VAR BusinessDays = 
    FILTER (
        'Calendar',
        'Calendar'[Date] >= StartDate
            && 'Calendar'[IsBusinessDay] = TRUE
    )
VAR ThirdBusinessDay = 
    MINX (
        TOPN(SLA_Days, BusinessDays, 'Calendar'[Date], ASC),
        'Calendar'[Date]
    )
RETURN
    DATETIME(ThirdBusinessDay, TIME(23, 59, 59))  -- end of 3rd biz day
    
    
Adjusted Start Date = 
VAR ApprovedDate = 'Table'[Approved Date]
VAR RequestTimeFlag = 'Table'[RequestTime]
VAR BaseDate = DATEVALUE(ApprovedDate)  -- remove time

RETURN
    IF (
        RequestTimeFlag = TRUE,
        CALCULATE (
            MIN ( 'Calendar'[Date] ),
            FILTER (
                'Calendar',
                'Calendar'[Date] > BaseDate &&
                'Calendar'[IsBusinessDay] = TRUE
            )
        ),
        BaseDate
    )
    
SLA Due DateTime = 
VAR StartDate = [Adjusted Start Date]
VAR SLA_Days = 3

VAR ThirdBusinessDay =
    CALCULATE (
        MAX ( 'Calendar'[Date] ),
        FILTER (
            'Calendar',
            'Calendar'[Date] >= StartDate &&
            'Calendar'[IsBusinessDay] = TRUE
        ),
        TOPN ( SLA_Days, 'Calendar', 'Calendar'[Date], ASC )
    )

RETURN
    ThirdBusinessDay + TIME(23, 59, 59)
    

Adjusted Start Date = 
VAR ApprovedDateTime = 'Table'[Approved Date]
VAR RequestTimeFlag = 'Table'[RequestTime]
VAR BaseDate = DATEVALUE(ApprovedDateTime)  -- strips time

RETURN
    IF (
        RequestTimeFlag = TRUE,
        CALCULATE (
            MIN('Calendar'[Date]),
            FILTER (
                'Calendar',
                'Calendar'[Date] > BaseDate &&
                'Calendar'[IsBusinessDay] = TRUE
            )
        ),
        BaseDate
    )
    
SLA Due DateTime = 
VAR StartDate = [Adjusted Start Date]
VAR SLA_Days = 3

VAR BusinessDays =
    FILTER (
        'Calendar',
        'Calendar'[Date] >= StartDate &&
        'Calendar'[IsBusinessDay] = TRUE
    )

VAR ThirdBusinessDay =
    MINX (
        TOPN ( SLA_Days, BusinessDays, 'Calendar'[Date], ASC ),
        'Calendar'[Date]
    )

RETURN
    IF (
        NOT ISBLANK(ThirdBusinessDay),
        ThirdBusinessDay + TIME(23,59,59),
        BLANK()
    )


SLA Due DateTime = 
VAR StartDate = [Adjusted Start Date]
VAR SLA_Days = 3

VAR BusinessDays =
    FILTER (
        'Calendar',
        'Calendar'[Date] >= StartDate &&     -- INCLUDE the start date
        'Calendar'[IsBusinessDay] = TRUE
    )

VAR TargetDate =
    MAXX (
        TOPN ( SLA_Days, BusinessDays, 'Calendar'[Date], ASC ),
        'Calendar'[Date]
    )

RETURN
    IF (
        NOT ISBLANK(TargetDate),
        TargetDate + TIME(23, 59, 59),
        BLANK()
    )
    


    

SLA Met = 
VAR SLA_Due = [SLA Due DateTime]
VAR LetterDate = 'Table'[Letter Issue Date]
RETURN
    IF (
        LetterDate <= SLA_Due,
        "SLA Met",
        "SLA Breached"
    )

SLA Met = 
VAR SLA_Due = [SLA Due DateTime]
VAR LetterDate = 'Table'[Letter Issue Date]

RETURN
    IF (
        ISBLANK(LetterDate),
        "End Date Blank",
        IF (
            LetterDate <= SLA_Due,
            "SLA Met",
            "SLA Breached"
        )
    )

GroupType = 
SWITCH(
    TRUE(),
    'Table'[Credit group] = "Credit group", "Credit Group",
    'Table'[Credit group] = "Non credit group" || ISBLANK('Table'[Credit group]), "Non-Credit Group",
    "Other"
)

SLA_Days = 
SWITCH(
    TRUE(),
    'Table'[Type] IN { "FX", "ST", "Lombard" } 
        && ('Table'[Credit group] = "Non credit group" || ISBLANK('Table'[Credit group])),
        3,

    'Table'[Type] IN { "A", "B", "C" } 
        && 'Table'[Credit group] = "Credit group",
        5,

    BLANK()
)

SLA Due DateTime = 
VAR StartDate = [Adjusted Start Date]
VAR SLA_Days = 'Table'[SLA_Days]

VAR BusinessDays =
    FILTER (
        'Calendar',
        'Calendar'[Date] >= StartDate &&
        'Calendar'[IsBusinessDay] = TRUE
    )

VAR TargetDate =
    MAXX (
        TOPN ( SLA_Days, BusinessDays, 'Calendar'[Date], ASC ),
        'Calendar'[Date]
    )

RETURN
    IF (
        NOT ISBLANK(TargetDate),
        TargetDate + TIME(23, 59, 59),
        BLANK()
    )
    
SLA Status = 
VAR SLA_Due = [SLA Due DateTime]
VAR LetterDate = 'Table'[Letter Issue Date]

RETURN
    IF (
        ISBLANK(LetterDate),
        "End Date Blank",
        IF (
            LetterDate <= SLA_Due,
            "SLA Met",
            "SLA Breached"
        )
    )
    
    
GroupType = 
VAR TypeText = LOWER('Table'[Type])
VAR CreditGroupCol = 'Table'[Credit group]

RETURN
SWITCH(
    TRUE(),

    -- Case 1: Embedded in Type
    SEARCH("credit", TypeText, 1, 0) > 0 && SEARCH("non", TypeText, 1, 0) = 0,
        "Credit Group",

    SEARCH("non-credit", TypeText, 1, 0) > 0 || SEARCH("non credit", TypeText, 1, 0) > 0,
        "Non-Credit Group",

    -- Case 2: Use Credit Group column
    CreditGroupCol = "Credit group",
        "Credit Group",

    CreditGroupCol = "Non credit group" || ISBLANK(CreditGroupCol),
        "Non-Credit Group",

    -- Fallback
    "Other"
)

SLA_Days = 
SWITCH(
    TRUE(),
    'Table'[Type] IN { "FX", "ST", "Lombard" } 
        && 'Table'[GroupType] = "Non-Credit Group",
        3,

    'Table'[Type] IN { "A", "B", "C" } 
        && 'Table'[GroupType] = "Credit Group",
        5,

    BLANK()
)

IncludeInSLA = 
VAR TypeText = LOWER('Table'[Type])
RETURN
    SWITCH(
        TRUE(),

        'Table'[Type] IN { "FX", "ST", "Lombard", "A", "B", "C" },
        TRUE(),

        SEARCH("credit", TypeText, 1, 0) > 0,
        TRUE(),

        SEARCH("non-credit", TypeText, 1, 0) > 0 || SEARCH("non credit", TypeText, 1, 0) > 0,
        TRUE(),

        FALSE()
    )
    
    
SLA Due DateTime = 
VAR StartDate = [Adjusted Start Date]
VAR SLA_Days = 'Table'[SLA_Days]

VAR BusinessDays =
    FILTER (
        'Calendar',
        'Calendar'[Date] >= StartDate &&
        'Calendar'[IsBusinessDay] = TRUE
    )

VAR TargetDate =
    MAXX (
        TOPN ( SLA_Days, BusinessDays, 'Calendar'[Date], ASC ),
        'Calendar'[Date]
    )

RETURN
    IF (
        NOT ISBLANK(TargetDate),
        TargetDate + TIME(23, 59, 59),
        BLANK()
    )

SLA Status = 
VAR SLA_Due = [SLA Due DateTime]
VAR LetterDate = 'Table'[Letter Issue Date]

RETURN
    IF (
        ISBLANK(LetterDate),
        "End Date Blank",
        IF (
            LetterDate <= SLA_Due,
            "SLA Met",
            "SLA Breached"
        )
    )


DocReview_AdjustedStartDate = 
DATEVALUE('Table'[Approved Date])

DocReview_SLA_DueDateTime = 
VAR StartDate = DATEVALUE('Table'[Approved Date])
VAR SLA_Days = 5

VAR BusinessDays =
    FILTER (
        'Calendar',
        'Calendar'[Date] >= StartDate &&
        'Calendar'[IsBusinessDay] = TRUE
    )

VAR TargetDate =
    MAXX (
        TOPN ( SLA_Days, BusinessDays, 'Calendar'[Date], ASC ),
        'Calendar'[Date]
    )

RETURN
    IF (
        NOT ISBLANK(TargetDate),
        TargetDate + TIME(23, 59, 59),
        BLANK()
    )
    
DocReview_SLA_Status = 
VAR SLA_Due = [DocReview_SLA_DueDateTime]
VAR ReviewDate = 'Table'[Document Review Date]

RETURN
    IF (
        ISBLANK(ReviewDate),
        "End Date Blank",
        IF (
            ReviewDate <= SLA_Due,
            "SLA Met",
            "SLA Breached"
        )
    )
    
ROC_BusinessDays = 
VAR RocStart = 'Table'[ROC- Submission Date]
VAR RocEnd = 'Table'[ROC- Completion Date]

RETURN
    CALCULATE (
        COUNTROWS('Calendar'),
        FILTER (
            'Calendar',
            'Calendar'[Date] >= DATEVALUE(RocStart) &&
            'Calendar'[Date] <= DATEVALUE(RocEnd) &&
            'Calendar'[IsBusinessDay] = TRUE
        )
    )
    
Avaloq_BusinessDays = 
VAR StartDate = 'Table'[Soft Copies Received Date]
VAR EndDate = 'Table'[Avaloq Setup Date]

RETURN
    CALCULATE (
        COUNTROWS('Calendar'),
        FILTER (
            'Calendar',
            'Calendar'[Date] >= DATEVALUE(StartDate) &&
            'Calendar'[Date] <= DATEVALUE(EndDate) &&
            'Calendar'[IsBusinessDay] = TRUE
        )
    )
    

Avaloq_BusinessDays = 
VAR StartDate = 'Table'[Soft Copies Received Date]
VAR EndDate = 'Table'[Avaloq Setup Date]

RETURN
    IF (
        NOT ISBLANK(StartDate) && NOT ISBLANK(EndDate),
        CALCULATE (
            COUNTROWS('Calendar'),
            FILTER (
                'Calendar',
                'Calendar'[Date] >= DATEVALUE(StartDate) &&
                'Calendar'[Date] <= DATEVALUE(EndDate) &&
                'Calendar'[IsBusinessDay] = TRUE
            )
        ),
        BLANK()
    )

Net_Business_Days = 
[Avaloq_BusinessDays] - [ROC_BusinessDays]

Avaloq_SLA_Status = 
VAR NetDays = [Net_Business_Days]

RETURN
    IF (
        ISBLANK('Table'[Avaloq Setup Date]),
        "End Date Blank",
        IF (
            NetDays <= 5,
            "SLA Met",
            "SLA Breached"
        )
    )
    
    
ROC_BusinessDays = 
VAR RocStart = 'Table'[ROC- Submission Date]
VAR RocEnd = 'Table'[ROC- Completion Date]
VAR TodayDate = TODAY()

RETURN
    IF (
        ISBLANK(RocStart),
        0,
        CALCULATE (
            COUNTROWS('Calendar'),
            FILTER (
                'Calendar',
                'Calendar'[Date] >= DATEVALUE(RocStart) &&
                'Calendar'[Date] <= DATEVALUE(IF(ISBLANK(RocEnd), TodayDate, RocEnd)) &&
                'Calendar'[IsBusinessDay] = TRUE
            )
        )
    )
    
Avaloq_BusinessDays = 
VAR StartDate = 'Table'[Soft Copies Received Date]
VAR EndDate = IF(ISBLANK('Table'[Avaloq Setup Date]), TODAY(), 'Table'[Avaloq Setup Date])

RETURN
    IF (
        ISBLANK(StartDate),
        BLANK(),
        CALCULATE (
            COUNTROWS('Calendar'),
            FILTER (
                'Calendar',
                'Calendar'[Date] >= DATEVALUE(StartDate) &&
                'Calendar'[Date] <= DATEVALUE(EndDate) &&
                'Calendar'[IsBusinessDay] = TRUE
            )
        )
    )
    
Net_Business_Days = 
IF(
    ISBLANK([Avaloq_BusinessDays]),
    BLANK(),
    [Avaloq_BusinessDays] - [ROC_BusinessDays]
)

    

Avaloq_SLA_Status = 
VAR SoftCopiesDate = 'Table'[Soft Copies Received Date]
VAR AvaloqSetupDate = 'Table'[Avaloq Setup Date]
VAR RocStart = 'Table'[ROC- Submission Date]
VAR RocEnd = 'Table'[ROC- Completion Date]
VAR NetDays = [Net_Business_Days]

RETURN
    IF (
        ISBLANK(SoftCopiesDate),
        "Soft Copies Blank",

        ISBLANK(RocStart) && NOT ISBLANK(RocEnd),
        "ROC Submission Blank",

        IF (
            NetDays <= 5,
            "SLA Met",
            "SLA Breached"
        )
    )

Avaloq_SLA_Status = 
VAR SoftCopiesDate = 'Table'[Soft Copies Received Date]
VAR AvaloqSetupDate = 'Table'[Avaloq Setup Date]
VAR RocStart = 'Table'[ROC- Submission Date]
VAR RocEnd = 'Table'[ROC- Completion Date]
VAR NetDays = [Net_Business_Days]

RETURN
SWITCH(
    TRUE(),

    ISBLANK(SoftCopiesDate),
        "Soft Copies Blank",

    ISBLANK(RocStart) && NOT ISBLANK(RocEnd),
        "ROC Submission Blank",

    NetDays <= 5,
        "SLA Met",

    NetDays > 5,
        "SLA Breached",

    BLANK()
)


LetterSLA_AdjustedStartDate = 
VAR ApprovedDate = 'Table'[Approved Date]
VAR RequestTime = 'Table'[RequestTime]

VAR AdjustedDate =
    IF(
        RequestTime = TRUE(),
        CALCULATE(
            MIN('Calendar'[Date]),
            FILTER(
                'Calendar',
                'Calendar'[Date] > DATEVALUE(ApprovedDate) &&
                'Calendar'[IsBusinessDay] = TRUE
            )
        ),
        DATEVALUE(ApprovedDate)
    )

RETURN
    IF(ISBLANK(ApprovedDate), BLANK(), AdjustedDate)
    
LetterSLA_ROC_BusinessDays = 
VAR RocStart = 'Table'[ROC- Submission Date]
VAR RocEnd = 'Table'[ROC- Completion Date]
VAR TodayDate = TODAY()

RETURN
    IF(
        ISBLANK(RocStart),
        0,
        CALCULATE(
            COUNTROWS('Calendar'),
            FILTER(
                'Calendar',
                'Calendar'[Date] >= DATEVALUE(RocStart) &&
                'Calendar'[Date] <= DATEVALUE(IF(ISBLANK(RocEnd), TodayDate, RocEnd)) &&
                'Calendar'[IsBusinessDay] = TRUE
            )
        )
    )
    
LetterSLA_BusinessDays = 
VAR StartDate = [LetterSLA_AdjustedStartDate]
VAR EndDate = IF(ISBLANK('Table'[Letter Issue Date]), TODAY(), 'Table'[Letter Issue Date])

RETURN
    IF(
        ISBLANK(StartDate),
        BLANK(),
        CALCULATE(
            COUNTROWS('Calendar'),
            FILTER(
                'Calendar',
                'Calendar'[Date] >= DATEVALUE(StartDate) &&
                'Calendar'[Date] <= DATEVALUE(EndDate) &&
                'Calendar'[IsBusinessDay] = TRUE
            )
        )
    )
    
LetterSLA_Net_Business_Days = 
IF(
    ISBLANK([LetterSLA_BusinessDays]),
    BLANK(),
    [LetterSLA_BusinessDays] - [LetterSLA_ROC_BusinessDays]
)

LetterSLA_Status = 
VAR StartDate = 'Table'[Approved Date]
VAR EndDate = 'Table'[Letter Issue Date]
VAR RocStart = 'Table'[ROC- Submission Date]
VAR RocEnd = 'Table'[ROC- Completion Date]
VAR NetDays = [LetterSLA_Net_Business_Days]

RETURN
SWITCH(
    TRUE(),

    ISBLANK(StartDate) && NOT ISBLANK(EndDate),
        "Blank Approved Date",

    ISBLANK(RocStart) && NOT ISBLANK(RocEnd),
        "Blank ROC Submission",

    NetDays <= 3,
        "SLA Met",

    NetDays > 3,
        "SLA Breached",

    BLANK()
)

SLA_Process = 
SWITCH(
    TRUE(),
    'Table'[Type] IN { "X1", "X2", "X3" }, "Process X",   -- your Type X variants
    'Table'[Type] IN { "Y1", "Y2", "Y3" }, "Process Y",   -- your Type Y variants
    BLANK()
)

SimpleSLA_BusinessDays = 
VAR StartDate = 'Table'[Approved Date]
VAR EndDate = IF(ISBLANK('Table'[Letter Issue Date]), TODAY(), 'Table'[Letter Issue Date])

RETURN
    IF(
        ISBLANK(StartDate),
        BLANK(),
        CALCULATE(
            COUNTROWS('Calendar'),
            FILTER(
                'Calendar',
                'Calendar'[Date] >= DATEVALUE(StartDate) &&
                'Calendar'[Date] <= DATEVALUE(EndDate) &&
                'Calendar'[IsBusinessDay] = TRUE
            )
        )
    )
    
SimpleSLA_Status = 
VAR StartDate = 'Table'[Approved Date]
VAR EndDate = 'Table'[Letter Issue Date]
VAR DaysTaken = [SimpleSLA_BusinessDays]

RETURN
SWITCH(
    TRUE(),
    ISBLANK(StartDate), "Blank Approved Date",
    DaysTaken <= 3, "SLA Met",
    DaysTaken > 3, "SLA Breached",
    BLANK()
)


SameDaySLA_DueDateTime = 
VAR StartDate = 'Table'[Approved Date]
RETURN
    IF(
        ISBLANK(StartDate),
        BLANK(),
        INT(StartDate) + TIME(23, 59, 59)
    )
    
SameDaySLA_Status = 
VAR StartDate = 'Table'[Approved Date]
VAR EndDate = IF(ISBLANK('Table'[Avaloq Setup Date]), TODAY(), 'Table'[Avaloq Setup Date])
VAR SLADue = [SameDaySLA_DueDateTime]

RETURN
SWITCH(
    TRUE(),
    ISBLANK(StartDate), "Blank Approved Date",
    EndDate <= SLADue, "SLA Met",
    EndDate > SLADue, "SLA Breached",
    BLANK()
)

MonthEndPlus2BizDays = 
VAR ApprovedDate = 'Table'[Approved Date]

-- Get last day of the month
VAR MonthEnd = 
    EOMONTH(ApprovedDate, 0)

-- Get the 2nd business day after month end
VAR TargetBizDate =
    CALCULATE(
        MAX('Calendar'[Date]),
        TOPN(
            2,
            FILTER(
                'Calendar',
                'Calendar'[Date] > MonthEnd &&
                'Calendar'[IsBusinessDay] = TRUE
            ),
            'Calendar'[Date], ASC
        )
    )

RETURN
    IF(
        ISBLANK(ApprovedDate),
        BLANK(),
        TargetBizDate + TIME(23, 59, 59)
    )
    
    
MonthEndSLA_Status = 
VAR ApprovedDate = 'Table'[Approved Date]
VAR SetupDate = IF(ISBLANK('Table'[Avaloq Setup Date]), TODAY(), 'Table'[Avaloq Setup Date])
VAR SLADue = [MonthEndPlus2BizDays]

RETURN
SWITCH(
    TRUE(),
    ISBLANK(ApprovedDate), "Blank Approved Date",
    SetupDate <= SLADue, "SLA Met",
    SetupDate > SLADue, "SLA Breached",
    BLANK()
)

BusinessDays_Bucket =
SWITCH(
    TRUE(),
    'Table'[BusinessDays_Taken] <= 5, "0–5 Days",
    'Table'[BusinessDays_Taken] <= 10, "6–10 Days",
    'Table'[BusinessDays_Taken] > 10, "10+ Days",
    BLANK()
)

Bucket_Order = 
SWITCH(
    'Table'[BusinessDays_Bucket],
    "0–5 Days", 1,
    "6–10 Days", 2,
    "10+ Days", 3
)


