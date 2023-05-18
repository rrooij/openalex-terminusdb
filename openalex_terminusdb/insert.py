#!/usr/bin/env python3
import argparse
import subprocess
import threading
import os

TERMINUSDB_COMMAND = './terminusdb'

def init_db(schema, threads):
    for x in range(0, threads):
        number = str(x)
        if x < 10:
            number = "0" + number
        try:
            subprocess.run(f"{TERMINUSDB_COMMAND} db delete admin/openalex_{number}", shell=True)
        except:
            pass
    subprocess.run(f"{TERMINUSDB_COMMAND} db delete admin/openalex", shell=True)
    subprocess.run(f"{TERMINUSDB_COMMAND} db create admin/openalex", shell=True)
    subprocess.run(f"{TERMINUSDB_COMMAND} doc insert admin/openalex -g schema --full-replace < {schema}", shell=True)

def split_json(filename, threads):
    subprocess.run(f"split -n l/{threads} -d -a 2 {filename} openalex_split", shell=True)

def ingest_json(filename, number, schema):
    db_name = f"openalex_{number}_"
    db = f'admin/{db_name}'
    subprocess.run(f'{TERMINUSDB_COMMAND} db create {db}', shell=True)
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
    init_db(args.schema, args.threads)
    split_json(args.file, args.threads)
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
