Ageing Bucket = 
SWITCH(
    TRUE(),
    'YourTable'[Total Ageing] <= 5, "0-5 Days",
    'YourTable'[Total Ageing] <= 10, "6-10 Days",
    "11+ Days"
)