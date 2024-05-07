import string
import datetime
from clause_map import _clause_mapping_string_type
from random import choice, randint, random

# generating random strings for insert statements
def random_string():
    return "{}".format(''.join(choice(string.ascii_lowercase) for _ in range(randint(1,5))))

# generating random timestamps for insert statements

def random_timestamp():
    return datetime.datetime(randint(2024,2025),randint(11,12),randint(11,12),randint(11,12),randint(11,12))

# generating random table name with 8 lowercase letters
def random_8_letters():
    return "{}".format(''.join(choice(string.ascii_lowercase) for _ in range(8)))

class AsyncQueryGenerator:
    """
    this is only for SQL demonstration
    asynchronous query generation aims to generate semantically equivalent
    but in different representations differential inputs for testing
    """

    columns = ["c0", "c1", "c2"]

    def __init__(self, extended_shared_clauses):
        self.shared_clauses = extended_shared_clauses
        self.shared_predicate_clauses = None

    def fuzzy_exp(self):
        return choice(["NULL"])

    """
    0. predicates part
    TODO: still many interesting or complex predicates not implemented ;(
    """

    def random_int_predicates(self, column_name):
        predicates = ["True"]
        if not self.shared_predicate_clauses:
            self.shared_predicate_clauses = []
            predicate_clauses = ["IN","BETWEEN"]
            for each_clause in predicate_clauses:
                if each_clause in self.shared_clauses:
                    self.shared_predicate_clauses.append(each_clause)
        for each_shared_clause in self.shared_predicate_clauses:
            if choice([True,False]):
                if each_shared_clause=="IN":
                    in_predicates = [
                        f"{column_name} IN ({column_name},{self.fuzzy_exp()})",
                        f"{column_name} NOT IN (0,1,2,{self.fuzzy_exp()})",
                    ]
                    predicates.append(choice(in_predicates))
                elif each_shared_clause=="IN_SUBQUERY":
                    # TODO
                    pass
                elif each_shared_clause=="BETWEEN":
                    between_predicates = [
                        f"{column_name} BETWEEN {column_name} AND {self.fuzzy_exp()}",
                        f"{column_name} NOT BETWEEN 0 AND {self.fuzzy_exp()}",
                    ]
                    predicates.append(choice(between_predicates))
        return ' AND '.join(predicates)

    def random_string_predicates(self, column_name):
        predicates = ["True"]
        if not self.shared_predicate_clauses:
            self.shared_predicate_clauses = []
            predicate_clauses = ["IN","BETWEEN"]
            for each_clause in predicate_clauses:
                if each_clause in self.shared_clauses:
                    self.shared_predicate_clauses.append(each_clause)
        for each_shared_clause in self.shared_predicate_clauses:
            if choice([True,False]):
                if each_shared_clause=="IN":
                    in_predicates = [
                        f"{column_name} IN ({column_name},{self.fuzzy_exp()})",
                        f"{column_name} NOT IN ('0','1','2',{self.fuzzy_exp()})",
                    ]
                    predicates.append(choice(in_predicates))
                elif each_shared_clause=="IN_SUBQUERY":
                    # TODO
                    pass
                elif each_shared_clause=="BETWEEN":
                    between_predicates = [
                        f"{column_name} BETWEEN {column_name} AND {self.fuzzy_exp()}",
                        f"{column_name} NOT BETWEEN '0' AND {self.fuzzy_exp()}",
                    ]
                    predicates.append(choice(between_predicates))
        return ' '.join(predicates)

    def random_timestamp_predicates(self, column_name):
        predicates = ["True"]
        if not self.shared_predicate_clauses:
            self.shared_predicate_clauses = []
            predicate_clauses = ["IN","BETWEEN"]
            for each_clause in predicate_clauses:
                if each_clause in self.shared_clauses:
                    self.shared_predicate_clauses.append(each_clause)
        for each_shared_clause in self.shared_predicate_clauses:
            if choice([True,False]):
                if each_shared_clause=="IN":
                    in_predicates = [
                        f"{column_name} IN ({column_name},{self.fuzzy_exp()})",
                        f"{column_name} NOT IN ('0','1','2',{self.fuzzy_exp()})",
                    ]
                    predicates.append(choice(in_predicates))
                elif each_shared_clause=="IN_SUBQUERY":
                    # TODO
                    pass
                elif each_shared_clause=="BETWEEN":
                    between_predicates = [
                        f"{column_name} BETWEEN {column_name} AND {self.fuzzy_exp()}",
                        f"{column_name} NOT BETWEEN '0' AND {self.fuzzy_exp()}",
                    ]
                    predicates.append(choice(between_predicates))
        return ' AND '.join(predicates)

    def random_predicates_no_join(self):
        predicates = []
        predicates.append(self.random_int_predicates("c1"))
        predicates.append(self.random_string_predicates("c2"))
        predicates.append(self.random_timestamp_predicates("c3"))
        return ' AND '.join(predicates)

    """
    1. simple CREATE statement implementations
    """

    def random_create_query(self):
        random_table_name = random_8_letters()
        create_query = f"CREATE TABLE {random_table_name} (c0 INT, c1 STRING, c2 TIMESTAMP);"
        async_queries = _clause_mapping_string_type(create_query)
        return random_table_name, async_queries

    def init_table(self, questdb_api, postgres_api):
        table1_name, table1_create_query = self.random_create_query()
        table2_name, table2_create_query = self.random_create_query()
        table3_name, table3_create_query = self.random_create_query()
        try:
            questdb_api.write_query(table1_create_query[0])
            questdb_api.write_query(table2_create_query[0])
            questdb_api.write_query(table3_create_query[0])
        except Exception as e:
            print("questdb init table failed!")
            print(str(e))
            exit(-1)
        try:
            postgres_api.write_query(table1_create_query[1])
            postgres_api.write_query(table2_create_query[1])
            postgres_api.write_query(table3_create_query[1])
        except Exception as e:
            print("postgres init table failed!")
            print(str(e))
            exit(-1)
        self.tables = [table1_name, table2_name, table3_name]
        print("tables init finished!")

    """
    2. INSERT statement
    """

    def random_insert_query(self, table_name):
        random_INT = randint(-1000, 1000)
        random_STRING = random_string()
        random_TIMESTAMP = random_timestamp()
        values = f"{random_INT}, '{random_STRING}', '{random_TIMESTAMP}'"
        insert_query = f"INSERT INTO {table_name} VALUES ({values});"
        return insert_query

    """
    3. UPDATE statement
    """

    def random_update_query(self, table_name):
        # TODO: update can be complex with JOINs, etc.
        random_INT = randint(-1000, 1000)
        random_STRING = random_string()
        random_TIMESTAMP = random_timestamp()
        updates = f"c0={random_INT},c1='{random_STRING}',c2='{random_TIMESTAMP}'"
        random_predicate = self.random_predicates_no_join()
        predicates = f"WHERE {random_predicate}"
        update_query = f"UPDATE {table_name} SET {updates} {predicates}"
        return update_query

    def random_select_query(self):
        return "SELECT 1"

    def random_query(self):
        select_query = 0.8
        insert_query = 0.1
        update_query = 0.1
        if random()<select_query:
            return self.random_select_query()
        elif random()>=1-update_query:
            return self.random_update_query(choice(self.tables))
        else:
            return self.random_insert_query(choice(self.tables))