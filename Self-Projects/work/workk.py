Due_Age_Bucket = 
SWITCH(
    TRUE(),
    'YourTable'[Age_To_Completion] <= 30, "0–30 Days",
    'YourTable'[Age_To_Completion] <= 60, "31–60 Days",
    'YourTable'[Age_To_Completion] <= 90, "61–90 Days",
    "90+ Days"
)

Due_Age_Bucket_Sort =
SWITCH(
    TRUE(),
    'YourTable'[Due_Age_Bucket] = "0–30 Days", 1,
    'YourTable'[Due_Age_Bucket] = "31–60 Days", 2,
    'YourTable'[Due_Age_Bucket] = "61–90 Days", 3,
    4
)