IsDueThisMonth = 
IF (
    MONTH('RR_Table'[Due Date Calculated]) = MONTH(TODAY()) &&
    YEAR('RR_Table'[Due Date Calculated]) = YEAR(TODAY()),
    TRUE(), FALSE()
)

RR_Status =
SWITCH(
    TRUE(),
    'RR_Table'[StatusCorpInd] = "KYC Completed", "Completed",
    'RR_Table'[StatusCorpInd] IN { "In Progress", "Pending Review", "Documents Missing", "Awaiting Client" }, "Pending",
    "Other"
)

DateTable = CALENDAR(DATE(2024,1,1), DATE(2025,12,31))

RR_TotalDue = 
CALCULATE(
    COUNTROWS('RR_Table'),
    'RR_Table'[IsDueThisMonth] = TRUE()
)

RR_Completed = 
CALCULATE(
    COUNTROWS('RR_Table'),
    'RR_Table'[IsDueThisMonth] = TRUE(),
    'RR_Table'[RR_Status] = "Completed"
)

RR_Pending = 
CALCULATE(
    COUNTROWS('RR_Table'),
    'RR_Table'[IsDueThisMonth] = TRUE(),
    'RR_Table'[RR_Status] = "Pending"
)

Daily_Completed = 
CALCULATE(
    COUNTROWS('RR_Table'),
    'RR_Table'[RR_Status] = "Completed",
    'RR_Table'[IsDueThisMonth] = TRUE()
)


