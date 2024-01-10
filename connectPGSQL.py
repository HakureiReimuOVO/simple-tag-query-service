import psycopg2

class pgsql_test():
    '''
    生成一个suppliers数据库, 包含:
        Schema |         Name          |   Type   | Owner 
        --------+-----------------------+----------+-------
        public | part_drawings         | table    | pepsi
        public | parts                 | table    | pepsi
        public | parts_part_id_seq     | sequence | pepsi
        public | vendor_parts          | table    | pepsi
        public | vendors               | table    | pepsi
        public | vendors_vendor_id_seq | sequence | pepsi
    其中 vendors 有 entry, 分别是:
        1 | 3M Co.
        2 | AKM Semiconductor Inc.
        3 | Asahi Glass Co Ltd.
        4 | Daikin Industries Ltd.
        5 | Dynacast International Inc.
        6 | Foster Electric Co. Ltd.
        7 | Murata Manufacturing Co. Ltd.
    
    '''
    def __init__(self,) -> None:
        self.connect()
        self.create_tables()
        # insert one vendor
        self.insert_vendor("3M Co.")
        # insert multiple vendors
        self.insert_vendor_list([
            ('AKM Semiconductor Inc.',),
            ('Asahi Glass Co Ltd.',),
            ('Daikin Industries Ltd.',),
            ('Dynacast International Inc.',),
            ('Foster Electric Co. Ltd.',),
            ('Murata Manufacturing Co. Ltd.',)
        ])
    @property
    def _param(self):
        '''
        服务器参数: 
        0=localhost(test), 
        1=ist(deployment). 
        '''
        return [{"host": "localhost", "database": "suppliers", "user": "pepsi", "password": "123456",},
                {"host": "124.222.140.214", "port": "5666", "database": "data_management", "user": "postgres", "password": "123qweasd",}]

    def connect(self,):
        """ Connect to the PostgreSQL database server """
        try:
            # connect to the PostgreSQL server
            # print('Connecting to the PostgreSQL database...')
            param = self._param[1]
            self.conn = psycopg2.connect(**param)
            
            # create a cursor
            self.cur = self.conn.cursor()
            # print('Connection is created...')

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            exit(1)

    def create_tables(self,):
        """ create tables in the PostgreSQL database"""
        commands = (
            """
CREATE TABLE vendors (
    vendor_id SERIAL PRIMARY KEY,
    vendor_name VARCHAR(255) NOT NULL
)
""",
            """ CREATE TABLE parts (
part_id SERIAL PRIMARY KEY,
part_name VARCHAR(255) NOT NULL
)
""",
            """
CREATE TABLE part_drawings (
        part_id INTEGER PRIMARY KEY,
        file_extension VARCHAR(5) NOT NULL,
        drawing_data BYTEA NOT NULL,
        FOREIGN KEY (part_id)
        REFERENCES parts (part_id)
        ON UPDATE CASCADE ON DELETE CASCADE
)
""",
            """
CREATE TABLE vendor_parts (
        vendor_id INTEGER NOT NULL,
        part_id INTEGER NOT NULL,
        PRIMARY KEY (vendor_id , part_id),
        FOREIGN KEY (vendor_id)
            REFERENCES vendors (vendor_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (part_id)
            REFERENCES parts (part_id)
            ON UPDATE CASCADE ON DELETE CASCADE
)
""")
        try:
            # create table one by one
            for command in commands:
                self.cur.execute(command)
            # close communication with the PostgreSQL database server
            self.cur.close()
            # commit the changes
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def insert_vendor(self, vendor_name):
        """ insert a new vendor into the vendors table """
        sql = """INSERT INTO vendors(vendor_name)
                VALUES(%s) RETURNING vendor_id;"""
        conn = None
        vendor_id = None
        try:
            conn = self.conn
            cur = conn.cursor()
            cur.execute(sql, (vendor_name,))
            vendor_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        return vendor_id
    
    def insert_vendor_list(self, vendor_list):
        """ insert multiple vendors into the vendors table  """
        sql = "INSERT INTO vendors(vendor_name) VALUES(%s)"
        conn = None
        try:
            conn = self.conn
            cur = conn.cursor()
            cur.executemany(sql,vendor_list)
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

class c2pg():
    def __init__(self, param_idx) -> None:
        '''
        服务器参数: 
        0=localhost(test), 
        1=ist(deployment). 
        '''
        self.connect(param_idx=param_idx)

    def retry(max_retries):
        '''
        装饰器函数, 在捕捉到DatabaseError异常后commit一次后再重试
        如果还是异常则返回错误.
        '''
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                retry_count = 0
                while retry_count <= max_retries:
                    try:
                        result = func(self=self, *args, **kwargs)
                        break
                    except (Exception, psycopg2.DatabaseError) as e:
                        print(f"Exception: {e}")
                        if retry_count < max_retries:
                            # print("retry...")
                            self.conn.commit()
                            retry_count += 1
                        else:
                            # print("max retries reached, exit.")
                            raise e
                return result
            return wrapper
        return decorator

    @property
    def _param(self):
        '''
        服务器参数: 
        0=localhost(test), 
        1=ist(deployment). 
        '''
        return [{"host": "localhost", "database": "suppliers", "user": "pepsi", "password": "123456",}, 
            {"host": "124.222.140.214", "port": "5666", "database": "data_management", "user": "postgres", "password": "123qweasd",}]

    @retry(max_retries=1)
    def connect(self, param_idx : int = 1):
        """ Connect to the PostgreSQL database server """
        # connect to the PostgreSQL server
        # print('Connecting to the PostgreSQL database...')
        param = self._param[param_idx]
        self.conn = psycopg2.connect(**param)
        
        # create a cursor
        self.cur = self.conn.cursor()
        # print('Connection is created...')
            
    @retry(max_retries=1)
    def table_check(self, ):
        '''
        查找数据库内有多少表
        '''
        check_statement_1 = '''SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';'''
        cur = self.conn.cursor()
        cur.execute(check_statement_1)
        schema = cur.fetchall()
        res = []
        for idx in range(len(schema)):
            name = schema[idx][0]
            check_statement_2 = "SELECT column_name, data_type, character_maximum_length, is_nullable\nFROM information_schema.columns\nWHERE table_schema = 'public' and table_name = '" + name + "';"
            cur = self.conn.cursor()
            cur.execute(check_statement_2)
            schema_info = cur.fetchall()
            for col_idx in range(len(schema_info)):
                info = tuple(str(_) for _ in schema_info[col_idx])
                res.append(str(name) + ": " + ", ".join(info)) 
            res.append('\n')
        return ", \n".join(res)
    
    @retry(max_retries=1)
    def query_check(self, statement):
        '''
        查找数据库内有多少表
        '''
        cur = self.conn.cursor()
        cur.execute(statement)
        return cur.fetchall()

if __name__ == '__main__':
    pgsql_test()
    a = c2pg(1)
    b = a.table_check()
    c = a.query_check(statement='SELECT AVG(FuelConsumption) AS average_carbon_emission\nFROM ship_engine_status')
    print(c)
    # print(str(b)+'\n'+str(c))