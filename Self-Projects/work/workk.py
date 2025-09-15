VAR TodayDate = TODAY()
VAR FirstOfCurrentMonth = DATE(YEAR(TodayDate), MONTH(TodayDate), 1)
VAR EndOfPrevMonth = EOMONTH(TodayDate, -1)
VAR FirstOfPrevMonth = DATE(YEAR(TodayDate), MONTH(TodayDate) - 1, 1)
VAR FifteenthOfCurrentMonth = DATE(YEAR(TodayDate), MONTH(TodayDate), 15)

VAR PrevMonthStart =
    IF(
        DAY(TodayDate) <= 15,
        FirstOfPrevMonth,
        FirstOfCurrentMonth
    )

VAR PrevMonthEnd =
    IF(
        DAY(TodayDate) <= 15,
        EndOfPrevMonth,
        FifteenthOfCurrentMonth
    )