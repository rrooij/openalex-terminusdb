#!/usr/bin/env python3
import argparse
import subprocess
import threading
import os
import json

TERMINUSDB_COMMAND = './terminusdb'


def init_db(schema, threads):
    for x in range(0, threads):
        number = str(x)
        if x < 10:
            number = "0" + number
        try:
            subprocess.run(f"{TERMINUSDB_COMMAND} db delete admin/openalex_{number}", shell=True)
            subprocess.run(f'{TERMINUSDB_COMMAND} db create admin/openalex_{number}', shell=True)
        except:
            pass
    subprocess.run(f"{TERMINUSDB_COMMAND} db delete admin/openalex", shell=True)
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

def split_json(threads):
    subprocess.run(f"split -n l/{threads} -d -a 2 converted.json openalex_split", shell=True)


def ingest_json(filename, number, schema):
    db_name = f"openalex_{number}"
    db = f'admin/{db_name}'
    subprocess.run(f"{TERMINUSDB_COMMAND} doc insert {db} -g schema --full-replace < {schema}", shell=True)
    subprocess.run(f'{TERMINUSDB_COMMAND} doc insert {db} < {filename}', shell=True)
    subprocess.run(f'{TERMINUSDB_COMMAND} triples dump {db}/local/branch/main/instance > {db_name}.triples', shell=True)
    subprocess.run(f'{TERMINUSDB_COMMAND} triples load admin/openalex/local/branch/main/instance {db_name}.triples', shell=True)
    os.remove(f'{db_name}.triples')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=os.path.abspath)
    parser.add_argument("schema", type=os.path.abspath)
    parser.add_argument("threads", type=int)
    args = parser.parse_args()
    add_types(args.file)
    init_db(args.schema, args.threads)
    split_json(args.threads)
    for x in range(0, args.threads):
        number = str(x)
        if x < 10:
            number = "0" + number
        print("RUNNING THREAD " + number)
        t = threading.Thread(target=ingest_json, args=('openalex_split' + number, number, args.schema))
        t.start()
    # TODO: We have to squash all the different data products into one


if __name__ == '__main__':
    main()
