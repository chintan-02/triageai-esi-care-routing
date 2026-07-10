import re


AGE_PATTERNS = [
    re.compile(r"\b(?P<age>\d{1,3})\s*[- ]?(year|yr|years?)\s*[- ]?old\b", re.I),
    re.compile(r"\b(?P<age>\d{1,3})\s*(yo|y/o)\b", re.I),
]

GENDER_PATTERNS = [
    re.compile(r"\b(?P<gender>male|female|man|woman|m|f)\b", re.I),
]

BP_PATTERNS = [
    re.compile(
        r"\b(?:BP|blood pressure)\s*[:=]?\s*(?P<sbp>\d{2,3})\s*/\s*(?P<dbp>\d{2,3})\b",
        re.I,
    ),
    re.compile(
        r"\b(?:BP|blood pressure)\s*[:=]?\s*(?P<sbp>\d{2,3})\s+over\s+(?P<dbp>\d{2,3})\b",
        re.I,
    ),
]

HR_PATTERNS = [
    re.compile(r"\b(?:HR|heart rate|pulse)\s*[:=]?\s*(?P<hr>\d{2,3})\b", re.I),
]

RR_PATTERNS = [
    re.compile(r"\b(?:RR|respiratory rate|resp rate)\s*[:=]?\s*(?P<rr>\d{1,2})\b", re.I),
]

OXYGEN_PATTERNS = [
    re.compile(r"\b(?:O2|SpO2|oxygen saturation|oxygen sat|sat)\s*[:=]?\s*(?P<o2>\d{2,3})\s*%?\b", re.I),
]

TEMP_PATTERNS = [
    re.compile(
        r"\b(?:temp|temperature|T)\s*[:=]?\s*(?P<temp>\d{2,3}(?:\.\d+)?)\s*(?:c|f|°c|°f)?\b",
        re.I,
    ),
]

COMPLAINT_PATTERNS = {
    "chest pain": [
        re.compile(r"\bchest pain\b", re.I),
        re.compile(r"\bchest pressure\b", re.I),
    ],
    "shortness of breath": [
        re.compile(r"\bshortness of breath\b", re.I),
        re.compile(r"\bdifficulty breathing\b", re.I),
        re.compile(r"\bSOB\b", re.I),
    ],
    "abdominal pain": [
        re.compile(r"\babdominal pain\b", re.I),
        re.compile(r"\bstomach pain\b", re.I),
    ],
    "dizziness": [
        re.compile(r"\bdizzy\b", re.I),
        re.compile(r"\bdizziness\b", re.I),
    ],
    "headache": [
        re.compile(r"\bheadache\b", re.I),
        re.compile(r"\bmigraine\b", re.I),
    ],
    "seizure": [
        re.compile(r"\bseizure\b", re.I),
    ],
    "unresponsive": [
        re.compile(r"\bunresponsive\b", re.I),
        re.compile(r"\bnot responding\b", re.I),
    ],
    "suicidal ideation": [
        re.compile(r"\bsuicidal ideation\b", re.I),
        re.compile(r"\bsuicidal thoughts\b", re.I),
        re.compile(r"\bwants to harm self\b", re.I),
        re.compile(r"\bself[- ]harm\b", re.I),
    ],
    "pregnancy": [
        re.compile(r"\bpregnant\b", re.I),
        re.compile(r"\bpregnancy\b", re.I),
    ],
    "stroke symptoms": [
        re.compile(r"\bfacial droop\b", re.I),
        re.compile(r"\bslurred speech\b", re.I),
        re.compile(r"\bone[- ]sided weakness\b", re.I),
        re.compile(r"\bstroke symptoms?\b", re.I),
    ],
    "severe trauma": [
        re.compile(r"\bsevere trauma\b", re.I),
        re.compile(r"\bmajor trauma\b", re.I),
        re.compile(r"\bmotor vehicle collision\b", re.I),
    ],
    "fever": [
        re.compile(r"\bfever\b", re.I),
        re.compile(r"\bfebrile\b", re.I),
    ],
}