Due_Age_Bucket = 
SWITCH(
    TRUE(),
    'YourTable'[Age_To_Completion] <= 30, "0–30 Days",
    'YourTable'[Age_To_Completion] <= 60, "31–60 Days",
    'YourTable'[Age_To_Completion] <= 90, "61–90 Days",
    "90+ Days"
)