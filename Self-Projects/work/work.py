Calendar = 
ADDCOLUMNS(
    CALENDAR(DATE(2022,1,1), DATE(2026,12,31)),
    "IsWorkingDay", 
        IF (
            WEEKDAY([Date], 2) <= 5,   -- 2 = Monday, 7 = Sunday
            TRUE(),
            FALSE()
        )
)