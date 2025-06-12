Calendar = 
ADDCOLUMNS (
    CALENDAR (
        DATE( YEAR(CALCULATE(MIN('Table'[Request Date]))), 
              MONTH(CALCULATE(MIN('Table'[Request Date]))), 
              DAY(CALCULATE(MIN('Table'[Request Date]))) 
        ),
        DATE( YEAR(CALCULATE(MAX('Table'[Checker Completion Date]))) + 1, 
              1, 1 
        )
    ),
    "IsWorkday", WEEKDAY([Date], 2) <= 5
)