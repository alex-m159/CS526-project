import csv

def main():
    with open('../data/life-expectancy-census-tract.csv', 'r') as fr:
        with open('../data/life-expectancy-census-tract-rownum.csv', 'w') as fw:
            reader = csv.reader(fr)
            
            newrows = []
            for (i, row) in enumerate(reader):
                newrows.append([
                    i,
                    str(row[0]), # State
                    row[1] if row[1] != "(blank)" else "", # County
                    f"{float(row[2]):07.2f}" if row[2] != "" else "", # Census Tract Number
                    row[3], # Life Expectancy
                    row[4], # Life Expectancy Range
                    row[5], # Life Expectancy Standard Error
                ])
            writer = csv.writer(fw)
            writer.writerows(newrows)
        

if __name__ == "__main__":
    main()