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


......

RR_TotalDue = 
CALCULATE(
    COUNTROWS('RR_Table'),
    'RR_Table'[IsDueThisMonth] = TRUE()
)

RR_Completed = 
CALCULATE(
    COUNTROWS('RR_Table'),
    'RR_Table'[IsDueThisMonth] = TRUE(),
    'RR_Table'[StatusCorpInd] = "KYC Completed"
)

RR_Pending = 
CALCULATE(
    COUNTROWS('RR_Table'),
    'RR_Table'[IsDueThisMonth] = TRUE(),
    'RR_Table'[StatusCorpInd] IN {
        "In Progress", "Pending Review", "Documents Missing", "Awaiting Client"
    }
)

RR_CompletedOnDate = 
CALCULATE(
    COUNTROWS('RR_Table'),
    'RR_Table'[IsDueThisMonth] = TRUE(),
    'RR_Table'[StatusCorpInd] = "KYC Completed"
)

RR_ColumnLabels = 
UNION(
    DATATABLE("Label", STRING, {
        {"Total Due"},
        {"Completed"},
        {"Pending"}
    }),
    SELECTCOLUMNS(
        FILTER(DateTable, 
            MONTH(DateTable[Date]) = MONTH(TODAY()) &&
            YEAR(DateTable[Date]) = YEAR(TODAY())
        ),
        "Label", FORMAT(DateTable[Date], "d MMM")
    )
)

RR_MatrixValue = 
VAR SelectedLabel = SELECTEDVALUE('RR_ColumnLabels'[Label])
VAR TodayMonth = MONTH(TODAY())
VAR TodayYear = YEAR(TODAY())

RETURN
    SWITCH(
        TRUE(),
        SelectedLabel = "Total Due", [RR_TotalDue],
        SelectedLabel = "Completed", [RR_Completed],
        SelectedLabel = "Pending", [RR_Pending],
        -- Daily completions
        CALCULATE(
            [RR_CompletedOnDate],
            FILTER(
                DateTable,
                FORMAT(DateTable[Date], "d MMM") = SelectedLabel &&
                MONTH(DateTable[Date]) = TodayMonth &&
                YEAR(DateTable[Date]) = TodayYear
            )
        )
    )
    
    


RR_MatrixValue = 
VAR SelectedLabel = SELECTEDVALUE('RR_ColumnLabels'[Label])
VAR TodayMonth = MONTH(TODAY())
VAR TodayYear = YEAR(TODAY())

VAR Result =
    SWITCH(
        TRUE(),
        SelectedLabel = "Total Due", [RR_TotalDue],
        SelectedLabel = "Completed", [RR_Completed],
        SelectedLabel = "Pending", [RR_Pending],
        
        -- Daily completions by matching actual Completion Date
        CALCULATE(
            COUNTROWS('RR_Table'),
            'RR_Table'[IsDueThisMonth] = TRUE(),
            'RR_Table'[StatusCorpInd] = "KYC Completed",
            FORMAT('RR_Table'[Completion Date], "d MMM") = SelectedLabel
        )
    )

RETURN Result


Risk_Group = 
SWITCH(
    TRUE(),
    'RR_Table'[Risk Category] = "High", "High",
    'RR_Table'[Risk Category] IN {"Medium", "Low"} || ISBLANK('RR_Table'[Risk Category]), "Medium/Low",
    "Other"
)
