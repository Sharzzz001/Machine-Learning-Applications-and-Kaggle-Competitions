SLA_Percentage =
VAR TotalRows =
    CALCULATE(
        COUNTROWS('Data'),
        'Data'[Process] = "Account Lifecycle",              -- Process condition
        NOT 'Data'[RequestType] IN { "TypeA", "TypeB" },     -- Exclusions
        'Data'[RequestDate] <> BLANK(),                      -- Must have start date
        'Data'[CompletionDate] <> BLANK()                    -- Must have end date
    )
VAR MetRows =
    CALCULATE(
        COUNTROWS('Data'),
        'Data'[Process] = "Account Lifecycle",
        NOT 'Data'[RequestType] IN { "TypeA", "TypeB" },
        'Data'[RequestDate] <> BLANK(),
        'Data'[CompletionDate] <> BLANK(),
        VAR SLA_Days = IF('Data'[Urgent], 1, 3)
        VAR ActualDays =
            NETWORKDAYS('Data'[RequestDate], 'Data'[CompletionDate])
        RETURN ActualDays <= SLA_Days
    )
RETURN
DIVIDE(MetRows, TotalRows, 0)


SLA_Percentage =
VAR TotalRows =
    CALCULATE(
        COUNTROWS('Data'),
        'Data'[SLA_Status] IN { "Met", "Breached" }
        -- Add your process-specific filter conditions here:
        -- 'Data'[Process] = "Account Lifecycle",
        -- 'Data'[OtherColumn] = "SomeValue"
    )
VAR MetRows =
    CALCULATE(
        COUNTROWS('Data'),
        'Data'[SLA_Status] = "Met"
        -- Same filters as above so they match exactly
        -- 'Data'[Process] = "Account Lifecycle",
        -- 'Data'[OtherColumn] = "SomeValue"
    )
RETURN
DIVIDE(MetRows, TotalRows, 0)