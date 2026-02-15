import argparse
import os
import sys
import webbrowser
from .analyzer import GitAnalyzer
from .renderer import DashboardRenderer

def main():
    parser = argparse.ArgumentParser(
        description="Commit Pulse - Premium Git Repository Analytics Dashboard"
    )
    
    parser.add_argument(
        'path', 
        nargs='?', 
        default='.', 
        help="Path to the repository (default is current directory)"
    )
    
    parser.add_argument(
        '--scan', 
        action='store_true', 
        help="Scan the current directory (and subdirectories) for all git repositories"
    )
    
    parser.add_argument(
        '--no-open', 
        action='store_true', 
        help="Do not automatically open the dashboard in the browser"
    )
    
    parser.add_argument(
        '--local', 
        action='store_true', 
        help="Generate a static HTML dashboard locally"
    )

    # Maintain --publish for backward compatibility, but it's now the default
    parser.add_argument(
        '--publish', 
        action='store_true', 
        help=argparse.SUPPRESS
    )

    args = parser.parse_args()
    
    # Cloud-first strategy: if no --local is specified, we intend to publish.
    # However, if explicitly requested --local, we must confirm.
    if args.local:
        confirm = input("\n💡 This will generate a static HTML dashboard locally. Do you wish to proceed? (y/n): ").lower()
        if confirm != 'y':
            print("Operation cancelled.")
            sys.exit(0)

    all_stats = []
    
    if args.scan:
        print(f"Scanning for git repositories in {os.path.abspath(args.path)}...")
        repo_paths = GitAnalyzer.scan_for_repos(args.path)
        print(f"Found {len(repo_paths)} repositories.")
        
        for p in repo_paths:
            analyzer = GitAnalyzer(p)
            stats = analyzer.get_stats()
            if stats:
                all_stats.append(stats)
    else:
        analyzer = GitAnalyzer(args.path)
        if not analyzer.is_git_repo():
            print(f"Error: {os.path.abspath(args.path)} is not a git repository.")
            print("💡 Tip: Use '--scan' to find and analyze all git repositories in this folder.")
            sys.exit(1)
            
        stats = analyzer.get_stats()
        if stats:
            all_stats.append(stats)

    if not all_stats:
        print("Note: No statistics could be gathered.")
        sys.exit(0)

    # Default to publishing unless --local is explicitly requested
    is_publishing = not args.local

    # Render local dashboard if requested
    output_path = None
    if args.local:
        renderer = DashboardRenderer(all_stats)
        output_path = renderer.render()
        
        print(f"\nDashboard generated successfully!")
        print(f"Location: {output_path}")
        
        if not args.no_open:
            webbrowser.open(f"file://{output_path}")

    # Cloud Publishing (Default Behavior)
    if is_publishing:
        import requests
        # Get username from git config
        username = GitAnalyzer.get_git_config_user() or os.getenv("USER") or "Anonymous"
        
        print(f"\n🚀 Synchronizing Pulse to Global Registry as '{username}'...")
        
        # Production Cloud URL
        cloud_url = os.getenv("COMMITPULSE_CLOUD_URL", "https://commitpulse.pxxl.click") 
        api_endpoint = f"{cloud_url}/api/publish"
        
        try:
            # For now we publish the first repo in all_stats if multiple found in scan
            # In a better version we'd handle multi-repo publishing
            repo_to_publish = all_stats[0]
            
            payload = {
                "username": username,
                "repoName": repo_to_publish["name"],
                "stats": all_stats 
            }
            
            response = requests.post(api_endpoint, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                published_url = result['url']
                print(f"✨ Successfully published! Share your Pulse at: {published_url}")
                
                # Automatically open cloud link if not suppressed
                if not args.no_open:
                    print(f"🌍 Opening your cloud dashboard...")
                    webbrowser.open(published_url)
            else:
                print(f"❌ Failed to publish: {response.text}")
        except Exception as e:
            print(f"⚠️ Cloud sync failed: {str(e)}")
            print("💡 Trying to generate a local fallback...")
            renderer = DashboardRenderer(all_stats)
            output_path = renderer.render()
            print(f"Fallback dashboard: {output_path}")
            if not args.no_open:
                webbrowser.open(f"file://{output_path}")

if __name__ == "__main__":
    main()
