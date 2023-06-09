#!/usr/bin/env python3
import argparse
import subprocess
import threading
import os
import json
import sys
import time
from multiprocessing import Pool

TERMINUSDB_COMMAND = 'terminusdb'

def prefix_number(number):
    str_number = str(number)
    if number < 10:
        return "00" + str_number
    elif number < 100:
        return "0" + str_number
    return str_number

def init_db(schema, threads):
    for x in range(0, threads):
        number = prefix_number(x)
        try:
#            subprocess.run(f"{TERMINUSDB_COMMAND} db delete admin/openalex_{number}", shell=True)
            subprocess.run(f'{TERMINUSDB_COMMAND} db create admin/openalex_{number}', shell=True)
        except:
            pass
#    subprocess.run(f"{TERMINUSDB_COMMAND} db delete admin/openalex", shell=True)
    subprocess.run(f"{TERMINUSDB_COMMAND} db create admin/openalex", shell=True)
    subprocess.run(f"{TERMINUSDB_COMMAND} doc insert admin/openalex -g schema --full-replace < {schema}", shell=True)

def add_types(filename):
    with open(filename, 'r') as f:
        with open('converted.json', 'w') as f2:
            lines = f.readlines()
            for line in lines:
                parsed = json.loads(line)
                parsed['@type'] = 'Author'
                json.dump(parsed, f2)
                f2.write("\n")

def split_json(threads, filename):
    subprocess.run(f"split -n l/{threads} -d -a 3 {filename} openalex_split", shell=True)


def split_db_json(threads, filename):
    subprocess.run(f"split -n l/{threads} -d -a 3 {filename} dbs/db_split", shell=True)

def apply_triples(threads):
    print("APPLYING TRIPPLES")
    for x in range(0, threads):
        number = prefix_number(x)
        db_name = f"openalex_{number}"
        db = f'admin/{db_name}'
        start = time.time()
        subprocess.run(f'{TERMINUSDB_COMMAND} triples load admin/openalex/local/branch/main/instance {db_name}.triples', shell=True)
        subprocess.run(f'sudo docker exec -i terminusdb /bin/bash -c \'rm -rf {db_name}.triples\'', shell=True)

def ingest_json(args):
    start = time.time()
    filename = args[0]
    number = args[1]
    schema = args[2]
    db_name = f"openalex_{number}"
    db = f'admin/{db_name}'
    with open(f"log/{db_name}.log", 'w') as f:
        subprocess.run(f"{TERMINUSDB_COMMAND} doc insert {db} -g schema --full-replace < {schema}", shell=True, stdout=f, stderr=f)
        subprocess.run(f'{TERMINUSDB_COMMAND} doc insert {db} < {filename}', shell=True, stdout=f, stderr=f)
        end_insert = time.time() - start
        f.write(f"\n\nEND TIME: {end_insert}\n")
#    print(f"THREAD {number} finished inserting in: {end_insert} seconds")
#    start = time.time()
#    subprocess.run(f'sudo docker exec -i terminusdb /bin/bash -c \'./terminusdb triples dump {db}/local/branch/main/instance > {db_name}.triples\'', shell=True)
#    end_triples = time.time() - start
#    print(f"THREAD {number} dumped triples in: {end_triples} seconds")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=os.path.abspath)
    parser.add_argument("schema", type=os.path.abspath)
    parser.add_argument("split", type=int)
    parser.add_argument("threads", type=int)
    args = parser.parse_args()
#    add_types(args.file)
    init_db(args.schema, args.split)
#    split_json(args.split, args.file)
    threads = []
    split_db_json(threads, 'dbs.list')
    args_process = [('openalex_split' + prefix_number(x), prefix_number(x), args.schema) for x in range(0, args.split)]
    with Pool(args.threads) as p:
        # Ingest JSON
        p.map(ingest_json, args_process)
    print("FINISHED")
#    apply_triples(args.threads)
    # TODO: We have to squash all the different data products into one


if __name__ == '__main__':
    main()
