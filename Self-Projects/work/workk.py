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

Al (investor class), Al (investor class) (No physicals required), IM Pack, Product features & Risk disclosure, IM Pack, Product features & Risk disclosure (Physicals required, IRPQ / Portfolio Waiver, IRPQ / Portfolio Waiver (No physicals required), IRPQ Attestation, IRPO Attestation (No physicals required), IRPQ Attestation Doc upload, IRPQ DOCM dates update, IRPQ DOCM dates update (No physicals required), IRPQ questionnaire (upgrade/ downgrade) (Physicals required), IRPQ upload, VC and Non VC, or VC and Non VC (No physicals required)

CDP/CDS, CDP/CDS (No physicals required), Commission, Commission (No physicals required), Custody Fees, Custody Fees (No physicals required), Sales Code Transfer (No physicals required), SSI Priority, SSI Priority (No physicals required), or Sales Code Transfer

Audit Confirmation, Audit Confirmation (Physicals required), Bank Reference Letter, Bank Reference Letter (Physicals required), DEC avaloq, DEC avaloq (Physicals required), DEC Letter, DEC Letter creation (No physicals required), E-Platform, E-Platform hard token (Physicals required), E-Platform Hard token Acknowledgment form (Physicals required), E-Platform hard token removal (No physicals required), Platform Paperless Consent letter, E-Platform Paperless Consent letter (Physicals required), E-Platform Soft Token - Migration (No physicals required), E-Platform Soft Token - New (Physicals required), E-Platform Soft Token (migration), E-Platform Soft Token (new), IA Tagging (No physicals required), or IA Tagging

SLA_Summary =
UNION(
    ROW("Process", "Account Lifecycle", "SLA_Percentage", [SLA_Percentage_AccountLifecycle]),
    ROW("Process", "Review",            "SLA_Percentage", [SLA_Percentage_Review]),
    ROW("Process", "XYZ",               "SLA_Percentage", [SLA_Percentage_XYZ])
)
