// Individual day columns (completed OR cancelled)
NOT IsTotalRow && NOT ISBLANK(SelectedDate),
    CALCULATE(
        COUNTROWS(RR_Table),
        (
            ( RR_Table[CompletionDate] = SelectedDate
              && RR_Table[StatusCorpInd] = "KYC Completed"
            )
            ||
            ( RR_Table[ClosureDate] = SelectedDate
              && RR_Table[RR_Status] = "Cancelled"
            )
        ),
        RR_Table[Flag_Due] = TRUE()
            || RR_Table[Flag_Due_Next] = TRUE()
    )