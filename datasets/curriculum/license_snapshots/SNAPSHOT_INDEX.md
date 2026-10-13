# License snapshots (retrieval date: 2026-10-11)

Short excerpts captured during source-plan verification. Full raw HTML (if fetched later) is gitignored under this folder (`*.html`, `*.txt`); these `.md` notes are committed.

## MIT OpenCourseWare
- URL: https://ocw.mit.edu/pages/privacy-and-terms-of-use/
- License: CC BY-NC-SA 4.0
- Excerpt: “OCW content may be used… under a Creative Commons license (CC BY-NC-SA 4.0).” Support pages: reuse for educational purposes under Creative Commons BY-NC-SA; attribution required.

## Stanford Engineering Everywhere
- URL: https://see.stanford.edu/UsingSEE
- License: CC BY-NC-SA 4.0
- Excerpt: “Unless otherwise expressly indicated, SEE content is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike (CC BY NC SA) 4.0 International License.”
- Exception logged: “Stanford Introduction to Logic is not licensed under a Creative Commons license.”

## Harvard CS50
- URL: https://cs50.harvard.edu/x/license
- License: CC BY-NC-SA 4.0
- Excerpt: “This course is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) license.”

## CMU Open Learning Initiative
- URL: https://oli.cmu.edu/
- License: CC BY-NC-SA 4.0 (site footer)
- Excerpt: “© 2025 Open Learning Initiative, Carnegie Mellon University. Licensed under CC BY-NC-SA 4.0.”
- Caveat: unit-level third-party content must still be excluded if mixed.

## TU Delft OpenCourseWare
- URL: https://ocw.tudelft.nl/
- License: CC BY-NC-SA 4.0
- Excerpt: “This work is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. Except where otherwise noted, contents on this site are licensed under…”

## The Open University OpenLearn
- URL: https://about.open.ac.uk/strategy-and-policies/policies-and-statements/copyright-openlearn
- License: Creative Commons (non-commercial; unit acknowledgments may add Special Restrictions)
- Excerpt: “The materials including the free courses made available on the OpenLearn Site… are released under the terms of the Creative Commons licence… for non-commercial purposes only.” Units with Special Restrictions or PROPRIETARY marks are excluded.

## CS2023 (SEPARATE ANCHOR — not pooled with courses)
- URL: https://ieeecs-media.computer.org/media/education/reports/CS2023.pdf
- Permission: “Permission is granted to use these curriculum guidelines for the development of educational materials and programs. Other use requires specific permission.”
- Note: already used in CURR01; not part of CURR02 course pool.

## NPTEL / SWAYAM (EXCLUDED)
- URL: https://swayam.gov.in/terms_of_use
- Excerpt: “you agree not to scrape, or otherwise download in bulk, any SWAYAM Site content…”; “Unless otherwise expressly stated… materials… are for your personal use… All rights… are reserved.”

## Elements of AI / University of Helsinki (EXCLUDED)
- URL: https://www.elementsofai.com/faq/how-is-the-content-licensed
- Excerpt: “all rights reserved… For licensing, please contact hello@minnalearn.com.”


## O*NET 30.0 Database (`db_30_0`) - ALIGN06, signed 2026-10-13
- Licence page: https://www.onetcenter.org/license_db.html (reached from https://www.onetcenter.org/license.html, "License Exceptions")
- Licence: **Creative Commons Attribution 4.0 International (CC BY 4.0)** - https://creativecommons.org/licenses/by/4.0/
- Excerpt: "Except as noted below, the content of the O*NET 31.0 Database is licensed under a Creative Commons Attribution 4.0 International License. You are free to copy or adapt the information from this database, as long as you: credit the O*NET 31.0 Database and the U.S. Department of Labor, Employment and Training Administration as the original source, link to the license, and indicate where any changes were made to the original."
- Older releases: "Earlier versions of the O*NET Database may be used under this license, or any previous license under which they were released. When using any version of the Database, please include the appropriate version number in your attribution."
- Credit line used: "This analysis uses information from the O*NET 30.0 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA). Used under the CC BY 4.0 license. O*NET(R) is a trademark of USDOL/ETA."
- Developer registration: optional, not required for this research use.
- **Correction:** `ALIGN06_PREREG.md` section 9 row 1 and `reports/INDEPENDENT_SOURCES.md` had both recorded O*NET as public domain. It is not; attribution is mandatory. Full raw snapshot: `onet_db_30_0.txt` (gitignored).

## BLS OEWS, May 2025 national - ALIGN06, signed 2026-10-13
- Licence page: https://www.bls.gov/opub/copyright-information.htm
- Licence: **Public domain** (17 U.S.C. section 105); no version number, no permission required.
- Excerpt: "The Bureau of Labor Statistics (BLS) is a Federal government agency and everything that we publish, both in hard copy and electronically, is in the public domain, except for previously copyrighted photographs and illustrations. You are free to use our public domain material without specific permission, although we do ask that you cite the Bureau of Labor Statistics as the source."
- Credit line used: "Source: U.S. Bureau of Labor Statistics, Occupational Employment and Wage Statistics (OEWS), May 2025 national estimates."
- Logo: "The BLS emblem ... are federally registered trademarks. Unauthorized use of the BLS emblem is prohibited." No BLS emblem is reproduced anywhere in this project.
- URL note: the two URLs originally cited in `ALIGN06_PREREG.md` section 9 (`bls.gov/oes/copyright.htm`, `bls.gov/oes/oes_stat.htm`) now serve the OEWS home page rather than licence text. The licence itself is unchanged.
- Access note: every `bls.gov` and `download.bls.gov` request from the author's host returns HTTP 403 (Akamai bot management), across curl/Schannel, Python urllib and Python requests, with a descriptive identifying User-Agent. Recorded in the raw snapshot `bls_oes_m2025.txt` (gitignored).
