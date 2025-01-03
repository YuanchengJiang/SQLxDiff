import re
from random import choice

# map structure: {syntax_in_questdb: syntax_in_postgres}

# for some complex mappings, it requires query mutations
# pattern: "_MUTATION_XXX"

def valid_expression():
    valid_expressions = [
        "CAST(1 AS FLOAT)", "CAST(NULL AS FLOAT)", "CAST(0.0 AS FLOAT)", "CAST('0' AS FLOAT)", "CAST(0-0 AS FLOAT)", "CAST(CAST(NULL AS INT) AS FLOAT)", "CAST(CAST('0' AS INT) AS FLOAT)", "CAST(CAST('0' AS FLOAT) AS INT)", "~CAST(NULL AS INT)", "~CAST(0.0 AS INT)", "~NULL::INT", "CAST(NULL AS INT)&CAST(NULL AS INT)", "CAST(NULL AS INT)&(~NULL::INT)", "CAST(NULL AS INT)^CAST(NULL AS INT)", "CAST(NULL AS INT)^(~NULL::INT)", "CAST(NULL AS INT)|CAST(NULL AS INT)", "CAST(NULL AS INT)|(~NULL::INT)", "'5'<>'5'", "'123'<'456'", "CAST(CAST('123'<'456' AS INT)|(~NULL::INT) AS INT)^CAST(NULL AS INT)"
    ]
    return choice(valid_expressions)

class ClauseMapping:

    def __init__(self):
        pass

    def extract_in_operations(self, query):
        in_operations = []
        # assume no continous spaces in the query
        query_splits = query.split(' ')
        for i in range(len(query_splits)):
            if query_splits[i]=="IN":
                in_operations.append(
                    f"{query_splits[i-1]} IN {query_splits[i+1]}"
                ) if query_splits[i-1]!="NOT" else in_operations.append(
                    f"{query_splits[i-2]} NOT IN {query_splits[i+1]}"
                )
        return in_operations

    def _clause_mapping_in_mutation(self, query):
        # this mapping aims to bridge the semantic gap in questdb
        # NULL in questdb is a specific value
        # we need to nullify results when necessary, which aligns with postgres

        # query[0] -> questdb query

        # for questdb
        in_operations = self.extract_in_operations(query[0])
        for each_in_operation in in_operations:
            in_target = each_in_operation.split(' ')[0]
            in_list = each_in_operation.split(' ')[-1]
            if "'" not in in_list:
                in_list = in_list.replace('0',"'0'").replace('1',"'1'").replace('2',"'2'")
            query[0] = query[0].replace(
                each_in_operation,
                f"CASE WHEN {in_target} IS NULL THEN NULL::BOOLEAN ELSE {each_in_operation} END"
                )

        # for postgres
        in_operations = self.extract_in_operations(query[1])
        for each_in_operation in in_operations:
            in_target = each_in_operation.split(' ')[0]
            in_list = each_in_operation.split(' ')[-1]
            if "'" not in in_list:
                in_list = in_list.replace('0',"'0'").replace('1',"'1'").replace('2',"'2'")
            new_in_operation = each_in_operation.replace(',NULL','').replace('(NULL)','()')
            query[1] = query[1].replace(
                each_in_operation,
                f"CASE WHEN {in_target} IS NULL THEN NULL ELSE {new_in_operation} END"
                )

        return query

    def extract_between_operations(self, query):
        between_operations = []
        # assume no continous spaces in the query
        query_splits = query.split(' ')
        for i in range(len(query_splits)):
            if query_splits[i]=="BETWEEN":
                between_operations.append(
                    f"{query_splits[i-1]} BETWEEN {query_splits[i+1]} {query_splits[i+2]} {query_splits[i+3]}"
                ) if query_splits[i-1]!="NOT" else between_operations.append(
                    f"{query_splits[i-2]} NOT BETWEEN {query_splits[i+1]} {query_splits[i+2]} {query_splits[i+3]}"
                )
        return between_operations

    def _clause_mapping_between_mutation(self, query):
        # this mapping aims to bridge the semantic gap in questdb
        # NULL in questdb is a specific value
        # we need to nullify results when necessary, which aligns with postgres

        # query[0] -> questdb query

        between_operations = self.extract_between_operations(query[0])
        for each_between_operation in between_operations:
            between_keyword = "NOT BETWEEN" if "NOT BETWEEN" in each_between_operation else "BETWEEN"
            # A BETWEEN B AND C
            A = each_between_operation.split(f' {between_keyword}')[0]
            B = each_between_operation.split(f'{between_keyword} ')[1].split(' AND')[0]
            C = each_between_operation.split('AND ')[1]
            query[0] = query[0].replace(
                each_between_operation,
                f"CASE WHEN {A} IS NULL THEN NULL::BOOLEAN WHEN {B} IS NULL THEN NULL::BOOLEAN WHEN {C} IS NULL THEN NULL::BOOLEAN ELSE {each_between_operation} END"
                )
        return query

    def _clause_mapping_string_type(self, query):
        questdb_map = {"STRING": "SYMBOL"}
        postgres_map = {"STRING": "VARCHAR(64)"}
        query[0] = query[0].replace("STRING", questdb_map["STRING"])
        query[1] = query[1].replace("STRING", postgres_map["STRING"])
        return query

    def _clause_mapping_between_symmetric(self, query):
        query[1] = query[1].replace(" BETWEEN ", " BETWEEN SYMMETRIC ")
        return query

    def _clause_mapping_count_distinct(self, query):
        # Note: the syntax here is not complete for easier match
        query[1] = query[1].replace(" COUNT_DISTINCT(", " COUNT(DISTINCT")
        return query

    def _clause_mapping_sample_by(self, query):
        """
        a bit complex to map SAMPLE BY: (e.g., SAMPLE BY 1d)
        1. add one new column to extract day: EXTRACT(DAY FROM c2) AS d
        2. add group by: GROUP BY d
        3. add column alias to COUNT(*): COUNT(*) AS sample_by_result
        4. wrap the whole query and only fetch the sample_by_result:
        SELECT sample_by_result (QUERY);
        """
        # this is just an demo implementation
        # ASSUMPTION: only fetct COUNT(*), use SAMPLE BY 1d
        # step 1 and step 3:
        col = 'COUNT(*) AS sample_by_result, EXTRACT(DAY FROM T1.c2) AS d'
        query = query.replace('COUNT(*)', col)
        # step 2:
        query = query.replace('SAMPLE BY 1d', 'GROUP BY d')
        # step 4:
        query = f"SELECT sample_by_result from ({query})"
        return query

    def main(self, query):

        # format queries before mapping
        mapped_query = [self.formatting_query(query), self.formatting_query(query)]

        # mapping IN clause
        mapped_query = self._clause_mapping_in_mutation(mapped_query)

        # mapping STRING type
        mapped_query = self._clause_mapping_string_type(mapped_query)

        # mapping BETWEEN clause
        mapped_query = self._clause_mapping_between_symmetric(mapped_query)

        # mapping SAMPLE BY clause
        if "SAMPLE BY" in mapped_query[0]:
            # when SAMPLE BY is used in questdb query
            # we map SAMPLE BY back to valid clauses in postgres
            mapped_query[1] = self._clause_mapping_sample_by(mapped_query[1])

        # map NULL with between:
        mapped_query = self._clause_mapping_between_mutation(mapped_query)

        return mapped_query

    def formatting_query(self, query):
        # we format the query for easier mapping:
        # 1. no continuous spaces
        query = re.sub('[ ]+', ' ', query)
        # 2. no space between commas
        query = re.sub(', ', ',', query)
        return query