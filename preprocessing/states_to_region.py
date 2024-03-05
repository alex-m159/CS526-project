import csv


rows = [
    ('Alabama', 'AL', 1, 'South', 'East South Central'),
    ('Alaska', 'AK', 2, 'West', 'Pacific'),
    ('Arizona', 'AZ', 4, 'West', 'Mountain'),
    ('Arkansas', 'AR', 5, 'South', 'West South Central'),
    ('California', 'CA', 6, 'West', 'Pacific'),
    ('Colorado', 'CO', 8, 'West', 'Mountain'),
    ('Connecticut', 'CT', 9, 'Northeast', 'New England'),
    ('Delaware', 'DE', 10, 'South', 'South Atlantic'),
    ('District of Columbia', 'DC', 11, 'South', 'South Atlantic'),
    ('Florida', 'FL', 12, 'South', 'South Atlantic'),
    ('Georgia', 'GA', 13, 'South', 'South Atlantic'),
    ('Hawaii', 'HI', 15, 'West', 'Pacific'),
    ('Idaho', 'ID', 16, 'West', 'Mountain'),
    ('Illinois', 'IL', 17, 'Midwest', 'East North Central'),
    ('Indiana', 'IN', 18, 'Midwest', 'East North Central'),
    ('Iowa', 'IA', 19, 'Midwest', 'West North Central'),
    ('Kansas', 'KS', 20, 'Midwest', 'West North Central'),
    ('Kentucky', 'KY', 21, 'South', 'East South Central'),
    ('Louisiana', 'LA', 22, 'South', 'West South Central'),
    ('Maine', 'ME', 23, 'Northeast', 'New England'),
    ('Maryland', 'MD', 24, 'South', 'South Atlantic'),
    ('Massachusetts', 'MA', 25, 'Northeast', 'New England'),
    ('Michigan', 'MI', 26, 'Midwest', 'East North Central'),
    ('Minnesota', 'MN', 27, 'Midwest', 'West North Central'),
    ('Mississippi', 'MS', 28, 'South', 'East South Central'),
    ('Missouri', 'MO', 29, 'Midwest', 'West North Central'),
    ('Montana', 'MT', 30, 'West', 'Mountain'),
    ('Nebraska', 'NE', 31, 'Midwest', 'West North Central'),
    ('Nevada', 'NV', 32, 'West', 'Mountain'),
    ('New Hampshire', 'NH', 33, 'Northeast', 'New England'),
    ('New Jersey', 'NJ', 34, 'Northeast', 'Middle Atlantic'),
    ('New Mexico', 'NM', 35, 'West', 'Mountain'),
    ('New York', 'NY', 36, 'Northeast', 'Middle Atlantic'),
    ('North Carolina', 'NC', 37, 'South', 'South Atlantic'),
    ('North Dakota', 'ND', 38, 'Midwest', 'West North Central'),
    ('Ohio', 'OH', 39, 'Midwest', 'East North Central'),
    ('Oklahoma', 'OK', 40, 'South', 'West South Central'),
    ('Oregon', 'OR', 41, 'West', 'Pacific'),
    ('Pennsylvania', 'PA', 42, 'Northeast', 'Middle Atlantic'),
    ('Rhode Island', 'RI', 44, 'Northeast', 'New England'),
    ('South Carolina', 'SC', 45, 'South', 'South Atlantic'),
    ('South Dakota', 'SD', 46, 'Midwest', 'West North Central'),
    ('Tennessee', 'TN', 47, 'South', 'East South Central'),
    ('Texas', 'TX', 48, 'South', 'West South Central'),
    ('Utah', 'UT', 49, 'West', 'Mountain'),
    ('Vermont', 'VT', 50, 'Northeast', 'New England'),
    ('Virginia', 'VA', 51, 'South', 'South Atlantic'),
    ('Washington', 'WA', 53, 'West', 'Pacific'),
    ('West Virginia', 'WV', 54, 'South', 'South Atlantic'),
    ('Wisconsin', 'WI', 55, 'Midwest', 'East North Central'),
    ('Wyoming', 'WY', 56, 'West', 'Mountain'),
]





def main():
    with open('../data/state-census-regions.csv', 'w') as fw:

        writer = csv.writer(fw)
        for wrow in rows:
            writer.writerow(list(wrow))

if __name__ == '__main__':
    main()













































































































































































































































