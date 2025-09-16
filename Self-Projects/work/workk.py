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


CALCULATE (
            COUNTROWS ( RR_Table ),
            (
                ( MONTH ( RR_Table[CompletionDate] ) = MONTH ( TODAY() )
                  && YEAR ( RR_Table[CompletionDate] ) = YEAR ( TODAY() )
                  && RR_Table[StatusCorpInd] = "KYC Completed"
                )
                ||
                ( MONTH ( RR_Table[ClosureDate] ) = MONTH ( TODAY() )
                  && YEAR ( RR_Table[ClosureDate] ) = YEAR ( TODAY() )
                  && RR_Table[RR_Status] = "Cancelled"
                )
            ),
            RR_Table[Flag_Due] = TRUE()
                || RR_Table[Flag_Due_Next] = TRUE()
        )
)