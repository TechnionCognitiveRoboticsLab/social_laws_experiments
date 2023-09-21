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
from concurrent.futures import TimeoutError
from pebble import ProcessPool, ProcessExpired


PDDL_DOMAINS_PATH = "downward-benchmarks"
ROBUSTNESS_RESULTS_FILE = "robustness_results.csv"
PLANNER_TIMEOUT = 600

random.seed(2023)
logging.basicConfig(filename='social_law_experiments.log', encoding='utf-8', level=logging.DEBUG)
up.shortcuts.get_environment().credits_stream = None

def check_robustness(args):
    logging.info("Job pool started job: %s", args)
    domain, problem_name, agent_type = args
    reader = PDDLReader()
    try:
        logging.info("Reading %s:%s", domain, problem_name)
        domain_filename = os.path.join(PDDL_DOMAINS_PATH, domain, "domain.pddl")
        problem_filename = os.path.join(PDDL_DOMAINS_PATH, domain, problem_name)
        problem = reader.parse_problem(domain_filename, problem_filename)
    except Exception as e:
        logging.error("Failed to parse problem: %s", e)
        return -1
    
    logging.info("Converting to MA")
    try:
        samac = SingleAgentToMultiAgentConverter([agent_type])
        samac_ret = samac.compile(problem)
    except Exception as e:
        logging.error("Failed to convert to MA: %s", e)
        return -2

    logging.info("Checking robustness")
    try:
        ma_problem = samac_ret.problem
        slrc = SocialLawRobustnessChecker(planner_name="fast-downward")
        
        t1 = time.time()                
        slrc_result = slrc.is_robust(ma_problem)
        t2 = time.time()                       
        
        elapsed_time = t2 - t1

        logging.info("Took %s time to get result: %s for %s:%s", elapsed_time, slrc_result.status.name, domain, problem_name)
        with open(ROBUSTNESS_RESULTS_FILE, "a") as results_file:
            print(domain, problem_name, str(elapsed_time), slrc_result.status.name, sep=",", file=results_file, flush=True)

    except Exception as e:
        logging.error("Error in robustness checking: %s", e)
        return -3

    return 0

def generate_job_list():
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
            yield domain, problem_file, domain_agent_types[domain]

def main():
    # check_robustness(("transport-opt14-strips", "p01.pddl", "vehicle"))
    jobs = generate_job_list()
    job_list = list(jobs)

    with ProcessPool() as pool:
        future = pool.map(check_robustness, job_list, timeout=PLANNER_TIMEOUT)

if __name__ == '__main__':
    main()