#IsDueThisMonth = 
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

RR_ColumnLabels = 
UNION(
    SELECTCOLUMNS(
        DATATABLE("Label", STRING, {
            {"Total Due"},
            {"Completed"},
            {"Pending"}
        }),
        "Label", [Label],
        "SortOrder", SWITCH([Label],
            "Total Due", 1,
            "Completed", 2,
            "Pending", 3
        )
    ),
    SELECTCOLUMNS(
        ADDCOLUMNS(
            FILTER(DateTable, 
                MONTH(DateTable[Date]) = MONTH(TODAY()) &&
                YEAR(DateTable[Date]) = YEAR(TODAY())
            ),
            "Label", FORMAT(DateTable[Date], "d MMM"),
            "SortOrder", DAY(DateTable[Date]) + 3
        ),
        "Label", [Label],
        "SortOrder", [SortOrder]
    )
)

RR Completed Matrix Measure = 
VAR SelectedLabel = SELECTEDVALUE(RR_ColumnLabels[Label])
RETURN
    SWITCH(
        TRUE(),
        SelectedLabel = "Total Due", [RR Total Due],
        SelectedLabel = "Completed", [RR Completed This Month],
        SelectedLabel = "Pending", [RR Pending This Month],
        -- Handle dates
        ISINSCOPE(RR_ColumnLabels[Label]), 
            CALCULATE(
                COUNTROWS(RR_Table),
                RR_Table[CompletionDate] = 
                    SELECTEDVALUE(DateTable[Date]),
                RR_Table[IsDueThisMonth] = TRUE(),
                RR_Table[RiskCategory] = SELECTEDVALUE(RR_Table[RiskCategory]),
                RR_Table[StatusCorpInd] = "KYC Completed"
            ),
        -- Grand Total across all days (horizontal total)
        SUMX(
            FILTER(RR_ColumnLabels, 
                NOT RR_ColumnLabels[Label] IN { "Total Due", "Completed", "Pending" }
            ),
            CALCULATE(
                COUNTROWS(RR_Table),
                RR_Table[IsDueThisMonth] = TRUE(),
                FORMAT(RR_Table[CompletionDate], "d MMM") = RR_ColumnLabels[Label],
                RR_Table[StatusCorpInd] = "KYC Completed"
            )
        )
    )

RR Matrix Value Fixed = 
VAR SelectedLabel = SELECTEDVALUE(RR_ColumnLabels[Label])
VAR SelectedDate =
    CALCULATE(
        MAX(DateTable[Date]),
        FILTER(DateTable,
            FORMAT(DateTable[Date], "d MMM") = SelectedLabel
        )
    )
VAR IsTotalRow = 
    NOT ISINSCOPE(RR_ColumnLabels[Label])

RETURN
SWITCH(
    TRUE(),
    SelectedLabel = "Total Due", [RR Total Due],
    SelectedLabel = "Completed", [RR Completed This Month],
    SelectedLabel = "Pending", [RR Pending This Month],
    
    // Individual day columns
    NOT IsTotalRow && NOT ISBLANK(SelectedDate),
        CALCULATE(
            COUNTROWS(RR_Table),
            RR_Table[CompletionDate] = SelectedDate,
            RR_Table[IsDueThisMonth] = TRUE(),
            RR_Table[StatusCorpInd] = "KYC Completed"
        ),

    // Grand total column (sum of all days)
    IsTotalRow,
        CALCULATE(
            COUNTROWS(RR_Table),
            RR_Table[IsDueThisMonth] = TRUE(),
            MONTH(RR_Table[CompletionDate]) = MONTH(TODAY()),
            YEAR(RR_Table[CompletionDate]) = YEAR(TODAY()),
            RR_Table[StatusCorpInd] = "KYC Completed"
        )
)


IsDueNextMonth = 
VAR DueDate = RR_Table[DueDateCalculated]  -- Replace with your due date column
VAR TodayDate = TODAY()
RETURN 
    NOT ISBLANK(DueDate) &&
    MONTH(DueDate) = MONTH(EOMONTH(TodayDate, 1)) &&
    YEAR(DueDate) = YEAR(EOMONTH(TodayDate, 1))
    
RR Total Due Next Month = 
CALCULATE(
    COUNTROWS(RR_Table),
    RR_Table[IsDueNextMonth] = TRUE()
)

RR Completed NextMonth_DoneThisMonth = 
CALCULATE(
    COUNTROWS(RR_Table),
    RR_Table[IsDueNextMonth] = TRUE(),
    RR_Table[StatusCorpInd] = "KYC Completed",
    MONTH(RR_Table[CompletionDate]) = MONTH(TODAY()),
    YEAR(RR_Table[CompletionDate]) = YEAR(TODAY())
)

RR Pending NextMonth = 
CALCULATE(
    COUNTROWS(RR_Table),
    RR_Table[IsDueNextMonth] = TRUE(),
    NOT RR_Table[StatusCorpInd] = "KYC Completed"
)

RR Matrix NextMonth = 
VAR SelectedLabel = SELECTEDVALUE(RR_ColumnLabels[Label])
VAR SelectedDate =
    CALCULATE(
        MAX(DateTable[Date]),
        FILTER(DateTable,
            FORMAT(DateTable[Date], "d MMM") = SelectedLabel
        )
    )
VAR IsTotalCol = NOT ISINSCOPE(RR_ColumnLabels[Label])

RETURN
SWITCH(
    TRUE(),
    SelectedLabel = "Total Due", [RR Total Due Next Month],
    SelectedLabel = "Completed", [RR Completed NextMonth_DoneThisMonth],
    SelectedLabel = "Pending", [RR Pending NextMonth],

    NOT IsTotalCol && NOT ISBLANK(SelectedDate),
        CALCULATE(
            COUNTROWS(RR_Table),
            RR_Table[IsDueNextMonth] = TRUE(),
            RR_Table[StatusCorpInd] = "KYC Completed",
            RR_Table[CompletionDate] = SelectedDate
        ),

    IsTotalCol,
        CALCULATE(
            COUNTROWS(RR_Table),
            RR_Table[IsDueNextMonth] = TRUE(),
            RR_Table[StatusCorpInd] = "KYC Completed",
            MONTH(RR_Table[CompletionDate]) = MONTH(TODAY()),
            YEAR(RR_Table[CompletionDate]) = YEAR(TODAY())
        )
)

RR_ColumnLabels_NextMonth = 
VAR NextMonthStart = DATE(YEAR(TODAY()), MONTH(TODAY()) + 1, 1)
VAR NextMonthEnd = EOMONTH(NextMonthStart, 0)

RETURN
UNION(
    DATATABLE("Label", STRING, {
        {"Total Due"},
        {"Completed"},
        {"Pending"}
    }),
    SELECTCOLUMNS(
        FILTER(
            DateTable,
            DateTable[Date] >= NextMonthStart &&
            DateTable[Date] <= NextMonthEnd
        ),
        "Label", FORMAT(DateTable[Date], "d MMM")
    )
)
SortOrder_NextMonth = 
SWITCH(
    TRUE(),
    RR_ColumnLabels_NextMonth[Label] = "Total Due", 1,
    RR_ColumnLabels_NextMonth[Label] = "Completed", 2,
    RR_ColumnLabels_NextMonth[Label] = "Pending", 3,
    TRUE, 
        3 + 
        DAY(
            DATEVALUE(
                RR_ColumnLabels_NextMonth[Label] & " " &
                FORMAT(EOMONTH(TODAY(), 1), "yyyy")
            )
        )
)


RR_ColumnLabels_NextMonth = 
VAR NextMonthStart = DATE(YEAR(TODAY()), MONTH(TODAY()) + 1, 1)
VAR NextMonthEnd = EOMONTH(NextMonthStart, 0)

RETURN
UNION(
    SELECTCOLUMNS(
        DATATABLE("Label", STRING, {
            {"Total Due"},
            {"Completed"},
            {"Pending"}
        }),
        "Label", [Label],
        "SortOrder", 
            SWITCH([Label],
                "Total Due", 1,
                "Completed", 2,
                "Pending", 3
            )
    ),
    SELECTCOLUMNS(
        ADDCOLUMNS(
            FILTER(
                DateTable,
                DateTable[Date] >= NextMonthStart &&
                DateTable[Date] <= NextMonthEnd
            ),
            "Label", FORMAT([Date], "d MMM"),
            "SortOrder", DAY([Date]) + 3
        ),
        "Label", [Label],
        "SortOrder", [SortOrder]
    )
)

RR_MatrixValues_NextMonth = 
VAR SelectedLabel = SELECTEDVALUE('RR_ColumnLabels_NextMonth'[Label])
VAR TodayDate = TODAY()

-- Base filters
VAR NextMonthStart = DATE(YEAR(TodayDate), MONTH(TodayDate) + 1, 1)
VAR NextMonthEnd = EOMONTH(NextMonthStart, 0)

-- Handle static labels
RETURN
SWITCH(
    TRUE(),
    
    SelectedLabel = "Total Due",
        CALCULATE(
            COUNTROWS(RRTable),
            RRTable[Due Date] >= NextMonthStart &&
            RRTable[Due Date] <= NextMonthEnd
        ),
    
    SelectedLabel = "Completed",
        CALCULATE(
            COUNTROWS(RRTable),
            RRTable[Due Date] >= NextMonthStart &&
            RRTable[Due Date] <= NextMonthEnd,
            RRTable[StatusCorpInd] = "KYC Completed",
            MONTH(RRTable[Completion Date]) = MONTH(TodayDate) &&
            YEAR(RRTable[Completion Date]) = YEAR(TodayDate)
        ),

    SelectedLabel = "Pending",
        CALCULATE(
            COUNTROWS(RRTable),
            RRTable[Due Date] >= NextMonthStart &&
            RRTable[Due Date] <= NextMonthEnd,
            NOT(RRTable[StatusCorpInd] = "KYC Completed")
            -- Add more conditions if needed for pending
        ),

    -- Handle dynamic date-based labels like "1 Aug", "2 Aug", ...
    -- Try parsing the label into date
    CALCULATE(
        COUNTROWS(RRTable),
        RRTable[Due Date] >= NextMonthStart &&
        RRTable[Due Date] <= NextMonthEnd,
        RRTable[StatusCorpInd] = "KYC Completed",
        FORMAT(RRTable[Completion Date], "d MMM") = SelectedLabel
    )
)