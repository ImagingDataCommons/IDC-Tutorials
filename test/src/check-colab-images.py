import json
import csv
import re
import pandas as pd
import subprocess

def main():
    # Step 1: Run the command to fetch Docker image information and save it to 'tags.json'
    result = subprocess.run(
        'gcloud artifacts docker tags list us-docker.pkg.dev/colab-images/public/runtime --format=json --quiet',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

    # Write the output to a file
    with open('tags.json', 'w') as f:
        f.write(result.stdout.decode('utf-8'))

    with open('tags.json', 'r') as json_file:
        data = json.load(json_file)

    # Step 3: Create a DataFrame from the JSON data
    df = pd.DataFrame(data)
    df["tag"] = df["tag"].str.split("tags/").str[1]
    df['docker_pull_tag'] = df['image'] + ':' + df['tag']
    df["date"] = df["tag"].apply(lambda x: re.search(r'\d{8}', x).group(0) if re.search(r'\d{8}', x) else None)
    df["sha256"] = df["version"].apply(lambda x: re.search(r'sha256:[a-f0-9]+', x).group(0) if re.search(r'sha256:[a-f0-9]+', x) else None)
    df['docker_pull_sha256_tag'] = df['image'] + '@' + df['sha256']

    df = df[['date', 'tag', 'sha256', 'docker_pull_tag', 'docker_pull_sha256_tag']]

    # Step 5: Read the existing CSV file from the local repository
    try:
        existing_df = pd.read_csv('test/colab-images-list.csv')
    except FileNotFoundError:
        print("Failed to read CSV file from local repository.")
        existing_df = None

    # Step 6: Compare 'latest' tag and SHA256 digest
    if existing_df is not None:
        latest_df = existing_df[existing_df['tag'] == 'latest']
        if not latest_df.empty:
            existing_sha256 = latest_df.iloc[0]['sha256']
            print('existing_sha256= '+existing_sha256)
            current_sha256 = df[df['tag'] == 'latest'].iloc[0]['sha256']
            print('current_sha256= '+current_sha256)
            if existing_sha256 != current_sha256:
                print("SHA256 digest has changed!")
                # Perform actions if the digest has changed, like updating GitHub Actions.
                df.to_csv('test/colab-images-list.csv', index=False)  # Save the new DataFrame as 'database.csv'
                print("Updated the database CSV.")
                result = True
            else:
                print("SHA256 digest has not changed.")
                # Perform actions if the digest has not changed, like returning False or taking no further action.
                result = False
        else:
            print("No 'latest' tag found in the existing DataFrame.")
            result = False
    else:
        print("Failed to read existing CSV data.")
        result = False

    # Return True or False based on whether the database has changed
    return str(result)  # Return as a string


if __name__ == "__main__":
    result = main()
    print(result)
    with open('check_colab_images_result.txt', 'w') as result_file:
        result_file.write(result)
