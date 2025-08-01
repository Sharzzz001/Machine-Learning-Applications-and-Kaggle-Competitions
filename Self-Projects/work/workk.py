#Pending Accounts by Bucket = 
VAR _bucket = SELECTEDVALUE('AgingBuckets'[Bucket])
VAR _count =
    SWITCH(
        TRUE(),
        _bucket = "0-30 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] <= 30, 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days with FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, NOT(ISBLANK('FactTable'[ExtendedDeadline])), 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days without FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, ISBLANK('FactTable'[ExtendedDeadline]), 'FactTable'[Status] = "Pending"),
        _bucket = ">100 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 100, 'FactTable'[Status] = "Pending"),
        _bucket = ">120 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 120, 'FactTable'[Status] = "Pending")
    )
RETURN COALESCE(_count, 0)

Action Comment Display = 
VAR _count = [Pending Accounts by Bucket]
RETURN IF(_count > 0, "Escalated to Team/ Group Head", "-")

Action Comment Display =
VAR _bucket = SELECTEDVALUE(AgingBucket[AgingBucket])
VAR _comment = LOOKUPVALUE(AgingBucket[ActionComment], AgingBucket[AgingBucket], _bucket)
VAR _count = [Pending Accounts by Bucket]  -- your existing measure

RETURN 
IF(_count > 0, _comment, "-")

Action Comment Display =
VAR _isTotalRow = NOT ISINSCOPE(AgingBucket[AgingBucket])
VAR _bucket = SELECTEDVALUE(AgingBucket[AgingBucket])
VAR _comment =
    LOOKUPVALUE(AgingBucket[ActionComment], AgingBucket[AgingBucket], _bucket)
VAR _count = [Pending Accounts by Bucket]

RETURN
    SWITCH(
        TRUE(),
        _isTotalRow, BLANK(),  -- Or "Summary row" if you want
        _count > 0, _comment,
        "-"
    )
    
Action Comment Display = 
VAR _isTotalRow = NOT ISINSCOPE(AgingBucket[AgingBucket])
VAR _bucket = SELECTEDVALUE(AgingBucket[AgingBucket])
VAR _comment = 
    LOOKUPVALUE(
        AgingBucket[ActionComment],
        AgingBucket[AgingBucket],
        _bucket
    )
VAR _count = [Pending Accounts by Bucket]

RETURN
SWITCH(
    TRUE(),
    _isTotalRow, BLANK(),  // You can replace BLANK() with "Total Comment" if desired
    _count > 0, _comment,
    "-"
)

Pending Accounts by Bucket = 
VAR _bucket = SELECTEDVALUE('AgingBuckets'[Bucket], "NO_BUCKET")
VAR _count =
    SWITCH(
        TRUE(),
        _bucket = "0-30 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] <= 30, 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days with FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, NOT(ISBLANK('FactTable'[ExtendedDeadline])), 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days without FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, ISBLANK('FactTable'[ExtendedDeadline]), 'FactTable'[Status] = "Pending"),
        _bucket = ">100 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 100, 'FactTable'[Status] = "Pending"),
        _bucket = ">120 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 120, 'FactTable'[Status] = "Pending"),
        "NO_BUCKET", BLANK()
    )
RETURN _count


Action Comment Display =
VAR _isTotalRow = NOT ISINSCOPE('AgingBuckets'[Bucket])
VAR _bucket = SELECTEDVALUE('AgingBuckets'[Bucket])
VAR _comment =
    LOOKUPVALUE(
        'AgingBuckets'[ActionComment],
        'AgingBuckets'[Bucket], _bucket
    )
VAR _count = [Pending Accounts by Bucket]
RETURN
SWITCH(
    TRUE(),
    _isTotalRow, BLANK(),         -- (Or "Total" if you want a label)
    _count > 0, _comment,
    "-"
)


Pending Accounts by Bucket = 
VAR _hasBucket = HASONEVALUE('AgingBuckets'[Bucket])
RETURN 
IF(
    _hasBucket,
    SWITCH(
        VALUES('AgingBuckets'[Bucket]),
        "0-30 Days", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] <= 30,
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        ">30 Days with FCC Extension", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 30,
                    NOT(ISBLANK('FactTable'[ExtendedDeadline])), 
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        ">30 Days without FCC Extension", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 30,
                    ISBLANK('FactTable'[ExtendedDeadline]), 
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        ">100 Days", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 100, 
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        ">120 Days", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 120, 
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        BLANK()
    ),
    // Total row - sum of all visible buckets
    SUMX(
        VALUES('AgingBuckets'[Bucket]),
        SWITCH(
            'AgingBuckets'[Bucket],
            "0-30 Days", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] <= 30,
                    'FactTable'[Status] = "Pending"
                ),
            ">30 Days with FCC Extension", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 30,
                    NOT(ISBLANK('FactTable'[ExtendedDeadline])), 
                    'FactTable'[Status] = "Pending"
                ),
            ">30 Days without FCC Extension", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 30,
                    ISBLANK('FactTable'[ExtendedDeadline]), 
                    'FactTable'[Status] = "Pending"
                ),
            ">100 Days", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 100, 
                    'FactTable'[Status] = "Pending"
                ),
            ">120 Days", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 120, 
                    'FactTable'[Status] = "Pending"
                ),
            0
        )
    )
)


Pending Accounts by Bucket = 
VAR _bucket = SELECTEDVALUE('AgingBuckets'[Bucket])
VAR _isTotal = NOT ISINSCOPE('AgingBuckets'[Bucket])

VAR _count =
    SWITCH(
        TRUE(),
        _bucket = "0-30 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] <= 30, 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days with FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, NOT(ISBLANK('FactTable'[ExtendedDeadline])), 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days without FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, ISBLANK('FactTable'[ExtendedDeadline]), 'FactTable'[Status] = "Pending"),
        _bucket = ">100 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 100, 'FactTable'[Status] = "Pending"),
        _bucket = ">120 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 120, 'FactTable'[Status] = "Pending")
    )

-- For totals, add up each bucket manually
VAR _total =
    CALCULATE(
        DISTINCTCOUNT('FactTable'[AccountID]),
        'FactTable'[Status] = "Pending"
    )

RETURN 
    IF(_isTotal, _total, COALESCE(_count, 0))


RR Matrix Value Fixed = 
VAR SelectedLabel = SELECTEDVALUE(RR_ColumnLabels[Label])
VAR SelectedDate =
    CALCULATE(
        MAX(DateTable[Date]),
        FILTER(DateTable,
            FORMAT(DateTable[Date], "d MMM") = SelectedLabel
        )
    )
VAR IsTotalRow = NOT ISINSCOPE(RR_ColumnLabels[Label])

VAR Result =
    SWITCH(
        TRUE(),
        SelectedLabel = "Total Due", [RR Total Due],
        SelectedLabel = "Completed", [RR Completed This Month],
        SelectedLabel = "Pending", [RR Pending This Month],

        NOT IsTotalRow && NOT ISBLANK(SelectedDate),
            CALCULATE(
                COUNTROWS(RR_Table),
                RR_Table[CompletionDate] = SelectedDate,
                RR_Table[IsDueThisMonth] = TRUE(),
                RR_Table[StatusCorpInd] = "KYC Completed"
            ),

        IsTotalRow,
            CALCULATE(
                COUNTROWS(RR_Table),
                RR_Table[IsDueThisMonth] = TRUE(),
                RR_Table[StatusCorpInd] = "KYC Completed",
                MONTH(RR_Table[CompletionDate]) = MONTH(TODAY()),
                YEAR(RR_Table[CompletionDate]) = YEAR(TODAY())
            )
    )

RETURN
    IF(ISBLANK(Result), 0, Result)




IsDueNextMonthOrLater = 
VAR DueDate = RR_Table[Due Date]
RETURN
    NOT ISBLANK(DueDate) &&
    DueDate > EOMONTH(TODAY(), 0)
    
    
RR Total Due NextMonth = 
CALCULATE(
    COUNTROWS(RR_Table),
    RR_Table[IsDueNextMonthOrLater] = TRUE()
)

RR Completed This Month for NextMonthDue = 
CALCULATE(
    COUNTROWS(RR_Table),
    RR_Table[IsDueNextMonthOrLater] = TRUE(),
    RR_Table[StatusCorpInd] = "KYC Completed",
    MONTH(RR_Table[CompletionDate]) = MONTH(TODAY()),
    YEAR(RR_Table[CompletionDate]) = YEAR(TODAY())
)

RR Pending NextMonthDue = 
CALCULATE(
    COUNTROWS(RR_Table),
    RR_Table[IsDueNextMonthOrLater] = TRUE(),
    RR_Table[StatusCorpInd] <> "KYC Completed"
)

RR Matrix Value NextMonthDue = 
VAR SelectedLabel = SELECTEDVALUE(RR_ColumnLabels[Label])
VAR SelectedDate =
    CALCULATE(
        MAX(DateTable[Date]),
        FILTER(DateTable,
            FORMAT(DateTable[Date], "d MMM") = SelectedLabel
        )
    )
VAR IsTotalRow = NOT ISINSCOPE(RR_ColumnLabels[Label])

VAR Result =
    SWITCH(
        TRUE(),
        SelectedLabel = "Total Due", [RR Total Due NextMonth],
        SelectedLabel = "Completed", [RR Completed This Month for NextMonthDue],
        SelectedLabel = "Pending", [RR Pending NextMonthDue],

        NOT IsTotalRow && NOT ISBLANK(SelectedDate),
            CALCULATE(
                COUNTROWS(RR_Table),
                RR_Table[IsDueNextMonthOrLater] = TRUE(),
                RR_Table[CompletionDate] = SelectedDate,
                RR_Table[StatusCorpInd] = "KYC Completed"
            ),

        IsTotalRow,
            CALCULATE(
                COUNTROWS(RR_Table),
                RR_Table[IsDueNextMonthOrLater] = TRUE(),
                RR_Table[StatusCorpInd] = "KYC Completed",
                MONTH(RR_Table[CompletionDate]) = MONTH(TODAY()),
                YEAR(RR_Table[CompletionDate]) = YEAR(TODAY())
            )
    )

RETURN
    IF(ISBLANK(Result), 0, Result)

