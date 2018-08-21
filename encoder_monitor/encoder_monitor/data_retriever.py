import pymongo as pm

class DataRetriever(object):

    """Docstring for DataRetriever. """

    def __init__(self, db_address, db_name):
        self.client = pm.MongoClient(db_address)
        self.db = self.client[db_name]

    def get_data(self, variables, end_time, window_size):
        """
        returns a dictionary of documents corresponding to the 
        collections referred to by 'variables' between
        (end_time - window_size) and end_time.
        The keys to the dictionary are the variable names and the values
        are the data for the corresponding variables.

        Args:
            variables: list of collection names
            end_time: end time of window in which to get data (as a Unix timestamp)
            window_size: time in seconds before the end_time in which
            to retrieve data
        Returns:
            dictionary of documents corresponding to the collection
            names in the given time period
        """

        start_time = end_time - window_size
        data = {}
        for v in variables:
            collection = self.db[v]
            collection_data = collection.find({"$and": [
                {"timestamp" : {"$lt": end_time}},
                {"timestamp" : {"$gt": start_time}}]})
            data[v] = list(collection_data)
        return data
