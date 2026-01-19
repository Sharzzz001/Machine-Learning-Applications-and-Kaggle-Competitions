AgeingDays =
DATEDIFF(
    DocDeficiency_Fact[DocDefiStartDate],
    TODAY(),
    DAY
)

AgeingDays =
NETWORKDAYS(
    DocDeficiency_Fact[DocDefiStartDate],
    TODAY()
)

HasFCCExtension =
IF(
    NOT ISBLANK(DocDeficiency_Fact[ExtendedDeadline]),
    "Yes",
    "No"
)

AgeingBucket =
VAR Age = DocDeficiency_Fact[AgeingDays]
VAR HasExt =
    NOT ISBLANK(DocDeficiency_Fact[ExtendedDeadline])
RETURN
SWITCH(
    TRUE(),

    Age <= 30,
        "0–30 Days",

    Age > 30 && HasExt,
        ">30 Days – With FCC Extension",

    Age > 30 && NOT HasExt && Age <= 100,
        ">30 Days – Without FCC Extension",

    Age > 100 && Age <= 120,
        ">100 Days",

    Age > 120,
        ">120 Days",

    "Unknown"
)

MitigatingActions =
DATATABLE(
    "AgeingBucket", STRING,
    "MitigatingAction", STRING,
    {
        {
            "0–30 Days",
            "Full block. Escalated to Team Head and Group Head."
        },
        {
            ">30 Days – With FCC Extension",
            "Full block. Escalated to Team Head, Group Head, Compliance and BM."
        },
        {
            ">30 Days – Without FCC Extension",
            "Full block. Escalated to Team Head and Group Head."
        },
        {
            ">100 Days",
            "Full block. Senior management escalation initiated."
        },
        {
            ">120 Days",
            "Critical breach. Immediate remediation and regulatory escalation."
        }
    }
)

link
DocDeficiency_Fact[AgeingBucket]
        ↓
MitigatingActions[AgeingBucket]


PendingAccounts :=
DISTINCTCOUNT(
    DocDeficiency_Fact[AccountNumber]
)

Account_Age_Action_Dim =
DATATABLE(
    "Account_Age_Bucket", STRING,
    "Mitigating_Action", STRING,
    "Sort_Order", INTEGER,
    {
        { "<30 Days", "New account – monitoring stage.", 1 },
        { "30–90 Days", "Follow-up with onboarding team.", 2 },
        { "91–180 Days", "Escalation to compliance and relationship manager.", 3 },
        { ">180 Days", "High-risk vintage – senior management review.", 4 },
        { "No Start Date", "Account open date missing – data remediation required.", 5 }
    }
)




