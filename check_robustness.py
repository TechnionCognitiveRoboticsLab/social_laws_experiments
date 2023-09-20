from unified_planning.shortcuts import *
from up_social_laws.sa_to_ma_converter import *
from unified_planning.io.pddl_reader import *
import random
import os
import json
import create_ma_benchmarks
import logging

PDDL_DOMAINS_PATH = "downward-benchmarks"
AGENT_TYPES_FILE = "domain_agent_types.json"
random.seed(2023)
logging.basicConfig(filename='social_law_experiments.log', encoding='utf-8', level=logging.DEBUG)


def main():
    logging.info("Starting robustness check")
    domain_agent_types = create_ma_benchmarks.get_ma_agent_types()

    for domain in domain_agent_types.keys():
        logging.info("Starting domain %s", domain)
        domain_filename = os.path.join(PDDL_DOMAINS_PATH, domain, "domain.pddl")        
        problems = os.listdir(os.path.join(PDDL_DOMAINS_PATH, domain)) 
        problems.remove("domain.pddl")
        logging.info("Got problems %s", problems)

        for problem_file in problems:
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

            ma_problem = samac_ret.problem
            logging.info("Success")

if __name__ == '__main__':
    main()