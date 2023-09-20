from unified_planning.shortcuts import *
from up_social_laws.sa_to_ma_converter import *
from unified_planning.io.pddl_reader import *
import random
import os
import json
import logging

PDDL_DOMAINS_PATH = "downward-benchmarks"
AGENT_TYPES_FILE = "domain_agent_types.json"
random.seed(2023)
logging.basicConfig(filename='social_law_experiments.log', encoding='utf-8', level=logging.DEBUG)


"""
This module contains code that scans through all of the PDDL domains in PDDL_DOMAINS_PATH (downward-benchmarks).
For each domain (which contains a single domain.pddl file) it chooses a random problem instance, 
and then tries to convert it to a multi-agent problem using each of the types in the domain as the agents.
If it finds a type that works, it stores it in a dictionary.

To speed things up, this dictionary is cached in a file called AGENT_TYPES_FILE (domain_agent_types.json).
If this file exists, the computation is skipped and the results are loaded.
"""


def convert_to_ma(domain, problem, domain_file = "domain.pddl"):
    logging.info("Reading %s : %s", domain, problem)
    reader = PDDLReader()
    domain_filename = os.path.join(PDDL_DOMAINS_PATH, domain, domain_file)
    problem_filename = os.path.join(PDDL_DOMAINS_PATH, domain, problem)
    
    try:
        problem = reader.parse_problem(domain_filename, problem_filename)
    except Exception as e:
        logging.info("Error parsing: %s", e)
        return None
        
    for utype in problem.user_types:
        agents = [utype.name]
        try:            
            logging.info("Trying type %s as agent", utype.name)
            samac = SingleAgentToMultiAgentConverter(agents)
            ret = samac.compile(problem)            
            return utype.name
        except Exception as e:
            logging.info("Error converting: %s", e)            
    return None

def search_for_ma_agent_types():
    domain_agent_type = {}

    for domain in os.listdir(PDDL_DOMAINS_PATH):
        if os.path.isdir(os.path.join(PDDL_DOMAINS_PATH, domain)):
            if os.path.exists(os.path.join(PDDL_DOMAINS_PATH, domain, "domain.pddl")):
                problems = os.listdir(os.path.join(PDDL_DOMAINS_PATH, domain)) 
                problems.remove("domain.pddl")
                rand_problem = random.choice(problems)
                ret = convert_to_ma(domain, rand_problem)
                if ret is not None:
                    domain_agent_type[domain] = ret
    return domain_agent_type

def get_ma_agent_types():
    if os.path.exists(AGENT_TYPES_FILE):
        logging.info("File exists, reading it")
        with open(AGENT_TYPES_FILE, 'r') as openfile:
            domain_agent_types = json.load(openfile)        
    else:
        logging.info("File does not exist, search for types")
        domain_agent_types = search_for_ma_agent_types()
        with open(AGENT_TYPES_FILE, "w") as outfile:
            json.dump(domain_agent_types, outfile)
    return domain_agent_types

if __name__ == '__main__':
    domain_agent_types = get_ma_agent_types()
    print(domain_agent_types)

