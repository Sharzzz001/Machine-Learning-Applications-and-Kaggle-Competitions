Pending Accounts by Bucket = 
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