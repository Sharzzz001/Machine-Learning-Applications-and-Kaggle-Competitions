Adjusted Start Date =
VAR ApprovedDateTime = 'LCO Tracker'[ApprovedDate] + TIME(8,0,0)   -- add 8 hours (SGT)
VAR BaseDate = DATEVALUE(ApprovedDateTime)                         -- strip time
VAR RequestTimeFlag = 'LCO Tracker'[SubmissionTime]                -- TRUE/FALSE

-- First: find the business day after timezone shift
VAR FirstBizDay =
    CALCULATE(
        MIN('Calendar'[Date]),
        FILTER(
            'Calendar',
            'Calendar'[Date] >= BaseDate &&
            'Calendar'[IsWorkingDay] = TRUE
        )
    )

-- If RequestTime = TRUE, add one more business day on top of FirstBizDay
VAR SecondBizDay =
    CALCULATE(
        MIN('Calendar'[Date]),
        FILTER(
            'Calendar',
            'Calendar'[Date] > FirstBizDay &&
            'Calendar'[IsWorkingDay] = TRUE
        )
    )

RETURN
    IF(RequestTimeFlag = TRUE, SecondBizDay, FirstBizDay)