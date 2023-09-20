from unified_planning.shortcuts import *
from up_social_laws.sa_to_ma_converter import *
from up_social_laws.robustness_checker import *
from unified_planning.io.pddl_reader import *
import random
import os
import csv
import create_ma_benchmarks
import logging
import time
from call_function_with_timeout import SetTimeout


PDDL_DOMAINS_PATH = "downward-benchmarks"
ROBUSTNESS_RESULTS_FILE = "robustness_results.csv"
PLANNER_TIMEOUT = 60

random.seed(2023)
logging.basicConfig(filename='social_law_experiments.log', encoding='utf-8', level=logging.DEBUG)
up.shortcuts.get_environment().credits_stream = None

def main():
    data = defaultdict(lambda : {})
    logging.info("Starting robustness check")
    domain_agent_types = create_ma_benchmarks.get_ma_agent_types()

    if not os.path.exists(ROBUSTNESS_RESULTS_FILE):
        results_file = open(ROBUSTNESS_RESULTS_FILE, "w")
        print("domain", "problem", "time", "result", sep=",", file=results_file, flush=True)        
    else:
        with open(ROBUSTNESS_RESULTS_FILE) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data[row['domain']][row['problem']] = row
        results_file = open(ROBUSTNESS_RESULTS_FILE, "a")    

    for domain in domain_agent_types.keys():
        logging.info("Starting domain %s", domain)
        domain_filename = os.path.join(PDDL_DOMAINS_PATH, domain, "domain.pddl")        
        problems = os.listdir(os.path.join(PDDL_DOMAINS_PATH, domain)) 
        problems.remove("domain.pddl")
        logging.info("Got problems %s", problems)

        for problem_file in problems:
            if domain in data.keys() and problem_file in data[domain].keys():
                logging.info("Problem %s:%s is already in results, skipping", domain, problem_file)
                continue            

            logging.info("Reading %s:%s", domain, problem_file)
            reader = PDDLReader()
            
            problem_filename = os.path.join(PDDL_DOMAINS_PATH, domain, problem_file)
            try:
                problem = reader.parse_problem(domain_filename, problem_filename)
            except Exception as e:
                logging.error("Failed to parse problem: %s", e)
                continue

            logging.info("Converting to MA")
            try:
                samac = SingleAgentToMultiAgentConverter([domain_agent_types[domain]])
                samac_ret = samac.compile(problem)
            except Exception as e:
                logging.error("Failed to convert to MA: %s", e)
                continue

            logging.info("Checking robustness")
            try:
                ma_problem = samac_ret.problem
                slrc = SocialLawRobustnessChecker(planner_name="fast-downward")
                
                def check_robustness():
                    t1 = time.time()                
                    slrc_result = slrc.is_robust(ma_problem)
                    t2 = time.time()                       
                    return t2-t1, slrc_result
                func_with_timeout = SetTimeout(check_robustness, timeout=PLANNER_TIMEOUT)
                is_done, is_timeout, erro_message, results = func_with_timeout()
                
                if is_timeout:
                    logging.info("Timed out")
                    print(domain, problem_file, "TO", "NA", sep=",", file=results_file, flush=True)
                else:
                    elapsed_time, slrc_result = results
                    logging.info("Took %s time to get result: %s", elapsed_time, slrc_result.status.name)
                    print(domain, problem_file, str(elapsed_time), slrc_result.status.name, sep=",", file=results_file, flush=True)

            except Exception as e:
                logging.error("Error in robustness checking: %s", e)
                continue


            logging.info("Success")

if __name__ == '__main__':
    main()