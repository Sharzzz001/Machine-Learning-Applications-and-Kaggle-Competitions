CalendarDays_Aging =
DATEDIFF('Table'[StartDate], TODAY(), DAY)


Aging_Bucket =
SWITCH(
    TRUE(),
    ISBLANK('Table'[StartDate]), "No Start Date",
    'Table'[CalendarDays_Aging] <= 30, "0–30 Days",
    'Table'[CalendarDays_Aging] > 30 && NOT(ISBLANK('Table'[Extended Deadline])) && 'Table'[CalendarDays_Aging] <= 100, ">30 Days with FCC Extension",
    'Table'[CalendarDays_Aging] > 30 && ISBLANK('Table'[Extended Deadline]) && 'Table'[CalendarDays_Aging] <= 100, ">30 Days without FCC Extension",
    'Table'[CalendarDays_Aging] > 100 && 'Table'[CalendarDays_Aging] <= 120, ">100 Days",
    'Table'[CalendarDays_Aging] > 120, ">120 Days",
    BLANK()
)


Pending_Accounts_Count =
CALCULATE(
    DISTINCTCOUNT('Table'[Account ID]),
    'Table'[Doc Status] = "Pending"
)

Aging_Bucket_Sort =
DATATABLE(
    "Aging_Bucket", STRING,
    "SortOrder", INTEGER,
    {
        { "0–30 Days", 1 },
        { ">30 Days with FCC Extension", 2 },
        { ">30 Days without FCC Extension", 3 },
        { ">100 Days", 4 },
        { ">120 Days", 5 },
        { "No Start Date", 6 }
    }
)

