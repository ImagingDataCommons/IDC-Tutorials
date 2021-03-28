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
    def __init__(self, paying_project, thread_count, test_mode):
        self._lock = threading.Lock()
        self._threads = []
        self._paying_project = paying_project
        self._test_mode = test_mode
        self._total_files = 0
        self._read_files = 0
        self._thread_count = thread_count
        self._bar_bump = 0

    def __str__(self):
        return "BucketPuller"

    def reset(self):
        self._threads.clear()
        self._total_files = 0
        self._read_files = 0
        self._bar_bump = 0

    def pull_from_buckets(self, pull_list, local_files_dir):
        self._total_files = len(pull_list)
        self._bar_bump = self._total_files // 100
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

        print_progress_bar(self._read_files, self._total_files)
        return

    def _pull_func(self, pull_list, local_files_dir):
        storage_client = storage.Client()
        for url in pull_list:
            path_pieces = up.urlparse(url)
            dir_name = os.path.dirname(path_pieces.path)
            make_dir = "{}{}".format(local_files_dir, dir_name)
            os.makedirs(make_dir, exist_ok=True)
            bucket = storage_client.bucket(path_pieces.netloc, user_project=self._paying_project)
            blob = bucket.blob(path_pieces.path[1:])  # drop leading / from blob name
            full_file = "{}{}".format(local_files_dir, path_pieces.path)
            blob.download_to_filename(full_file)
            if self._test_mode:
                os.remove(full_file)
            self._bump_progress()

    def _bump_progress(self):

        with self._lock:
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
Pull BQ manifest to local file
'''

def pull_manifest(limit, table, manifest_file):

    if limit is not None:
        query= "SELECT * FROM `{}` limit {}".format(table, limit)
    else:
        query = "SELECT * FROM `{}`}".format(table)

    results = bq_harness_with_result(query, False)

    with open(manifest_file, 'w+') as outfile:
        for row in results:
            gu = row.gcs_url
            outfile.write(gu)
            outfile.write('\n')

    return

'''
----------------------------------------------------------------------------------------------
Pull files to disk
'''

def pull_files(manifest_file, local_files_dir, paying_project, threads, test_mode):

    with open(manifest_file, mode='r') as pull_list_file:
        pull_list = pull_list_file.read().splitlines()
        print("Preparing to download %s files from buckets\n" % len(pull_list))
        bp = BucketPuller(paying_project, threads, test_mode)
        bp.pull_from_buckets(pull_list, local_files_dir)
        print("DONE\n")
    return

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
    MANIFEST_FILE = '/path-to-your-home-dir/BQ-MANIFEST.txt' # Where will manifest file go
    TARG_DIR = '/path-to-your-home-dir/black_hole' # Since we are testing, stuff gets deleted after download
    PAYING = 'your-project-id' # Needed for requester pays though it is free to crossload to a VM
    THREADS = 16 # 2 * number of cpus seems to work best
    TEST_MODE = True # Files deleted after download, so timing tests do not need lots of VM memory

    print_time()
    pull_manifest(NUM, TABLE, MANIFEST_FILE)
    print_time()
    pull_files(MANIFEST_FILE, TARG_DIR, PAYING, THREADS, TEST_MODE)
    print_time()

    return

'''
----------------------------------------------------------------------------------------------
Pull files to disk
'''
def main(args):

    NUM = None  # Don't chop off the table if you are not just testing...
    TABLE = 'your-project-id.your-dataset.your-manifest-table' # BQ table with your manifest
    MANIFEST_FILE = '/path-to-your-home-dir/BQ-MANIFEST.txt' # Where will manifest file go
    # With IDC data version 1, DICOM files live in a bucket with a hierarchical structure, so
    # this directory will be filled with subdirectories of studies which hold subdirectories
    # of series. Starting IDC data verion 2, buckets will be flat, and additional information
    # will be needed to build the hierarchy. Stay tuned:
    TARG_DIR = '/path-to-your-home-dir/destination'
    PAYING = 'your-project-id'  # Needed for requester pays though it is free to crossload to a VM
    THREADS = 16 # 2 * number of cpus seems to work best
    TEST_MODE = False

    pull_manifest(NUM, TABLE, MANIFEST_FILE)
    pull_files(MANIFEST_FILE, TARG_DIR, PAYING, THREADS, TEST_MODE)

    return

if __name__ == '__main__':
    main(sys.argv)
