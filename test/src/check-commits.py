import requests
import datetime

def check_commits(repo_name):
    six_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    current_time = datetime.datetime.utcnow()

    commits_url = f"https://api.github.com/repos/{repo_name}/commits"
    params = {
        "since": six_hours_ago.isoformat(),
        "until": current_time.isoformat()
    }
    headers = {
        "accept": "application/vnd.github+json"  # Set the accept header
    }

    response = requests.get(commits_url, params=params, headers=headers)

    if response.status_code == 200:
        commits = response.json()
        return commits
    else:
        return None

if __name__ == "__main__":
    repo_name = "googlecolab/backend-info"
    commits = check_commits(repo_name)

    if commits:
        print("Commits found in the last 6 hours:")
        for commit in commits:
            print(commit['sha'])
    else:
        print("No commits found in the last 6 hours.")
