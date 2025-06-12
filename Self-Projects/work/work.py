Calendar = 
VAR StartDate = DATE(2022, 1, 1)
VAR EndDate = DATE(2026, 12, 31)
RETURN
ADDCOLUMNS (
    CALENDAR (StartDate, EndDate),
    "IsWorkingDay",
        IF (
            WEEKDAY ( [Date], 2 ) <= 5,
            TRUE(),
            FALSE()
        )
)