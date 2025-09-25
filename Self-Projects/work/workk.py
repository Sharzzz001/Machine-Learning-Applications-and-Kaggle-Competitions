Overdue Bucket =
SWITCH (
    TRUE(),
    [Age to Completion] >= 0, "Not Overdue",
    [Age to Completion] < 0 && [Age to Completion] >= -10, "0-10 days overdue",
    [Age to Completion] < -10 && [Age to Completion] >= -30, "10-30 days overdue",
    [Age to Completion] < -30 && [Age to Completion] >= -60, "30-60 days overdue",
    [Age to Completion] < -60, "60+ days overdue",
    BLANK()
)