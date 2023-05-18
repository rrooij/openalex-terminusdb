#!/usr/bin/env python3
import argparse
import subprocess
import threading
import os

def init_db(schema, threads):
    for x in range(0, threads):
        try:
            subprocess.run(f"./terminusdb db delete admin/openalex_{x}", shell=True)
        except:
            pass
    subprocess.run("./terminusdb db delete admin/openalex", shell=True)
    subprocess.run("./terminusdb db create admin/openalex", shell=True)
    subprocess.run(f"./terminusdb doc insert admin/openalex -g schema --full-replace < {schema}", shell=True)

def split_json(filename, threads):
    subprocess.run(f"split -n l/{threads} -d -a 1 {filename} openalex_split", shell=True)

def ingest_json(filename, number, schema):
    db = f'admin/openalex_{number}'
    subprocess.run(f'./terminusdb db create {db}', shell=True)
    subprocess.run(f"./terminusdb doc insert {db} -g schema --full-replace < {schema}", shell=True)
    subprocess.run(f'./terminusdb doc insert {db} < {filename}', shell=True)

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
        print("RUNNING THREAD " + number)
        t = threading.Thread(target=ingest_json, args=('openalex_split' + number, number, args.schema))
        t.start()
    # TODO: We have to squash all the different data products into one


if __name__ == '__main__':
    main()
