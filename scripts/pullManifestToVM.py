"""

Copyright 2018-2021, Institute for Systems Biology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from google.cloud import bigquery
from google.cloud import storage
import threading
import sys
import time
import os
import shutil
import csv
from datetime import datetime
import urllib.parse as up

'''
A key part of working in the cloud is pulling the file manifest for a cohort out of a BigQuery table onto
a VM, and then crossloading all the files from the storage buckets onto the VM. This example script shows
how this can be done.
'''

'''
----------------------------------------------------------------------------------------------
A class that pulls files from buckets using the specified number of threads
'''

class BucketPuller(object):
    """Multithreaded  bucket puller"""
    def __init__(self, paying_project, thread_count, test_mode, size_only=False):
        self._lock = threading.Lock()
        self._path_lock = threading.Lock()
        self._threads = []
        self._paying_project = paying_project
        self._test_mode = test_mode
        self._total_files = 0
        self._read_files = 0
        self._thread_count = thread_count
        self._bar_bump = 0
        self._total_bytes = 0
        self._size_only = size_only
        self._paths_dict = None

    def __str__(self):
        return "BucketPuller"

    def reset(self):
        self._threads.clear()
        self._total_files = 0
        self._read_files = 0
        self._bar_bump = 0
        self._total_bytes = 0
        self._paths_dict = None

    def pull_from_buckets(self, pull_list, paths_tsv, local_files_dir):
        self._total_files = len(pull_list)
        self._bar_bump = self._total_files // 100
        # Build the paths dict:
        print("Bulding the paths dict")
        self._paths_dict = {}
        with open(paths_tsv, 'rt') as path_file:
            tsv_reader = csv.reader(path_file, delimiter='\t')
            for row in tsv_reader:
                self._paths_dict[row[0]] = row[1]
        print("Done")

        if self._bar_bump == 0:
            self._bar_bump = 1
        size = self._total_files // self._thread_count
        size = size if self._total_files % self._thread_count == 0 else size + 1
        chunks = [pull_list[pos:pos + size] for pos in range(0, self._total_files, size)]
        for i in range(0, self._thread_count):
            if i >= len(chunks):
                break
            th = threading.Thread(target=self._pull_func, args=(chunks[i], local_files_dir))
            self._threads.append(th)

        for i in range(0, len(self._threads)):
            self._threads[i].start()

        for i in range(0, len(self._threads)):
            self._threads[i].join()

        print("Done")
        return self._total_bytes

    def _pull_func(self, pull_list, local_files_dir):
        storage_client = storage.Client()
        for url in pull_list:
            url_path_pieces = up.urlparse(url)
            file_path = self._path_for_file(url)
            dir_name = os.path.dirname(file_path)
            make_dir = "{}/{}".format(local_files_dir, dir_name)
            os.makedirs(make_dir, exist_ok=True)
            bucket = storage_client.bucket(url_path_pieces.netloc, user_project=self._paying_project)
            if self._size_only:
                # get_blob gets the metadata without the actual fetch of the data:
                blob = bucket.get_blob(url_path_pieces.path[1:])  # drop leading / from blob name
                size_bump = blob.size if blob.size is not None else 0
                self._bump_size(size_bump)
            else:
                blob = bucket.blob(url_path_pieces.path[1:])  # drop leading / from blob name
                full_file = "{}/{}".format(local_files_dir, file_path)
                blob.download_to_filename(full_file)
                size_bump = os.path.getsize(full_file)
                if self._test_mode:
                    os.remove(full_file)
                self._bump_size(size_bump)

    def _path_for_file(self, gcs_url):
        with self._path_lock:
            return self._paths_dict[gcs_url]


    def _bump_size(self, size):
        with self._lock:
            self._total_bytes += size
            self._read_files += 1
            if (self._read_files % self._bar_bump) == 0:
                print_progress_bar(self._read_files, self._total_files)


'''
----------------------------------------------------------------------------------------------
Print a progress bar
'''

def print_progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Ripped from Stack Overflow.
    https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    H/T to Greenstick: https://stackoverflow.com/users/2206251/greenstick

    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()
    return

'''
----------------------------------------------------------------------------------------------
Use to run queries where we want to get the result back to use (not write into a table)
'''

def bq_harness_with_result(sql, do_batch):
    """
    Handles all the boilerplate for running a BQ job
    """

    client = bigquery.Client()
    job_config = bigquery.QueryJobConfig()
    if do_batch:
        job_config.priority = bigquery.QueryPriority.BATCH
    location = 'US'

    # API request - starts the query
    query_job = client.query(sql, location=location, job_config=job_config)

    # Query
    job_state = 'NOT_STARTED'
    while job_state != 'DONE':
        query_job = client.get_job(query_job.job_id, location=location)
        print('Job {} is currently in state {}'.format(query_job.job_id, query_job.state))
        job_state = query_job.state
        if job_state != 'DONE':
            time.sleep(5)
    print('Job {} is done'.format(query_job.job_id))

    query_job = client.get_job(query_job.job_id, location=location)
    if query_job.error_result is not None:
        print('Error result!! {}'.format(query_job.error_result))
        return None

    results = query_job.result()

    return results

'''
----------------------------------------------------------------------------------------------
Find out the size needed for the manifest by gathering storage metadata
*Vastly* faster and more preferable technique is to use BigQuery
'''

def get_loading_size(manifest_file, paying_project, threads):

    with open(manifest_file, mode='r') as pull_list_file:
        pull_list = pull_list_file.read().splitlines()
        print("Preparing to check size of %s files f\n" % len(pull_list))
        bp = BucketPuller(paying_project, threads, True, size_only=True)
        total_size = bp.pull_from_buckets(pull_list, None, None)
    return total_size

'''
----------------------------------------------------------------------------------------------
Pull BQ manifest to local file
'''

def pull_manifest(limit, table, manifest_file):

    if limit is not None:
        query= "SELECT * FROM `{}` limit {}".format(table, limit)
    else:
        query = "SELECT * FROM `{}`".format(table)

    results = bq_harness_with_result(query, False)

    with open(manifest_file, 'w+') as outfile:
        for row in results:
            gu = row.gcs_url
            outfile.write(gu)
            outfile.write('\n')
    return

'''
----------------------------------------------------------------------------------------------
Find the size of the load
'''

def find_size(manifest_table, aux_table):

    query = '''
            SELECT SUM(Instance_Size) as tot_size
            FROM `{}` as met
            JOIN `{}` as coh
            ON coh.gcs_url = met.gcs_url
            '''.format(aux_table, manifest_table)

    results = bq_harness_with_result(query, False)

    size_sum = 0
    for row in results:
        size_sum = row.tot_size
        break

    return size_sum

'''
----------------------------------------------------------------------------------------------
Build the paths file
'''

def build_paths(manifest_table, aux_table, path_tsv_file):

    query = '''
            SELECT met.gcs_url, met.SOPInstanceUID, met.StudyInstanceUID, met.SeriesInstanceUID, Instance_Size
            FROM `{}` as met
            JOIN `{}` as coh
            ON coh.gcs_url = met.gcs_url
            '''.format(aux_table, manifest_table)

    results = bq_harness_with_result(query, False)
    print("Bulding the paths file")
    with open(path_tsv_file, 'wt') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        for row in results:
            gu = row.gcs_url
            path = "%s/%s/%s.dcm" % (row.StudyInstanceUID, row.SeriesInstanceUID, row.SOPInstanceUID)
            tsv_array = [gu, path]
            tsv_writer.writerow(tsv_array)
    print("Done")

    return

'''
----------------------------------------------------------------------------------------------
Pull files to disk
'''

def pull_files(manifest_file, local_files_dir, paths_tsv, paying_project, threads, test_mode):

    with open(manifest_file, mode='r') as pull_list_file:
        pull_list = pull_list_file.read().splitlines()
        print("Preparing to download %s files from buckets\n" % len(pull_list))
        bp = BucketPuller(paying_project, threads, test_mode)
        size = bp.pull_from_buckets(pull_list, paths_tsv, local_files_dir)
    return size

'''
----------------------------------------------------------------------------------------------
Print time
'''
def print_time():
    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    return

'''
----------------------------------------------------------------------------------------------
Run a timing test
'''

def timing_test(args):

    NUM = 20000
    TABLE = 'your-project-id.your-dataset.your-manifest-table' # BQ table with your manifest
    AUX_TABLE = 'canceridc-data.idc.auxilliary_metadata'
    MANIFEST_FILE = '/path-to-your-home-dir/BQ-MANIFEST.txt' # Where will manifest file go
    PATHS_TSV_FILE = '/path-to-your-home-dir/PATHS.tsv' # Where will path file go
    TARG_DIR = '/path-to-your-home-dir/black_hole' # Since we are testing, stuff gets deleted after download
    PAYING = 'your-project-id' # Needed for requester pays though it is free to crossload to a VM
    THREADS = 16 # 2 * number of cpus seems to work best
    TEST_MODE = True # Files deleted after download, so timing tests do not need lots of VM memory

    print_time()
    pull_manifest(NUM, TABLE, MANIFEST_FILE)
    print_time()
    build_paths(TABLE, AUX_TABLE, PATHS_TSV_FILE)
    print_time()
    find_size(TABLE, AUX_TABLE)
    print_time()
    pull_files(MANIFEST_FILE, TARG_DIR, PATHS_TSV_FILE, PAYING, THREADS, TEST_MODE)
    print_time()
    return

'''
----------------------------------------------------------------------------------------------
Pull files to disk
'''
def main(args):

    NUM = None  # Don't chop off the table if you are not just testing...
    TABLE = 'your-project-id.your-dataset.your-manifest-table' # BQ table with your manifest
    AUX_TABLE = 'canceridc-data.idc.auxilliary_metadata'
    MANIFEST_FILE = '/path-to-your-home-dir/BQ-MANIFEST.txt' # Where will manifest file go
    PATHS_TSV_FILE = '/path-to-your-home-dir/PATHS.tsv' # Where will path file go
    # With IDC data version 1, DICOM files live in a bucket with a hierarchical structure, so
    # this directory will be filled with subdirectories of studies which hold subdirectories
    # of series. Starting IDC data verion 2, buckets will be flat, and additional information
    # will be needed to build the hierarchy. Stay tuned:
    TARG_DIR = '/path-to-your-home-dir/destination'
    PAYING = 'your-project-id'  # Needed for requester pays though it is free to crossload to a VM
    THREADS = 16 # 2 * number of cpus seems to work best
    TEST_MODE = False # If set to true, will delete files after it downloaded (timing test only!)

    #
    # Get the manifest out of BigQuery into a local file:
    #

    pull_manifest(NUM, TABLE, MANIFEST_FILE)

    #
    # Build the file that maps bucket location to a file in the DICOM study/series/instance directory hierarchy:
    #

    build_paths(TABLE, AUX_TABLE, PATHS_TSV_FILE)

    #
    # Figure out how big the pull will be, and if we have enough space:
    #

    pull_size = find_size(TABLE, AUX_TABLE)
    print("Your machine will need %i bytes of storage for this download" % pull_size)
    total, used, free = shutil.disk_usage(TARG_DIR)
    print("total: %i used: %i free: %i" % (total, used, free))
    overrun = pull_size - free

    #
    # If we have the space, do the pull:
    #

    if overrun > 0:
        print("Insufficient disk space in target directory. %i more bytes needed" % overrun)
    else:
        size = pull_files(MANIFEST_FILE, TARG_DIR, PATHS_TSV_FILE, PAYING, THREADS, TEST_MODE)
        print("Your machine used %i bytes of storage for this download" % size)

    return

if __name__ == '__main__':
    main(sys.argv)
