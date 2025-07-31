#Pending Accounts by Bucket = 
VAR _bucket = SELECTEDVALUE('AgingBuckets'[Bucket])
VAR _count =
    SWITCH(
        TRUE(),
        _bucket = "0-30 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] <= 30, 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days with FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, NOT(ISBLANK('FactTable'[ExtendedDeadline])), 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days without FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, ISBLANK('FactTable'[ExtendedDeadline]), 'FactTable'[Status] = "Pending"),
        _bucket = ">100 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 100, 'FactTable'[Status] = "Pending"),
        _bucket = ">120 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 120, 'FactTable'[Status] = "Pending")
    )
RETURN COALESCE(_count, 0)

Action Comment Display = 
VAR _count = [Pending Accounts by Bucket]
RETURN IF(_count > 0, "Escalated to Team/ Group Head", "-")

Action Comment Display =
VAR _bucket = SELECTEDVALUE(AgingBucket[AgingBucket])
VAR _comment = LOOKUPVALUE(AgingBucket[ActionComment], AgingBucket[AgingBucket], _bucket)
VAR _count = [Pending Accounts by Bucket]  -- your existing measure

RETURN 
IF(_count > 0, _comment, "-")

Action Comment Display =
VAR _isTotalRow = NOT ISINSCOPE(AgingBucket[AgingBucket])
VAR _bucket = SELECTEDVALUE(AgingBucket[AgingBucket])
VAR _comment =
    LOOKUPVALUE(AgingBucket[ActionComment], AgingBucket[AgingBucket], _bucket)
VAR _count = [Pending Accounts by Bucket]

RETURN
    SWITCH(
        TRUE(),
        _isTotalRow, BLANK(),  -- Or "Summary row" if you want
        _count > 0, _comment,
        "-"
    )
    
Action Comment Display = 
VAR _isTotalRow = NOT ISINSCOPE(AgingBucket[AgingBucket])
VAR _bucket = SELECTEDVALUE(AgingBucket[AgingBucket])
VAR _comment = 
    LOOKUPVALUE(
        AgingBucket[ActionComment],
        AgingBucket[AgingBucket],
        _bucket
    )
VAR _count = [Pending Accounts by Bucket]

RETURN
SWITCH(
    TRUE(),
    _isTotalRow, BLANK(),  // You can replace BLANK() with "Total Comment" if desired
    _count > 0, _comment,
    "-"
)

Pending Accounts by Bucket = 
VAR _bucket = SELECTEDVALUE('AgingBuckets'[Bucket], "NO_BUCKET")
VAR _count =
    SWITCH(
        TRUE(),
        _bucket = "0-30 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] <= 30, 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days with FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, NOT(ISBLANK('FactTable'[ExtendedDeadline])), 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days without FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, ISBLANK('FactTable'[ExtendedDeadline]), 'FactTable'[Status] = "Pending"),
        _bucket = ">100 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 100, 'FactTable'[Status] = "Pending"),
        _bucket = ">120 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 120, 'FactTable'[Status] = "Pending"),
        "NO_BUCKET", BLANK()
    )
RETURN _count


Action Comment Display =
VAR _isTotalRow = NOT ISINSCOPE('AgingBuckets'[Bucket])
VAR _bucket = SELECTEDVALUE('AgingBuckets'[Bucket])
VAR _comment =
    LOOKUPVALUE(
        'AgingBuckets'[ActionComment],
        'AgingBuckets'[Bucket], _bucket
    )
VAR _count = [Pending Accounts by Bucket]
RETURN
SWITCH(
    TRUE(),
    _isTotalRow, BLANK(),         -- (Or "Total" if you want a label)
    _count > 0, _comment,
    "-"
)


Pending Accounts by Bucket = 
VAR _hasBucket = HASONEVALUE('AgingBuckets'[Bucket])
RETURN 
IF(
    _hasBucket,
    SWITCH(
        VALUES('AgingBuckets'[Bucket]),
        "0-30 Days", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] <= 30,
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        ">30 Days with FCC Extension", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 30,
                    NOT(ISBLANK('FactTable'[ExtendedDeadline])), 
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        ">30 Days without FCC Extension", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 30,
                    ISBLANK('FactTable'[ExtendedDeadline]), 
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        ">100 Days", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 100, 
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        ">120 Days", 
            COALESCE(
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 120, 
                    'FactTable'[Status] = "Pending"
                ), 
                0
            ),
        BLANK()
    ),
    // Total row - sum of all visible buckets
    SUMX(
        VALUES('AgingBuckets'[Bucket]),
        SWITCH(
            'AgingBuckets'[Bucket],
            "0-30 Days", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] <= 30,
                    'FactTable'[Status] = "Pending"
                ),
            ">30 Days with FCC Extension", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 30,
                    NOT(ISBLANK('FactTable'[ExtendedDeadline])), 
                    'FactTable'[Status] = "Pending"
                ),
            ">30 Days without FCC Extension", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 30,
                    ISBLANK('FactTable'[ExtendedDeadline]), 
                    'FactTable'[Status] = "Pending"
                ),
            ">100 Days", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 100, 
                    'FactTable'[Status] = "Pending"
                ),
            ">120 Days", 
                CALCULATE(
                    DISTINCTCOUNT('FactTable'[AccountID]), 
                    'FactTable'[Days] > 120, 
                    'FactTable'[Status] = "Pending"
                ),
            0
        )
    )
)


Pending Accounts by Bucket = 
VAR _bucket = SELECTEDVALUE('AgingBuckets'[Bucket])
VAR _isTotal = NOT ISINSCOPE('AgingBuckets'[Bucket])

VAR _count =
    SWITCH(
        TRUE(),
        _bucket = "0-30 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] <= 30, 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days with FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, NOT(ISBLANK('FactTable'[ExtendedDeadline])), 'FactTable'[Status] = "Pending"),
        _bucket = ">30 Days without FCC Extension",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 30, ISBLANK('FactTable'[ExtendedDeadline]), 'FactTable'[Status] = "Pending"),
        _bucket = ">100 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 100, 'FactTable'[Status] = "Pending"),
        _bucket = ">120 Days",
            CALCULATE(DISTINCTCOUNT('FactTable'[AccountID]), 'FactTable'[Days] > 120, 'FactTable'[Status] = "Pending")
    )

-- For totals, add up each bucket manually
VAR _total =
    CALCULATE(
        DISTINCTCOUNT('FactTable'[AccountID]),
        'FactTable'[Status] = "Pending"
    )

RETURN 
    IF(_isTotal, _total, COALESCE(_count, 0))



from PIL import Image, ExifTags
from PyPDF2 import PdfMerger
import os

def correct_image_orientation(img):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        exif = img._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation, None)

            if orientation_value == 3:
                img = img.rotate(180, expand=True)
            elif orientation_value == 6:
                img = img.rotate(270, expand=True)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
    except Exception as e:
        pass
    return img

def convert_image_to_pdf(image_path):
    img = Image.open(image_path)
    img = correct_image_orientation(img).convert("RGB")

    # Rotate to portrait if it's in landscape
    if img.width > img.height:
        img = img.rotate(90, expand=True)

    pdf_path = image_path + ".temp.pdf"
    img.save(pdf_path)
    return pdf_path

def create_pdf_from_files(file_list, output_path):
    merger = PdfMerger()
    temp_files = []

    for file in file_list:
        ext = os.path.splitext(file)[1].lower()
        
        if ext in [".jpg", ".jpeg", ".png"]:
            pdf_file = convert_image_to_pdf(file)
            temp_files.append(pdf_file)
            merger.append(pdf_file)
        elif ext == ".pdf":
            merger.append(file)
        else:
            print(f"Skipping unsupported file: {file}")

    merger.write(output_path)
    merger.close()

    # Cleanup temp files
    for temp_file in temp_files:
        os.remove(temp_file)

    print(f"✅ PDF created at: {output_path}")

# Example usage
file_paths = [
    "img1.jpg",
    "page2.png",
    "scan3.pdf"
]

create_pdf_from_files(file_paths, "final_combined.pdf")