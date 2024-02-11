import clickhouse_connect
from typing import List

class CPSDatum:
    
    def __init__(self, **kwargs):
        self.rownum = kwargs['ROWNUM']  
        self.year = kwargs['YEAR']  
        self.serial = kwargs['SERIAL']  
        self.month = kwargs['MONTH']  
        self.month_name = kwargs['MONTH_NAME']  
        self.cpsid = kwargs['CPSID']  
        self.asecflag = kwargs['ASECFLAG']  
        self.hflag = kwargs['HFLAG']  
        self.asecwth = kwargs['ASECWTH']  
        self.statefip = kwargs['STATEFIP']  
        self.statefip_name = kwargs['STATEFIP_NAME']  
        self.statecensus = kwargs['STATECENSUS']  
        self.county = kwargs['COUNTY']  
        self.metfips = kwargs['METFIPS']  
        self.metarea = kwargs['METAREA']  
        self.metarea_name = kwargs['METAREA_NAME']  
        self.metro = kwargs['METRO']  
        self.metro_name = kwargs['METRO_NAME']  
        self.individcc = kwargs['INDIVIDCC']  
        self.pernum = kwargs['PERNUM']  
        self.cpsidv = kwargs['CPSIDV']  
        self.cpsidp = kwargs['CPSIDP']  
        self.asecwt = kwargs['ASECWT']  
        self.educ = kwargs['EDUC']  
        self.educ_name = kwargs['EDUC_NAME']  
        self.higrade = kwargs['HIGRADE']  
        self.higrade_name = kwargs['HIGRADE_NAME']  
        self.ftotval = kwargs['FTOTVAL']  
        self.inctot = kwargs['INCTOT']  
        self.adjginc = kwargs['ADJGINC']  
        self.fedtax = kwargs['FEDTAX']  
        self.fedtaxac = kwargs['FEDTAXAC']  
        self.margtax = kwargs['MARGTAX']  
        self.statetax = kwargs['STATETAX']  
        self.stataxac = kwargs['STATAXAC']  
        self.taxinc = kwargs['TAXINC']  
        
    
class CPSRepo:
    """This class manages the details of interacting with 
    the database to fetch the CPS data from IPUMS.
    It's meant to be a relatively thin layer of abstraction
    that makes the other code simpler and consolidates the 
    database specific code.
    """
    def __init__(self) -> None:
        self.client = clickhouse_connect.get_client(
            host='localhost', 
            port=18123, 
            interface='http', 
            username='pubhealth'
        )
    
    def test(self):
        return self.client.server_version
    
    
    def get_n(self, n=100) -> List[CPSDatum]:
        p = {'num': n}
        q = self.client.query('SELECT * FROM cps_00004.cps_00004 LIMIT {num:UInt32}', parameters=p)
        result = []
        for row in q.result_rows:
            row
            c = CPSDatum(
                rownum             =    row[0],
                year               =    row[1],
                serial             =    row[2],
                month              =    row[3],
                month_name         =    row[4],
                cpsid              =    row[5],
                asecflag           =    row[6],
                hflag              =    row[7],
                asecwth            =    row[8],
                statefip           =    row[9],
                statefip_name      =    row[10],
                statecensus        =    row[11],
                county             =    row[12],
                metfips            =    row[13],
                metarea            =    row[14],
                metarea_name       =    row[15],
                metro              =    row[16],
                metro_name         =    row[17],
                individcc          =    row[18],
                pernum             =    row[19],
                cpsidv             =    row[20],
                cpsidp             =    row[21],
                asecwt             =    row[22],
                educ               =    row[23],
                educ_name          =    row[24],
                higrade            =    row[25],
                higrade_name       =    row[26],
                ftotval            =    row[27],
                inctot             =    row[28],
                adjginc            =    row[29],
                fedtax             =    row[30],
                fedtaxac           =    row[31],
                margtax            =    row[32],
                statetax           =    row[33],
                stataxac           =    row[34],
                taxinc             =    row[35]
            )
            result.append(c)
        return result
    
