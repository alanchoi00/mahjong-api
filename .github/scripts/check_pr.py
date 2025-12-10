import os
import sys
import json
import re
import urllib.request

BOT_IDENTIFIER = '<!-- pr-check -->'  # used to detect/update comment


def github_api(url: str, method: str = 'GET', data=None):
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

    if data is not None:
        req.data = json.dumps(data).encode('utf-8')

    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def update_pr_comment(owner: str, repo: str, pr_number: int, body: str):
    """Create or update a PR comment with a stable identifier."""
    # List comments for this PR
    comments_url = f'https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments'
    comments = github_api(comments_url)

    existing_id = None
    for c in comments:
        if (c.get('body') or '').startswith(BOT_IDENTIFIER):
            existing_id = c['id']
            break

    full_body = f'{BOT_IDENTIFIER}\n{body}'

    if existing_id:
        update_url = f'https://api.github.com/repos/{owner}/{repo}/issues/comments/{existing_id}'
        github_api(update_url, method='PATCH', data={'body': full_body})
        print(f'Updated PR comment (id={existing_id})')
    else:
        github_api(comments_url, method='POST', data={'body': full_body})
        print('Created PR comment')


def main() -> int:
    # GitHub Actions context
    repo_full = os.environ.get('GITHUB_REPOSITORY')  # "owner/repo"
    event_path = os.environ.get('GITHUB_EVENT_PATH')

    if not repo_full or not event_path:
        print('Not running inside GitHub Actions with pull_request context.')
        return 0

    owner, repo = repo_full.split('/', 1)

    # Load event payload to get the PR number
    with open(event_path, encoding='utf-8') as f:
        event = json.load(f)

    # For pull_request events, this is always present
    pr_number = event.get('number')
    if not pr_number:
        print('No PR number found in event payload; skipping.')
        return 0

    # Fetch PR details
    pr_data = github_api(
        f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}',
    )

    title = pr_data.get('title') or ''
    assignees = pr_data.get('assignees') or []
    labels = pr_data.get('labels') or []

    # ---- Validation rules ----
    errors: list[str] = []

    # Title format: "<type>(optional-domain): description"
    # e.g. "feat(core): add scoring API", "fix: handle 500s"
    title_pattern = re.compile(r'^[a-z]+(\([^)]+\))?: .+')
    title_ok = bool(title_pattern.match(title))
    assignees_ok = bool(assignees)
    labels_ok = bool(labels)

    if not title_ok:
        errors.append(
            (
                'Title must follow the format '
                '`<type>(optional-domain): description` '
                '(for example: `feat(core): add scoring API`).'
            ),
        )

    if not assignees_ok:
        errors.append('An assignee must be set so ownership is clear.')

    if not labels_ok:
        errors.append('At least one label must be applied to the PR.')

    if errors:
        # Professional failure comment with status table
        status_rows = [
            f'| Title format | {"✅" if title_ok else "❌"} |',
            f'| Assignee set | {"✅" if assignees_ok else "❌"} |',
            f'| Labels set   | {"✅" if labels_ok else "❌"} |',
        ]
        status_table = '| Check | Status |\n|-------|--------|\n' + '\n'.join(
            status_rows,
        )

        body = (
            '## ❌ PR Health Check\n\n'
            'The automated PR checks found one or more issues with this '
            'pull request.\n\n'
            f'{status_table}\n\n'
            '### Details\n' + '\n'.join(f'- {msg}' for msg in errors) + '\n\n'
            'Once you have addressed the above items (e.g. updating the title, '
            'adding an assignee or labels), this check will re-run automatically '
            'on the next PR update.'
        )
        update_pr_comment(owner, repo, pr_number, body)
        return 1

    # Success: professional summary with table
    assignee_list = ', '.join(a['login'] for a in assignees) or '—'
    label_list = ', '.join(label['name'] for label in labels) or '—'

    summary_table = (
        '| Field     | Value |\n'
        '|-----------|-------|\n'
        f'| Title     | `{title}` |\n'
        f'| Assignees | {assignee_list} |\n'
        f'| Labels    | {label_list} |\n'
    )

    body = (
        '## ✅ PR Health Check Passed\n\n'
        'All required PR hygiene checks have been satisfied.\n\n'
        f'{summary_table}\n'
        '\nThank you for keeping the pull request metadata consistent and clear.'
    )
    update_pr_comment(owner, repo, pr_number, body)
    return 0


if __name__ == '__main__':
    sys.exit(main())
