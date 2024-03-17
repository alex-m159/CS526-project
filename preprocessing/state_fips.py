STATES = [
    (1, 'ALABAMA'),
    (2, 'ALASKA'),
    (4, 'ARIZONA'),
    (5, 'ARKANSAS'),
    (6, 'CALIFORNIA'),
    (8, 'COLORADO'),
    (9, 'CONNECTICUT'),
    (10, 'DELAWARE'),
    (11, 'DISTRICT OF COLUMBIA'),
    (12, 'FLORIDA'),
    (13, 'GEORGIA'),
    (15, 'HAWAII'),
    (16, 'IDAHO'),
    (17, 'ILLINOIS'),
    (18, 'INDIANA'),
    (19, 'IOWA'),
    (20, 'KANSAS'),
    (21, 'KENTUCKY'),
    (22, 'LOUISIANA'),
    (23, 'MAINE'),
    (24, 'MARYLAND'),
    (25, 'MASSACHUSETTS'),
    (26, 'MICHIGAN'),
    (27, 'MINNESOTA'),
    (28, 'MISSISSIPPI'),
    (29, 'MISSOURI'),
    (30, 'MONTANA'),
    (31, 'NEBRASKA'),
    (32, 'NEVADA'),
    (33, 'NEW HAMPSHIRE'),
    (34, 'NEW JERSEY'),
    (35, 'NEW MEXICO'),
    (36, 'NEW YORK'),
    (37, 'NORTH CAROLINA'),
    (38, 'NORTH DAKOTA'),
    (39, 'OHIO'),
    (40, 'OKLAHOMA'),
    (41, 'OREGON'),
    (42, 'PENNSYLVANIA'),
    (44, 'RHODE ISLAND'),
    (45, 'SOUTH CAROLINA'),
    (46, 'SOUTH DAKOTA'),
    (47, 'TENNESSEE'),
    (48, 'TEXAS'),
    (49, 'UTAH'),
    (50, 'VERMONT'),
    (51, 'VIRGINIA'),
    (53, 'WASHINGTON'),
    (54, 'WEST VIRGINIA'),
    (55, 'WISCONSIN'),
    (56, 'WYOMING'),
]








import csv

with open('../data/state-fips.csv', 'w') as fw:
    writer = csv.writer(fw)
    writer.writerows(STATES)