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