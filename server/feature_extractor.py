"""
Extracts the same 6-month feature set used during model training,
given a GitHub repo name (e.g. "owner/repo").

All features are strictly bounded to [repo_created, repo_created + 6 months]
to match the training data exactly and avoid temporal leakage.
"""

import re
import time
import os
import requests
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

# Github token is needed so API requests are made as authenticated user
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# =================================================
# Helpers
# =================================================

def safe_divide(numerator, denominator):
    try:
        if denominator and denominator > 0:
            return round(numerator / denominator, 2)
    except (ZeroDivisionError, TypeError):
        pass
    return 0.0


def parse_datetime(dt_str):
    if dt_str is None:
        return None
    if isinstance(dt_str, datetime):
        return dt_str if dt_str.tzinfo else dt_str.replace(tzinfo=timezone.utc)
    try:
        s = str(dt_str).strip().replace(" ", "T")
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


def github_get(url, params=None, headers_override=None, retries=3):
    hdrs = headers_override or HEADERS
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=hdrs, params=params, timeout=30)
            if r.status_code == 403:
                remaining = int(r.headers.get("X-RateLimit-Remaining", 1))
                if remaining == 0:
                    reset_ts = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
                    sleep_for = max(reset_ts - time.time(), 1) + 2
                    time.sleep(sleep_for)
                    continue
            if r.status_code in (500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            return r
        except requests.exceptions.RequestException:
            time.sleep(2 ** attempt)
    return None


def paginate(url, params=None, headers_override=None, max_pages=100):
    base_params = {"per_page": 100, "page": 1}
    if params:
        base_params.update(params)
    for page_num in range(1, max_pages + 1):
        base_params["page"] = page_num
        r = github_get(url, params=dict(base_params), headers_override=headers_override)
        if r is None or r.status_code != 200:
            break
        data = r.json()
        if not isinstance(data, list) or not data:
            break
        yield from data
        if len(data) < base_params["per_page"]:
            break
        time.sleep(0.05)


# =================================================
# PyPI package name → GitHub repo resolver
# =================================================

def resolve_repo_from_input(user_input: str):
    """
    Accepts either:
      - A full GitHub URL: https://github.com/owner/repo (example: https://github.com/psf/requests)
      - A PyPI package name: requests.

    Returns (owner/repo string, repo_url) or raises ValueError.
    """
    user_input = user_input.strip()

    # Already a GitHub URL
    gh_match = re.match(
        r"(?:https?://)?github\.com/([^/\s]+/[^/\s]+?)(?:\.git)?/?$",
        user_input, re.IGNORECASE
    )
    if gh_match:
        repo = gh_match.group(1).rstrip("/")
        return repo, f"https://github.com/{repo}"

    # Try as a PyPI package name
    pypi_url = f"https://pypi.org/pypi/{user_input}/json"
    try:
        r = requests.get(pypi_url, timeout=15)
        if r.status_code == 200:
            info = r.json().get("info", {})
            for key in ("project_urls", ):
                urls = info.get(key) or {}
                for label, url in urls.items():
                    if url and "github.com" in url.lower():
                        m = re.search(r"github\.com/([^/\s]+/[^/\s]+?)(?:\.git)?/?$", url)
                        if m:
                            repo = m.group(1).rstrip("/")
                            return repo, f"https://github.com/{repo}"
            # Fall back to home_page
            home = info.get("home_page") or ""
            if "github.com" in home.lower():
                m = re.search(r"github\.com/([^/\s]+/[^/\s]+?)(?:\.git)?/?$", home)
                if m:
                    repo = m.group(1).rstrip("/")
                    return repo, f"https://github.com/{repo}"
    except requests.exceptions.RequestException:
        pass

    raise ValueError(
        f"Could not resolve '{user_input}' to a GitHub repository. "
        "Please enter a GitHub URL (https://github.com/owner/repo) or "
        "a valid PyPI package name."
    )


# =================================================
# Section A — Repo & author metadata
# =================================================

def get_author_public_repos_at_creation(owner: str, repo_created: datetime) -> int:
    count = 0
    for repo_item in paginate(
        f"https://api.github.com/users/{owner}/repos",
        params={"type": "public", "sort": "created", "direction": "asc"}
    ):
        created = parse_datetime(repo_item.get("created_at"))
        if created is None:
            continue
        if created < repo_created:
            count += 1
        else:
            break
    return count


def get_repo_and_author_metadata(repo: str, repo_created: datetime) -> dict:
    six_month_mark = repo_created + relativedelta(months=6)
    six_month_mark_iso = six_month_mark.isoformat().replace("+00:00", "Z")

    meta = {
        "owner_type": "Unknown",
        "is_organization": 0,
        "author_account_age_years": 0.0,
        "author_public_repos_at_creation": 0,
        "has_readme": 0,
        "has_license": 0,
        "has_contributing": 0,
        "has_ci_cd": 0,
        "has_setup_cfg_or_pyproject": 0,
        "has_changelog": 0,
        "has_dockerfile": 0,
        "has_tests_dir": 0,
        "has_docs_dir": 0,
        "has_docs_config": 0,
    }

    r = github_get(f"https://api.github.com/repos/{repo}")
    if r is None or r.status_code != 200:
        return meta

    data = r.json()
    meta["owner_type"] = data.get("owner", {}).get("type", "Unknown")
    meta["is_organization"] = 1 if meta["owner_type"] == "Organization" else 0
    owner_login = data.get("owner", {}).get("login")

    if owner_login:
        u_res = github_get(f"https://api.github.com/users/{owner_login}")
        if u_res and u_res.status_code == 200:
            u = u_res.json()
            if u.get("created_at"):
                user_created = parse_datetime(u["created_at"])
                age_days = (repo_created - user_created).days
                meta["author_account_age_years"] = round(max(0.0, age_days / 365.25), 2)
        meta["author_public_repos_at_creation"] = get_author_public_repos_at_creation(
            owner_login, repo_created
        )

    ref_res = github_get(
        f"https://api.github.com/repos/{repo}/commits",
        params={"until": six_month_mark_iso, "per_page": 1}
    )
    if ref_res is None or ref_res.status_code != 200 or not ref_res.json():
        return meta

    historical_sha = ref_res.json()[0].get("sha")
    if not historical_sha:
        return meta

    c_res = github_get(
        f"https://api.github.com/repos/{repo}/contents/",
        params={"ref": historical_sha}
    )
    if c_res is None or c_res.status_code != 200:
        return meta

    root_entries = c_res.json() if isinstance(c_res.json(), list) else []
    names = [e.get("name", "").lower() for e in root_entries]
    entry_types = {e.get("name", "").lower(): e.get("type") for e in root_entries}

    meta["has_readme"] = 1 if any(n.startswith("readme") for n in names) else 0
    meta["has_license"] = 1 if any(n.startswith(("license", "copying", "copyright")) for n in names) else 0
    meta["has_contributing"] = 1 if any(n.startswith(("contribut", "hacking")) for n in names) else 0
    meta["has_ci_cd"] = 1 if any(n in (".github", ".travis.yml", "circle.yml", ".circleci", "tox.ini", "jenkinsfile")for n in names) else 0
    meta["has_setup_cfg_or_pyproject"] = 1 if any(n in ("setup.py", "setup.cfg", "pyproject.toml") for n in names) else 0
    meta["has_changelog"] = 1 if any(n.startswith(("changelog", "changes", "history", "news", "releases")) for n in names) else 0
    meta["has_dockerfile"] = 1 if "dockerfile" in names else 0
    meta["has_tests_dir"] = 1 if any(n in ("tests", "test") and entry_types.get(n) == "dir" for n in names) else 0
    meta["has_docs_dir"] = 1 if any(n in ("docs", "doc", "documentation") and entry_types.get(n) == "dir"for n in names) else 0
    meta["has_docs_config"] = 1 if any(n in ("mkdocs.yml", "mkdocs.yaml", "_config.yml", "conf.py", "readthedocs.yml", ".readthedocs.yaml")for n in names) else 0

    return meta


# =================================================
# Section B — Commit metrics
# =================================================

def get_commit_metrics(repo: str, start_date: datetime, end_date: datetime) -> dict:
    total_commits = 0
    author_counts = Counter()
    weekly_buckets = set()
    first_commit_date = None
    mid_date = start_date + relativedelta(months=3)
    commits_m1_m3 = 0
    commits_m4_m6 = 0

    since_iso = start_date.isoformat().replace("+00:00", "Z")
    until_iso = end_date.isoformat().replace("+00:00", "Z")

    for commit in paginate(
        f"https://api.github.com/repos/{repo}/commits",
        params={"since": since_iso, "until": until_iso}
    ):
        total_commits += 1
        commit_date = parse_datetime(commit.get("commit", {}).get("author", {}).get("date"))
        if commit_date:
            if first_commit_date is None or commit_date < first_commit_date:
                first_commit_date = commit_date
            weekly_buckets.add(commit_date.strftime("%Y-W%W"))
            if start_date <= commit_date < mid_date:
                commits_m1_m3 += 1
            elif mid_date <= commit_date <= end_date:
                commits_m4_m6 += 1

        gh_author = commit.get("author")
        author_key = (
            gh_author.get("login")
            if gh_author and gh_author.get("login")
            else commit.get("commit", {}).get("author", {}).get("name", "Unknown")
        )
        if author_key and author_key != "Unknown":
            author_counts[author_key] += 1

    unique_contributors = len(author_counts)
    top_author_commits = author_counts.most_common(1)[0][1] if author_counts else 0
    commit_concentration = safe_divide(top_author_commits, total_commits)

    bus_factor = 0
    running_sum = 0
    if total_commits > 0:
        for count in sorted(author_counts.values(), reverse=True):
            running_sum += count
            bus_factor += 1
            if running_sum > total_commits / 2:
                break

    return {
        "commits": total_commits,
        "contributors": unique_contributors,
        "commits_m1_m3": commits_m1_m3,
        "commits_m4_m6": commits_m4_m6,
        "commit_concentration": commit_concentration,
        "bus_factor": bus_factor,
        "active_weeks": len(weekly_buckets),
        "days_to_first_commit": ((first_commit_date - start_date).days if first_commit_date else -1),
    }


# =================================================
# Section C — Issues & PRs
# =================================================

def get_issue_pr_metrics(repo: str, start_date: datetime, end_date: datetime) -> dict:
    issues_opened = issues_closed = prs_opened = prs_closed = 0
    first_issue_date = None
    since_iso = start_date.isoformat().replace("+00:00", "Z")

    for item in paginate(
        f"https://api.github.com/repos/{repo}/issues",
        params={"state": "all", "sort": "created", "direction": "asc", "since": since_iso}
    ):
        created_at = parse_datetime(item.get("created_at"))
        closed_at = parse_datetime(item.get("closed_at"))
        if created_at and created_at > end_date:
            break
        if created_at and created_at < start_date:
            continue
        is_pr = "pull_request" in item
        if is_pr:
            prs_opened += 1
            if closed_at and closed_at <= end_date:
                prs_closed += 1
        else:
            issues_opened += 1
            if closed_at and closed_at <= end_date:
                issues_closed += 1
            if first_issue_date is None and created_at:
                first_issue_date = created_at

    return {
        "issues_opened": issues_opened,
        "issues_closed": issues_closed,
        "prs_opened": prs_opened,
        "prs_closed": prs_closed,
        "days_to_first_issue": ((first_issue_date - start_date).days if first_issue_date else -1),
    }


# =================================================
# Section D — Issue comments
# =================================================

def get_issue_comments(repo: str, start_date: datetime, end_date: datetime) -> int:
    count = 0
    since_iso = start_date.isoformat().replace("+00:00", "Z")
    for comment in paginate(
        f"https://api.github.com/repos/{repo}/issues/comments",
        params={"since": since_iso, "sort": "created", "direction": "asc"}
    ):
        created = parse_datetime(comment.get("created_at"))
        if created and created > end_date:
            break
        if created and start_date <= created <= end_date:
            count += 1
    return count


# =================================================
# Section E — Stars
# =================================================

def get_stars(repo: str, start_date: datetime, end_date: datetime) -> int:
    count = 0
    star_headers = {**HEADERS, "Accept": "application/vnd.github.v3.star+json"}
    for star in paginate(
        f"https://api.github.com/repos/{repo}/stargazers",
        headers_override=star_headers
    ):
        starred_at = parse_datetime(star.get("starred_at"))
        if starred_at is None:
            return count
        if starred_at > end_date:
            break
        if starred_at >= start_date:
            count += 1
    return count


# =================================================
# Section F — Forks
# =================================================

def get_forks(repo: str, start_date: datetime, end_date: datetime) -> int:
    count = 0
    for fork in paginate(
        f"https://api.github.com/repos/{repo}/forks",
        params={"sort": "oldest"}
    ):
        created_at = parse_datetime(fork.get("created_at"))
        if created_at and created_at > end_date:
            break
        if created_at and created_at >= start_date:
            count += 1
    return count


# =================================================
# Section G — Releases
# =================================================

def get_release_count(repo: str, start_date: datetime, end_date: datetime) -> int:
    count = 0
    for release in paginate(f"https://api.github.com/repos/{repo}/releases"):
        published = parse_datetime(release.get("published_at"))
        if published and published > end_date:
            break
        if published and start_date <= published <= end_date:
            count += 1
    return count


# =================================================
# Master extractor
# =================================================

def extract_features(repo: str):
    """
    Given a 'owner/repo' string, fetches all signals and returns:
      {
        "features": { feature_name: value, ... },
        "meta": { display info for the UI },
        "error": None | str
      }
    """
    r = github_get(f"https://api.github.com/repos/{repo}")
    if r is None or r.status_code != 200:
        return {"features": None, "meta": None, "error": f"Repository '{repo}' not found or inaccessible."}

    repo_data = r.json()
    repo_created = parse_datetime(repo_data.get("created_at"))
    if repo_created is None:
        return {"features": None, "meta": None, "error": "Could not determine repository creation date."}

    now = datetime.now(timezone.utc)
    months_old = (now - repo_created).days / 30.44
    if months_old < 6:
        return {
            "features": None,
            "meta": None,
            "error": (
                f"This repository is only {months_old:.1f} months old. "
                "At least 6 months of activity is required for a reliable prediction."
            )
        }

    end_date = repo_created + relativedelta(months=6)

    commit_metrics = get_commit_metrics(repo, repo_created, end_date)
    issue_metrics = get_issue_pr_metrics(repo, repo_created, end_date)
    issue_comments = get_issue_comments(repo, repo_created, end_date)
    stars = get_stars(repo, repo_created, end_date)
    forks = get_forks(repo, repo_created, end_date)
    releases = get_release_count(repo, repo_created, end_date)
    metadata = get_repo_and_author_metadata(repo, repo_created)

    commits = commit_metrics["commits"]
    contributors = commit_metrics["contributors"]
    commits_m1_m3 = commit_metrics["commits_m1_m3"]
    commits_m4_m6 = commit_metrics["commits_m4_m6"]
    issues_opened = issue_metrics["issues_opened"]
    issues_closed = issue_metrics["issues_closed"]
    prs_opened = issue_metrics["prs_opened"]
    prs_closed = issue_metrics["prs_closed"]

    features = {
        "owner_type": metadata["owner_type"],
        "is_organization": metadata["is_organization"],
        "author_account_age_years": metadata["author_account_age_years"],
        "author_public_repos_at_creation": metadata["author_public_repos_at_creation"],
        "has_readme": metadata["has_readme"],
        "has_license": metadata["has_license"],
        "has_contributing": metadata["has_contributing"],
        "has_ci_cd": metadata["has_ci_cd"],
        "has_setup_cfg_or_pyproject": metadata["has_setup_cfg_or_pyproject"],
        "has_changelog": metadata["has_changelog"],
        "has_dockerfile": metadata["has_dockerfile"],
        "has_tests_dir": metadata["has_tests_dir"],
        "has_docs_dir": metadata["has_docs_dir"],
        "has_docs_config": metadata["has_docs_config"],
        "commits": commits,
        "contributors": contributors,
        "commits_m1_m3": commits_m1_m3,
        "commits_m4_m6": commits_m4_m6,
        "commit_concentration": commit_metrics["commit_concentration"],
        "bus_factor": commit_metrics["bus_factor"],
        "active_weeks": commit_metrics["active_weeks"],
        "days_to_first_commit": commit_metrics["days_to_first_commit"],
        "issues_opened": issues_opened,
        "issues_closed": issues_closed,
        "prs_opened": prs_opened,
        "prs_closed": prs_closed,
        "issue_comments": issue_comments,
        "days_to_first_issue": issue_metrics["days_to_first_issue"],
        "stars": stars,
        "forks": forks,
        "releases": releases,
        "commit_momentum": commits_m4_m6 - commits_m1_m3,
        "commit_per_contributor": safe_divide(commits, contributors),
        "issue_resolution_rate": safe_divide(issues_closed + 1, issues_opened + 1),
        "pr_merge_rate": safe_divide(prs_closed + 1, prs_opened + 1),
        "interest_density": safe_divide(stars + forks, commits + 1),
        "comments_per_issue_pr": safe_divide(issue_comments, issues_opened + prs_opened),
        "engagement_score": stars + forks + issue_comments + prs_opened,
        "has_issues": 1 if issues_opened > 0 else 0,
        "has_prs": 1 if prs_opened > 0 else 0,
        "has_releases": 1 if releases > 0 else 0,
        "has_external_contributors": 1 if contributors > 1 else 0,
        "has_community_engagement": 1 if (
            issues_opened > 0 or prs_opened > 0 or
            issue_comments > 0 or forks > 0 or stars > 0
        ) else 0,
        "zero_commit_activity": 1 if commits == 0 else 0,
        "single_contributor_no_engagement": 1 if (
            contributors <= 1 and stars == 0 and
            forks == 0 and issues_opened == 0
        ) else 0,
    }

    display_meta = {
        "repo": repo,
        "repo_url": f"https://github.com/{repo}",
        "full_name": repo_data.get("full_name", repo),
        "description": repo_data.get("description") or "",
        "created_at": repo_data.get("created_at", ""),
        "language": repo_data.get("language") or "Unknown",
        "owner_type": metadata["owner_type"],
        "months_old": round(months_old, 1),
        "observation_window": f"{repo_created.strftime('%b %Y')} — {end_date.strftime('%b %Y')}",
        "structural_flags": {
            "has_readme": metadata["has_readme"],
            "has_license": metadata["has_license"],
            "has_contributing": metadata["has_contributing"],
            "has_ci_cd": metadata["has_ci_cd"],
            "has_setup_cfg_or_pyproject": metadata["has_setup_cfg_or_pyproject"],
            "has_changelog": metadata["has_changelog"],
            "has_dockerfile": metadata["has_dockerfile"],
            "has_tests_dir": metadata["has_tests_dir"],
            "has_docs_dir": metadata["has_docs_dir"],
            "has_docs_config": metadata["has_docs_config"],
        },
        "key_metrics": {
            "commits": commits,
            "contributors": contributors,
            "stars": stars,
            "forks": forks,
            "releases": releases,
            "active_weeks": commit_metrics["active_weeks"],
            "issues_opened": issues_opened,
            "prs_opened": prs_opened,
        },
    }

    return {"features": features, "meta": display_meta, "error": None}
