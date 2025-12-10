import os
import sys
import json
import re
import urllib.request


BOT_IDENTIFIER = '<!-- pr-check -->'  # used to detect/update comment


def github_api(url: str, method='GET', data=None):
    """Generic GitHub API request."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise RuntimeError('Missing GITHUB_TOKEN')

    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }

    req = urllib.request.Request(url, method=method, headers=headers)

    if data:
        req.data = json.dumps(data).encode('utf-8')

    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def update_pr_comment(owner: str, repo: str, pr_number: str, body: str):
    """Create or update a PR comment with a stable identifier."""
    comments_url = f'https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments'
    comments = github_api(comments_url)

    existing_id = None
    for c in comments:
        if c.get('body', '').startswith(BOT_IDENTIFIER):
            existing_id = c['id']
            break

    full_body = f'{BOT_IDENTIFIER}\n{body}'

    if existing_id:
        update_url = f'{comments_url}/{existing_id}'
        github_api(update_url, method='PATCH', data={'body': full_body})
        print(f'Updated PR comment (id={existing_id})')
    else:
        github_api(comments_url, method='POST', data={'body': full_body})
        print('Created PR comment')


def main() -> int:
    pr_url = os.environ.get('CIRCLE_PULL_REQUEST')
    owner = os.environ.get('CIRCLE_PROJECT_USERNAME')
    repo = os.environ.get('CIRCLE_PROJECT_REPONAME')

    if not pr_url:
        print('Not a PR build — skipping PR check')
        return 0

    pr_number = pr_url.rstrip('/').split('/')[-1]

    # Fetch PR details
    pr_data = github_api(
        f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}',
    )

    title = pr_data.get('title') or ''
    assignees = pr_data.get('assignees') or []
    labels = pr_data.get('labels') or []

    # ---- RULES ----
    errors = []

    # PR title must match:
    # "feat(core): add scoring API"
    # "fix: something"
    pattern = re.compile(r'^[a-z]+(\([^)]+\))?: .+')
    if not pattern.match(title):
        errors.append(
            f'❌ Invalid title: **{title}**\n'
            'Title must follow: `<type>(optional-domain): description`',
        )

    if not assignees:
        errors.append('❌ PR has **no assignee** — assign someone')

    if not labels:
        errors.append('❌ PR has **no labels** — add at least one')

    if errors:
        body = (
            '## 🔴 PR Check Failed\n'
            + '\n'.join(errors)
            + '\n\nPlease fix the above issues and re-run CI.'
        )
        update_pr_comment(owner, repo, pr_number, body)
        return 1

    # If OK
    body = (
        '## 🟢 PR Check Passed\n'
        f'**Title:** {title}\n'
        f'**Assignees:** {[a["login"] for a in assignees]}\n'
        f'**Labels:** {[label["name"] for label in labels]}\n'
        '\nAll requirements satisfied ✔️'
    )
    update_pr_comment(owner, repo, pr_number, body)
    return 0


if __name__ == '__main__':
    sys.exit(main())
