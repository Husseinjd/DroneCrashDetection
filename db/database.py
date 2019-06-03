import pymongo

class DatabaseConnector():

    def __init__(self,dbname,port):
        self.dbname = dbname
        self.port = port
        self.mycol = None
        self.connectDB()

    def connectDB(self):
            try:
                print("mongodb://localhost:"+self.port+"/")
                self.myclient = pymongo.MongoClient("mongodb://localhost:"+self.port+"/")
                print('Database connected')
            except:
                print('Database connection error..')
                return -1
            self.mydb = self.myclient[self.dbname]


    def set_collection(self,cname):
        self.mycol = self.mydb[cname]

    def insert_dict(self,dict):
        """creates and Insert dict into collection

        Parameters
        ----------
        colname : str
            Description of parameter `colname`.
        dict : dict
            Description of parameter `dict`.
        """
        try:
            self.mycol.insert_one(dict)
        except Exception as e:
            print('error inserting dict to mongo')
            print(e)
            return -1

    def dropdb(self,dbname):
            self.myclient.drop_database(dbname)
            print(f'{dbname} database deleted')

    def query_str(self,sub):
        """retruns a list of files that contains sub as a substring

        Parameters
        ----------
        sub : str
            substring in the collection name

        Returns
        -------
        list
            list of file names with vname in collection name

        """
        return [c for c in self.mydb.list_collection_names() if sub in c]


    def query(self,collection_name,variable=None):
        """return list of values for a variable within a component collection

        Parameters
        ----------
        collection_name : str
            Description of parameter `collection_name`.
        variable : str
            if this value is none the query returns the collection as dict
        Returns
        -------
        int
            -1 if key error
        list
            list of values for the variables requested
        """
        self.mycol = self.mydb[collection_name]
        for x in self.mycol.find():
            try:
                if variable is None:
                    return  x
                else:
                    return x[variable]
            except:
                return -1

    def close_connection(self):
        self.myclient.close()
