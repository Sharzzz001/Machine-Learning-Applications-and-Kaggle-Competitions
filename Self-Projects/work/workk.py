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

RAG_Table =
UNION(
    ROW( "Team", "Account Opening", "Process", "Document Review (VIP/Non-VIP)", "SLA_Percentage", 0.98 ),
    ROW( "Team", "Account Opening", "Process", "Name Screening (<30 hits, VIP/Non-VIP)", "SLA_Percentage", 0.92 ),
    ROW( "Team", "Account Opening", "Process", "Name Screening (>30 hits, VIP/Non-VIP)", "SLA_Percentage", 1.00 ),
    ROW( "Team", "Rolling Reviews", "Process", "Prospects Creation", "SLA_Percentage", 0.99 ),
    ROW( "Team", "Rolling Reviews", "Process", "Static Setup", "SLA_Percentage", 0.83 ),
    ROW( "Team", "Rolling Reviews", "Process", "Document Review", "SLA_Percentage", 0.875 ),
    ROW( "Team", "Rolling Reviews", "Process", "Name Screening (<30 hits)", "SLA_Percentage", 1.00 ),
    ROW( "Team", "Rolling Reviews", "Process", "Name Screening (>30 hits)", "SLA_Percentage", 1.00 ),
    ROW( "Team", "Products & Services - Static", "Process", "Static Setup", "SLA_Percentage", 0.86 ),
    ROW( "Team", "Products & Services - Static", "Process", "Account Closures", "SLA_Percentage", 0.65 ),
    ROW( "Team", "Products & Services - Static", "Process", "Client Certification / Attestations", "SLA_Percentage", 0.655 ),
    ROW( "Team", "Products & Services - Static", "Process", "Products & Services enablement", "SLA_Percentage", 0.805 ),
    ROW( "Team", "Products & Services - Static", "Process", "Address/Contact details updates; Deceased a/cs", "SLA_Percentage", 0.85 ),
    ROW( "Team", "Products & Services - Static", "Process", "Blocking & Unblocking of Accounts", "SLA_Percentage", 1.00 ),
    ROW( "Team", "Products & Services - Static", "Process", "Operational Client Updates", "SLA_Percentage", 0.845 ),
    ROW( "Team", "Products & Services - Static", "Process", "Document Review", "SLA_Percentage", 0.935 ),
    ROW( "Team", "Products & Services - Static", "Process", "Limit Setups", "SLA_Percentage", 0.755 ),
    ROW( "Team", "Products & Services - Static", "Process", "Facility Cancellation", "SLA_Percentage", 1.00 ),
    ROW( "Team", "Products & Services - LCO", "Process", "Letter Issuance (non-credit grp)", "SLA_Percentage", 0.755 ),
    ROW( "Team", "Products & Services - LCO", "Process", "Letter Issuance (credit grp)", "SLA_Percentage", 0.675 ),
    ROW( "Team", "Products & Services - LCO", "Process", "Insurance/Mortgage Financing", "SLA_Percentage", 0.00 ),
    ROW( "Team", "Products & Services - LCO", "Process", "Limit Reduction", "SLA_Percentage", 1.00 ),
    ROW( "Team", "Products & Services - LCO", "Process", "Renewal", "SLA_Percentage", BLANK() )
)

TeamSort =
DATATABLE (
    "Team", STRING,
    "SortOrder", INTEGER,
    {
        { "Account Opening", 1 },
        { "Rolling Reviews", 2 },
        { "Products & Services - Static", 3 },
        { "Products & Services - LCO", 4 }
    }
)

RR Matrix Value NextMonthDue =
VAR CurrentMonthStart =
    DATE ( YEAR ( TODAY() ), MONTH ( TODAY() ), 1 )
VAR CurrentMonthEnd =
    EOMONTH ( TODAY(), 0 )
VAR DueCutoff -- anything due AFTER end of current month
    = CurrentMonthEnd

VAR SelectedLabel =
    SELECTEDVALUE ( RR_ColumnLabels[Label] )

VAR IsTotalCol =
    NOT ISINSCOPE ( RR_ColumnLabels[Label] )

VAR IsStaticLabel =
    CONTAINSROW ( { "Total Due", "Completed", "Pending" }, SelectedLabel )

-- Only try to resolve a date when we are on a day label (not totals)
VAR SelectedDate =
    IF (
        NOT IsStaticLabel && NOT IsTotalCol,
        CALCULATE (
            MAX ( DateTable[Date] ),
            KEEPFILTERS (
                FILTER (
                    DateTable,
                    DateTable[Date] >= CurrentMonthStart
                        && DateTable[Date] <= CurrentMonthEnd
                        && FORMAT ( DateTable[Date], "d MMM" ) = SelectedLabel
                )
            )
        )
    )

-- Common filters
VAR Filter_DueNextMonthOrLater =
    RR_Table[Due Date] > DueCutoff

VAR Filter_CompletedThisMonth =
    RR_Table[StatusCorpInd] = "KYC Completed"
        && RR_Table[CompletionDate] >= CurrentMonthStart
        && RR_Table[CompletionDate] <= CurrentMonthEnd

RETURN
VAR Result =
    SWITCH (
        TRUE (),

        /* Static columns */
        SelectedLabel = "Total Due",
            CALCULATE (
                COUNTROWS ( RR_Table ),
                Filter_DueNextMonthOrLater
            ),

        SelectedLabel = "Pending",
            CALCULATE (
                COUNTROWS ( RR_Table ),
                Filter_DueNextMonthOrLater,
                RR_Table[StatusCorpInd] <> "KYC Completed"
            ),

        SelectedLabel = "Completed",
            CALCULATE (
                COUNTROWS ( RR_Table ),
                Filter_DueNextMonthOrLater,
                Filter_CompletedThisMonth
            ),

        /* Day columns: one date in current month */
        NOT IsStaticLabel && NOT IsTotalCol && NOT ISBLANK ( SelectedDate ),
            CALCULATE (
                COUNTROWS ( RR_Table ),
                Filter_DueNextMonthOrLater,
                RR_Table[StatusCorpInd] = "KYC Completed",
                INT ( RR_Table[CompletionDate] ) = SelectedDate   -- strip time
            ),

        /* Rightmost grand total (sum of day columns) */
        IsTotalCol,
            CALCULATE (
                COUNTROWS ( RR_Table ),
                Filter_DueNextMonthOrLater,
                Filter_CompletedThisMonth
            )
    )
RETURN
    COALESCE ( Result, 0 )


= if [DueDate] = null or Text.Trim([DueDate]) = "" then null 
  else if Text.Contains([DueDate], "T") 
    then DateTime.Date(DateTime.FromText([DueDate])) 
  else try Date.FromText([DueDate]) otherwise Date.FromText(Text.Replace([DueDate],"/","-"))

flag_due =
VAR CurrentMonthStart = DATE(YEAR(TODAY()), MONTH(TODAY()), 1)
VAR TwoMonthsAheadEnd = EDATE(CurrentMonthStart, 2) - 1
RETURN
IF(
    'Table'[DueDate] <= TwoMonthsAheadEnd,
    TRUE(),
    FALSE()
)