import subprocess
import os
import hashlib
import json
import urllib.request
import urllib.parse
from collections import Counter
from datetime import datetime

class GitAnalyzer:
    def __init__(self, repo_path):
        self.repo_path = os.path.abspath(repo_path)
        self.repo_name = os.path.basename(self.repo_path)
        self.github_avatar_cache = {}

    def _run_git(self, args):
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
                shell=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def is_git_repo(self):
        return os.path.exists(os.path.join(self.repo_path, '.git'))

    def _get_github_avatar(self, email):
        if email in self.github_avatar_cache:
            return self.github_avatar_cache[email]
        
        # Default to Gravatar
        email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
        avatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=150"
        
        try:
            # Try to search for user by email using GitHub's public API
            search_url = f"https://api.github.com/search/users?q={urllib.parse.quote(email)}"
            request = urllib.request.Request(search_url)
            request.add_header('User-Agent', 'CommitPulse-CLI-v0.1')
            
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get('total_count', 0) > 0:
                    avatar_url = data['items'][0]['avatar_url']
        except Exception:
            # Silently fall back to Gravatar on any error (rate limit, network, etc)
            pass
            
        self.github_avatar_cache[email] = avatar_url
        return avatar_url

    def get_stats(self):
        if not self.is_git_repo():
            return None

        print(f"Analyzing {self.repo_name}... (High Precision)")

        # Get all commit dates and times for heatmap and productivity
        # Use --all to include all branches and --no-merges to match GitHub's default contribution view
        # or remove --no-merges if we want every single commit. GitHub counts merges if they occurred on GitHub.
        # We'll stick to --all for full visibility.
        commit_dates_raw = self._run_git(['log', '--all', '--format=%aI'])
        
        heatmap_data = Counter()
        hourly_distribution = Counter()
        
        if commit_dates_raw:
            dates = commit_dates_raw.split('\n')
            for d in dates:
                if not d: continue
                try:
                    dt = datetime.fromisoformat(d)
                    date_str = dt.date().isoformat()
                    hour = dt.hour
                    
                    heatmap_data[date_str] += 1
                    hourly_distribution[hour] += 1
                except ValueError:
                    continue

        total_commits = sum(heatmap_data.values())

        # Get first and last commit dates
        first_date = "N/A"
        last_date = "N/A"
        if heatmap_data:
            sorted_dates = sorted(heatmap_data.keys())
            first_date = sorted_dates[0]
            last_date = sorted_dates[-1]

        # Get contributors with high precision
        # Format: count <tab> name <email>
        shortlog = self._run_git(['shortlog', '-sne', '--all'])
        contributors = []
        if shortlog:
            for line in shortlog.split('\n'):
                line = line.strip()
                if not line: continue
                parts = line.split('\t')
                if len(parts) == 2:
                    count = int(parts[0].strip())
                    name_email = parts[1].strip()
                    name = name_email
                    email = ""
                    if '<' in name_email:
                        name = name_email.split('<')[0].strip()
                        email = name_email.split('<')[1].split('>')[0].strip()
                    
                    avatar = self._get_github_avatar(email)
                    
                    contributors.append({
                        "name": name,
                        "email": email,
                        "commits": count,
                        "avatar": avatar
                    })

        # Get code churn (Lines added/deleted)
        # git log --shortstat --all: "N files changed, X insertions(+), Y deletions(-)"
        lines_added = 0
        lines_deleted = 0
        shortstat_raw = self._run_git(['log', '--all', '--shortstat', '--format='])
        if shortstat_raw:
            for line in shortstat_raw.split('\n'):
                line = line.strip()
                if not line: continue
                
                # Format: "X insertions(+), Y deletions(-)"
                if "insertions(+)" in line:
                    try:
                        pts = line.split(',')
                        for p in pts:
                            if "insertion" in p:
                                lines_added += int(p.strip().split(' ')[0])
                            if "deletion" in p:
                                lines_deleted += int(p.strip().split(' ')[0])
                    except: pass

        # Language Detection (Robust Byte-Count Analysis)
        languages = Counter()
        
        # Comprehensive language map (Extensions -> Language Name)
        # Sourced from industry standards for polyglot analysis
        LANG_MAP = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.tsx': 'React/TS', 
            '.jsx': 'React/JS', '.html': 'HTML', '.css': 'CSS', '.go': 'Go', '.rs': 'Rust',
            '.cpp': 'C++', '.c': 'C', '.h': 'C/C++', '.java': 'Java', '.rb': 'Ruby', 
            '.php': 'PHP', '.cs': 'C#', '.swift': 'Swift', '.kt': 'Kotlin', '.m': 'Obj-C',
            '.sql': 'SQL', '.sh': 'Shell', '.bat': 'Batch', '.ps1': 'PowerShell',
            '.dart': 'Dart', '.lua': 'Lua', '.scala': 'Scala', '.pl': 'Perl',
            '.r': 'R', '.jl': 'Julia', '.ex': 'Elixir', '.exs': 'Elixir',
            '.yaml': 'YAML', '.yml': 'YAML', '.json': 'JSON', '.md': 'Markdown',
            '.dockerfile': 'Docker', 'dockerfile': 'Docker', '.proto': 'Protobuf'
        }

        # Directories and files to strictly ignore
        IGNORE_DIRS = {
            '.git', 'node_modules', 'venv', '.venv', 'env', '__pycache__', 
            'build', 'dist', 'target', '.next', 'out', '.svelte-kit',
            'vendor', 'bin', 'obj', '.vs', '.idea', '.vscode'
        }
        
        IGNORE_FILES = {
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'composer.lock',
            'poetry.lock', 'gemfile.lock', 'cargo.lock', 'mix.lock'
        }

        # Scan files using byte-count for precision
        for root, dirs, files in os.walk(self.repo_path):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for f in files:
                if f in IGNORE_FILES:
                    continue
                    
                full_path = os.path.join(root, f)
                ext = os.path.splitext(f)[1].lower()
                
                # Check extension or direct filename (like Dockerfile)
                lang = LANG_MAP.get(ext) or LANG_MAP.get(f.lower())
                
                if lang:
                    try:
                        # Weight by byte-count to mirror GitHub's Linguist accuracy
                        size = os.path.getsize(full_path)
                        languages[lang] += size
                    except (OSError, PermissionError):
                        # Fallback to simple increment if size can't be read
                        languages[lang] += 1

        top_languages = [lang for lang, count in languages.most_common(5)]

        # Estimate Engineering Hours
        # Heuristic: Clustered sessions. Commits < 2hrs apart = same session.
        estimated_hours = 0
        if commit_dates_raw:
            # Sort full ISO timestamps
            all_timestamps = []
            for d in commit_dates_raw.split('\n'):
                if not d: continue
                try:
                    all_timestamps.append(datetime.fromisoformat(d))
                except: pass
            
            all_timestamps.sort()
            
            if all_timestamps:
                session_start_buffer = 0.5 # 30 mins session prep
                estimated_hours += session_start_buffer
                
                for i in range(1, len(all_timestamps)):
                    diff = (all_timestamps[i] - all_timestamps[i-1]).total_seconds() / 3600
                    if diff < 2: # Within 2 hours
                        estimated_hours += diff
                    else:
                        estimated_hours += session_start_buffer
        
        # Calculate most productive hour
        peak_hour = "N/A"
        if hourly_distribution:
            peak_hour = f"{hourly_distribution.most_common(1)[0][0]}:00"

        # Calculate segments
        activity_segments = {
            "Early Bird": 0, # 0-6
            "Morning": 0,    # 6-12
            "Afternoon": 0,  # 12-18
            "Late Night": 0   # 18-24
        }
        for hour, count in hourly_distribution.items():
            if 0 <= hour < 6: activity_segments["Early Bird"] += count
            elif 6 <= hour < 12: activity_segments["Morning"] += count
            elif 12 <= hour < 18: activity_segments["Afternoon"] += count
            else: activity_segments["Late Night"] += count

        return {
            "name": self.repo_name,
            "path": self.repo_path,
            "total_commits": total_commits,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "estimated_hours": round(estimated_hours, 1),
            "first_commit": first_date,
            "last_commit": last_date,
            "peak_hour": peak_hour,
            "top_languages": top_languages,
            "heatmap": dict(heatmap_data),
            "activity_pulse": activity_segments,
            "hourly_distribution": dict(hourly_distribution),
            "contributors": sorted(contributors, key=lambda x: x['commits'], reverse=True)
        }

    @staticmethod
    def scan_for_repos(root_dir, max_depth=3):
        repos = []
        root_dir = os.path.abspath(root_dir)
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            if '.git' in dirnames:
                repos.append(dirpath)
                dirnames.remove('.git')
            
            depth = dirpath.replace(root_dir, '').count(os.sep)
            if depth >= max_depth:
                del dirnames[:]
                
        return repos
    @staticmethod
    def get_git_config_user():
        try:
            import subprocess
            name = subprocess.check_output(["git", "config", "user.name"]).decode().strip()
            return name
        except:
            return None
