Region =
VAR FullText = 'Table'[UserName]
VAR StartPos = FIND("/", FullText, 1, -1)
VAR EndPos   = FIND(")", FullText, StartPos, -1)
RETURN
IF (
    StartPos > 0 && EndPos > 0,
    MID(
        FullText,
        StartPos + 1,
        EndPos - StartPos - 1
    ),
    BLANK()
)