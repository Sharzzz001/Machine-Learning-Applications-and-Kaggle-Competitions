ROW (
    "Team", "Account Opening",
    "Process", "Document Review (VIP/Non-VIP)",
    "SLA_Percentage", [SLA_DocumentReview_VIP],
    "Comments",
        IF (
            ISBLANK([SLA_DocumentReview_VIP]),
            "No cases",
            IF (
                [SLA_DocumentReview_VIP] > 0.8,
                "-",
                "Your static comment here"
            )
        )
)