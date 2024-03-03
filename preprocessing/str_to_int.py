import csv

def main():
    with open('../data/Ruralurbancontinuumcodes2023.csv', 'r') as fr:
        with open('../data/Ruralurbancontinuumcodes2023_Converted.csv', 'w') as fw:
            reader = csv.reader(fr)
            
            newrows = []
            for row in reader:
                newrows.append([
                    row[0],
                    row[1],
                    row[2],
                    int(row[3].replace(',', '')),
                    row[4],
                    row[5],
                ])
            writer = csv.writer(fw)
            writer.writerows(newrows)
        

if __name__ == "__main__":
    main()