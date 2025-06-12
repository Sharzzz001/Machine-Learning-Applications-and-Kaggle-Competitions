Calendar = 
ADDCOLUMNS (
    CALENDAR (
        CALCULATE ( MIN ( 'Table'[Request Date] ) ),
        CALCULATE ( MAX ( 'Table'[Checker Completion Date] ) ) + 365
    ),
    "IsWorkday", WEEKDAY([Date], 2) <= 5
)