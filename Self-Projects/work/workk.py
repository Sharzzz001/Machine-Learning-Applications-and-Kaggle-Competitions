CalendarDays_Aging =
DATEDIFF('Table'[StartDate], TODAY(), DAY)


Aging_Bucket =
SWITCH(
    TRUE(),
    ISBLANK('Table'[StartDate]), "No Start Date",
    'Table'[CalendarDays_Aging] <= 30, "0–30 Days",
    'Table'[CalendarDays_Aging] > 30 && NOT(ISBLANK('Table'[Extended Deadline])) && 'Table'[CalendarDays_Aging] <= 100, ">30 Days with FCC Extension",
    'Table'[CalendarDays_Aging] > 30 && ISBLANK('Table'[Extended Deadline]) && 'Table'[CalendarDays_Aging] <= 100, ">30 Days without FCC Extension",
    'Table'[CalendarDays_Aging] > 100 && 'Table'[CalendarDays_Aging] <= 120, ">100 Days",
    'Table'[CalendarDays_Aging] > 120, ">120 Days",
    BLANK()
)


Pending_Accounts_Count =
CALCULATE(
    DISTINCTCOUNT('Table'[Account ID]),
    'Table'[Doc Status] = "Pending"
)

Aging_Bucket_Sort =
DATATABLE(
    "Aging_Bucket", STRING,
    "SortOrder", INTEGER,
    {
        { "0–30 Days", 1 },
        { ">30 Days with FCC Extension", 2 },
        { ">30 Days without FCC Extension", 3 },
        { ">100 Days", 4 },
        { ">120 Days", 5 },
        { "No Start Date", 6 }
    }
)

ActionComment =
SWITCH(
    [Aging_Bucket],
    "0–30 Days", "Escalated to Team/Group Head",
    ">30 Days with FCC Extension", "Escalated to FCC for Approval",
    ">30 Days without FCC Extension", "Pending Review - No FCC Approval",
    ">100 Days", "Critical - Immediate Action Required",
    ">120 Days", "Breached - High Priority Escalation",
    "No Start Date", "Data Issue - Start Date Missing",
    BLANK()
)

ActionComment_Display =
IF(
    HASONEFILTER('Aging_Bucket_Sort'[Aging_Bucket]),
    FIRSTNONBLANK('Aging_Bucket_Sort'[ActionComment], 1),
    BLANK()  // For Grand Total row, show blank
)

PendingAccounts_ByBucket =
VAR SelectedBucket = SELECTEDVALUE('Aging_Bucket_Sort'[Aging_Bucket])
RETURN
CALCULATE (
    DISTINCTCOUNT('FactTable'[Account ID]),
    FILTER (
        'FactTable',
        'FactTable'[Aging_Bucket] = SelectedBucket &&
        'FactTable'[Doc Status] = "Pending"
    )
)


PendingAccounts_ByBucket =
VAR SelectedBucket = SELECTEDVALUE('Aging_Bucket_Sort'[Aging_Bucket])
RETURN
CALCULATE(
    DISTINCTCOUNT('DocumentData'[Account ID]),
    TREATAS( { SelectedBucket }, 'DocumentData'[Aging_Bucket] ),
    'DocumentData'[Doc Status] = "Pending"
)

PendingAccounts_ByBucket =
VAR SelectedBucket = SELECTEDVALUE('Aging_Bucket_Sort'[Aging_Bucket])
VAR CountResult =
    CALCULATE(
        DISTINCTCOUNT('DocumentData'[Account ID]),
        TREATAS( { SelectedBucket }, 'DocumentData'[Aging_Bucket] ),
        'DocumentData'[Doc Status] = "Pending"
    )
RETURN
COALESCE(CountResult, 0)

