Calendar = 
ADDCOLUMNS (
    CALENDAR(DATE(2022, 1, 1), DATE(2026, 12, 31)),
    "IsWorkingDay",
        VAR ThisDate = [Date]
        RETURN IF (
            WEEKDAY(ThisDate, 2) <= 5,  -- 2 = Monday, 6/7 = weekend
            TRUE(),
            FALSE()
        )
)