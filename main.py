import os
import decimal
from tqdm import tqdm
from driver import *
from clause_identification import clauses_identifying
from query_generation import QueryGenerator

EVAL_CONFIG_CLAUSE_MAPPING = True

def postgres_exception_log(logstr):
    f = open("./postgres_exception.log", "a")
    f.write(f"\n===EXCEPTION===\n{logstr}\n")
    f.close()

def postgres_testing_log(logstr):
    f = open("./postgres_testing.log", "a")
    f.write(f"\n===Query Records===\n{logstr}\n")
    f.close()

def questdb_exception_log(logstr):
    f = open("./questdb_exception.log", "a")
    f.write(f"\n===EXCEPTION===\n{logstr}\n")
    f.close()

def questdb_testing_log(logstr):
    f = open("./questdb_testing.log", "a")
    f.write(f"\n===Query Records===\n{logstr}\n")
    f.close()

def bug_log(logstr):
    f = open("./bug.log", "a")
    f.write(f"\n===Bug-inducing Cases===\n{logstr}\n")
    f.close()

def differential_inputs_log(logstr):
    f = open("./diff_input.log", "a")
    f.write(logstr)
    f.close()

def questdb_execute_query(questdb_qpi, query):
    if "SELECT " in query:
        try:
            result = questdb_qpi.query(query)
            return result
        except Exception as e:
            questdb_exception_log(f"\nquery:{query}\n"+str(e))
            return -1
    else:
        try:
            questdb_qpi.write_query(query)
        except Exception as e:
            questdb_exception_log(f"\nquery:{query}\n"+str(e))
            return -1
        return None

def postgres_execute_query(postgre_api, query):
    if "SELECT " in query:
        try:
            result = postgre_api.query(query)
            return result
        except Exception as e:
            postgre_api.reconnect()
            postgres_exception_log(f"\nquery:{query}\n"+str(e))
            return -1
    else:
        try:
            postgre_api.write_query(query)
        except Exception as e:
            postgre_api.reconnect()
            postgres_exception_log(f"\nquery:{query}\n"+str(e))
            return -1
        return None

def result_analysis(query, questdb_result, postgres_result):
    if questdb_result==None or postgres_result==None or questdb_result==-1 or postgres_result==-1:
        bugstr = f"\nQuery:{query}\nnone result\n"
        return
    if len(postgres_result)>0:
        for i in range(len(postgres_result)):
            postgres_result[i] = list(postgres_result[i])
            for j in range(len(postgres_result[i])):
                if type(postgres_result[i][j])==type(decimal.Decimal(0.1)):
                    postgres_result[i][j] = float(postgres_result[i][j])
            postgres_result[i] = tuple(postgres_result[i])
    if set(questdb_result)!=set(postgres_result):
        bugstr = f"\nQuestDB Query:{query[0]}\n"
        bugstr += f"\nPostgresDB Query:{query[1]}\n"
        bugstr += f"\n\tquestdb:{str(set(questdb_result))}"
        bugstr += f"\n\tpostgres:{str(set(postgres_result))}"
        bug_log(bugstr)
    else:
        differential_inputs_log(str([query[0], query[1]])+'\n')


def main():
    if os.path.exists("./postgres_testing.log"):
        os.system("mv ./postgres_testing.log /tmp")
    if os.path.exists("./postgres_exception.log"):
        os.system("mv ./postgres_exception.log /tmp")
    if os.path.exists("./questdb_testing.log"):
        os.system("mv ./questdb_testing.log /tmp")
    if os.path.exists("./questdb_exception.log"):
        os.system("mv ./questdb_exception.log /tmp")
    if os.path.exists("./bug.log"):
        os.system("mv ./bug.log /tmp")
    if os.path.exists("./diff_input.log"):
        os.system("mv ./diff_input.log /tmp")
    """
    this is a demo code for testing one emerging database system QuestDB
    with the reference to mature relational database system Postgres
    """
    questdb_api = QuestDBConnector()
    postgres_api = PostgresConnector()
    # step 1: get shared clauses
    shared_clauses = clauses_identifying(questdb_api, postgres_api)
    # step 2: extend the set of shated clauses via clause mappings
    # step 3: generate differential inputs for testing
    query_generator = QueryGenerator(shared_clauses, EVAL_CONFIG_CLAUSE_MAPPING)
    # step 4: testing and analyzing
    testing_round = 0
    while True:
        tables, table1_query, table2_query, table3_query = query_generator.init_table(questdb_api, postgres_api)
        differential_inputs_log(str([f"DROP TABLE IF EXISTS {tables[0]}",f"DROP TABLE IF EXISTS {tables[0]}"])+'\n')
        differential_inputs_log(str([f"DROP TABLE IF EXISTS {tables[1]}",f"DROP TABLE IF EXISTS {tables[1]}"])+'\n')
        differential_inputs_log(str([f"DROP TABLE IF EXISTS {tables[2]}",f"DROP TABLE IF EXISTS {tables[2]}"])+'\n')
        differential_inputs_log(str(table1_query)+'\n')
        differential_inputs_log(str(table2_query)+'\n')
        differential_inputs_log(str(table3_query)+'\n')
        testing_round += 1
        print(f"testing round {testing_round}")
        questdb_success_query_count = 0
        postgres_success_query_count = 0
        for i in tqdm(range(2000)):
            query = query_generator.random_query()
            # print(query)
            questdb_result = questdb_execute_query(questdb_api, query[0])
            if questdb_result!=-1:
                questdb_success_query_count+=1
            postgres_result = postgres_execute_query(postgres_api, query[1])
            if postgres_result!=-1:
                postgres_success_query_count+=1
            if "SELECT " in query[0] and "SELECT " in query[1]:
                result_analysis(query, questdb_result, postgres_result)
            else:
                differential_inputs_log(str(query)+'\n')
            if i%100==0:
                print(f"questdb query success rate:{float(questdb_success_query_count/(i+1))}")
                print(f"postgres query success rate:{float(postgres_success_query_count/(i+1))}")
            questdb_testing_log(query[0])
            postgres_testing_log(query[1])

main()
