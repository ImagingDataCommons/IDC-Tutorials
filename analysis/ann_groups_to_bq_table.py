"""
Script to query IDC for ANN objects referencing pathology whole-slide images, 
download and parse them in parallel, extract annotation group info, and write results to BigQuery.

Authentication:
This script uses Google Application Default Credentials (ADC). The recommended way to authenticate is to run:
    gcloud auth application-default login
in your terminal before running this script. Ensure your account has access to BigQuery and Cloud Storage resources.
"""
import concurrent.futures
from typing import List, Dict
from google.cloud import bigquery
from google.cloud import storage
from google.api_core.exceptions import NotFound
import highdicom as hd

# CONFIGURATION
PROJECT_ID = 'idc-pathomics-000'
QUERY_TO_IDC = '''
SELECT 
    dcm_all.SOPInstanceUID,
    dcm_all.SeriesInstanceUID, 
    dcm_all.gcs_url
FROM 
    `bigquery-public-data.idc_current.dicom_all` AS dcm_all
WHERE Modality = 'ANN' AND collection_id LIKE '%bonemarrowwsi%'
'''
MAX_WORKERS = 8  
BQ_DATASET = 'idc_pathology'
BQ_TABLE = 'annotation_groups'
BQ_TABLE_SCHEMA = [ 
    bigquery.SchemaField('SOPInstanceUID', 'STRING'),
    bigquery.SchemaField('SeriesInstanceUID', 'STRING'),
    bigquery.SchemaField('annotated_property_category', 'RECORD', fields=[
        bigquery.SchemaField('CodeValue', 'STRING'),
        bigquery.SchemaField('CodeMeaning', 'STRING'),
        bigquery.SchemaField('CodingSchemeDesignator', 'STRING'),
    ]),
    bigquery.SchemaField('annotated_property_type', 'RECORD', fields=[
        bigquery.SchemaField('CodeValue', 'STRING'),
        bigquery.SchemaField('CodeMeaning', 'STRING'),
        bigquery.SchemaField('CodingSchemeDesignator', 'STRING'),
    ]),
    bigquery.SchemaField('num_annotations', 'INTEGER'),
    bigquery.SchemaField('annotated_SeriesInstanceUID', 'STRING'),
]


def query_ann_files(client: bigquery.Client) -> List[Dict]:
    query_job = client.query(QUERY_TO_IDC)
    return [dict(row) for row in query_job]


def process_ann_files(rows: List[Dict]) -> List[Dict]:
    storage_client = storage.Client(project=PROJECT_ID)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_row = {
            executor.submit(
                parse_ann_blob,
                storage_client,
                row['gcs_url'],
                row['SOPInstanceUID'],
                row['SeriesInstanceUID']
            ): row for row in rows
        }
        for future in concurrent.futures.as_completed(future_to_row):
            row = future_to_row[future]
            try:
                ann_results = future.result()
                results.extend(ann_results)
            except Exception as e:
                print(f'Error processing {row["gcs_url"]}: {e}')
    return results


def parse_ann_blob(storage_client: storage.Client, gcs_url: str, sop_instance_uid: str,series_instance_uid: str) -> List[Dict]:
    # Parse bucket and blob name from GCS URL
    parts = gcs_url[5:].split('/', 1)
    bucket_name, blob_name = parts[0], parts[1]
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    results = []
    with blob.open('rb') as file_obj:
        ann = hd.ann.annread(file_obj)
        for ann_group in ann.get_annotation_groups():
            results.append({
                'SOPInstanceUID': sop_instance_uid,
                'SeriesInstanceUID': series_instance_uid,
                'annotated_property_category': coded_concept_to_dict(ann_group.annotated_property_category),
                'annotated_property_type': coded_concept_to_dict(ann_group.annotated_property_type),
                'num_annotations': ann_group.number_of_annotations, 
                'annotated_SeriesInstanceUID': ann.ReferencedSeriesSequence[0].SeriesInstanceUID
            })
    return results


def coded_concept_to_dict(cc):
    return {
        'CodeValue': cc.value,
        'CodeMeaning': cc.meaning,
        'CodingSchemeDesignator': cc.scheme_designator
    } if cc is not None else None


def main():
    bq_client = bigquery.Client(project=PROJECT_ID)
    # Query ANN files
    rows = query_ann_files(bq_client)
    print(f'Found {len(rows)} ANN files to process.')
    # Process ANN files in parallel
    results = process_ann_files(rows)
    print(f'Extracted annotation group info from {len(results)} groups.')
    # Write to BigQuery
    if results:
        table_ref = bq_client.dataset(BQ_DATASET).table(BQ_TABLE)
        # Always delete and recreate the table before inserting
        try:
            bq_client.delete_table(table_ref, not_found_ok=True)
            print(f'Table {BQ_TABLE} deleted.')
        except Exception as e:
            print(f'Error deleting table: {e}')
        table = bigquery.Table(table_ref, schema=BQ_TABLE_SCHEMA)
        bq_client.create_table(table)
        print(f'Table {BQ_TABLE} created.')
        # Retry loop to ensure table is available before inserting
        import time
        found = False
        for _ in range(10):
            try:
                bq_client.get_table(table_ref)
                found = True
                break
            except NotFound:
                time.sleep(2)
        if not found:
            print(f'Error: Table {BQ_TABLE} not found after creation. Saving results locally as ann_groups_results.json.')
            import json
            with open('ann_groups_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            return
        errors = bq_client.insert_rows_json(table_ref, results)
        if errors:
            print(f'BigQuery insert errors: {errors}')
        else:
            print('Results written to BigQuery.')
    else:
        print('No results to write.')


if __name__ == '__main__':
    main()
