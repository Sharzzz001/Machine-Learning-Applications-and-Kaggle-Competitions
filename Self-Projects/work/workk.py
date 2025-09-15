Report Label =
VAR TodayDate = TODAY()
VAR FirstOfMonth = DATE(YEAR(TodayDate), MONTH(TodayDate), 1)
VAR EndPrevMonth = EOMONTH(TodayDate, -1)
VAR FifteenthThisMonth = DATE(YEAR(TodayDate), MONTH(TodayDate), 15)
RETURN
    IF(
        DAY(TodayDate) <= 15,
        "Report as of " & FORMAT(EndPrevMonth, "DD MMMM"),
        "Report as of " & FORMAT(FifteenthThisMonth, "DD MMMM")
    )