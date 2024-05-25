import subprocess
import nbformat


def modify_notebook(file_name, project_id, query1, query2):
    # Load the notebook
    with open(file_name) as f:
        nb = nbformat.read(f, as_version=4)

    # Loop over the cells
    for cell in nb.cells:
        if cell.cell_type == "code":
            # Replace the line if it exists
            cell.source = cell.source.replace(
                'my_ProjectID = "" #@param {type:"string"}',
                f"#this project_id is injected for testing\nmy_ProjectID='{project_id}'",
            )
            # Comment out another line
            cell.source = cell.source.replace(
                "auth.authenticate_user()",
                "#while testing, the authentication is handled by using application default credentials\n#auth.authenticate_user()",
            )
            cell.source = cell.source.replace(
                "REPLACE THIS TEXT WITH YOUR QUERY!", query1
            )
            cell.source = cell.source.replace(
                "# write the selection criteria under this line!", query2
            )
            cell.source = (
                "# " + cell.source.replace("\n", "\n# ")
                if cell.source.lower().startswith("viewer")
                else cell.source
            )

    # Write the notebook back to disk
    with open(file_name, "w") as f:
        nbformat.write(nb, f)


# Command to run
files = [
    "notebooks/getting_started/part1_prerequisites.ipynb",
    "notebooks/getting_started/part2_searching_basics.ipynb",
    "notebooks/getting_started/part3_exploring_cohorts.ipynb",
]

for file_name in files:

    project_id = "idc-external-025"
    query1 = (
        "#this query is injected for testing\n SELECT DISTINCT collection_tumorLocation FROM `bigquery-public-data.idc_current.dicom_all` "
        if "part2" in file_name
        else ""
    )
    query2 = (
        "#this query is injected for testing\n MODALITY='MR' AND collection_tumorLocation='Lung'"
        if "part2" in file_name
        else ""
    )
    modify_notebook(file_name, project_id, query1, query2)
