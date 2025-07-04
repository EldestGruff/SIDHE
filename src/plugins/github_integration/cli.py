import click
import json
import sys
from typing import Dict, Any
from .plugin_interface import GitHubManager
from .mission_parser import MissionParser

@click.group()
def cli():
    """Riker GitHub Integration CLI"""
    pass

@cli.command()
@click.option('--state', default='open', help='Mission state: open, closed, all')
@click.option('--format', 'output_format', default='table', help='Output format: table, json')
def list_missions(state, output_format):
    """List all Away Missions"""
    try:
        manager = GitHubManager()
        missions = manager.get_away_missions(state)
        
        if output_format == 'json':
            click.echo(json.dumps(missions, indent=2))
        else:
            if not missions:
                click.echo(f"No away missions found in state: {state}")
                return
            
            click.echo(f"\n🚀 Away Missions ({state.upper()})")
            click.echo("=" * 50)
            
            for mission in missions:
                click.echo(f"\n#{mission['number']}: {mission['title']}")
                click.echo(f"  Mission ID: {mission['mission_id']}")
                click.echo(f"  Status: {mission['state']}")
                click.echo(f"  Priority: {mission['classification']}")
                click.echo(f"  Type: {mission['mission_type']}")
                click.echo(f"  URL: {mission['url']}")
                
                if mission['objectives']:
                    click.echo("  Objectives:")
                    for obj in mission['objectives']:
                        marker = "🎯" if obj['is_primary'] else "  •"
                        click.echo(f"    {marker} {obj['description']}")
                
                if mission['acceptance_criteria']:
                    pending = sum(1 for ac in mission['acceptance_criteria'] if not ac['is_complete'])
                    total = len(mission['acceptance_criteria'])
                    click.echo(f"  Acceptance Criteria: {total - pending}/{total} complete")
                
                click.echo()
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('mission_number', type=int)
@click.option('--format', 'output_format', default='detailed', help='Output format: detailed, json')
def show_mission(mission_number, output_format):
    """Show detailed mission information"""
    try:
        manager = GitHubManager()
        mission = manager.get_mission_details(mission_number)
        
        if output_format == 'json':
            click.echo(json.dumps(mission, indent=2))
        else:
            _print_mission_details(mission)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('mission_number', type=int)
def start_mission(mission_number):
    """Start working on a mission (create branch, update status)"""
    try:
        manager = GitHubManager()
        
        # Get mission details
        mission = manager.get_mission_details(mission_number)
        
        click.echo(f"Starting mission #{mission_number}: {mission['title']}")
        
        # Create feature branch
        branch_name = manager.create_feature_branch(
            mission_number, 
            mission['title']
        )
        
        # Update mission status
        manager.update_mission_progress(
            mission_number,
            "in-progress",
            f"Number One has begun implementation on branch `{branch_name}`"
        )
        
        click.echo(f"✅ Mission #{mission_number} started on branch: {branch_name}")
        click.echo(f"🔗 Mission URL: {mission['url']}")
        click.echo(f"\nNext steps:")
        click.echo(f"1. git checkout {branch_name}")
        click.echo(f"2. Implement the mission objectives")
        click.echo(f"3. Run: riker-github complete-mission {mission_number}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('mission_number', type=int)
@click.option('--summary', prompt='Changes summary', help='Summary of changes made')
def complete_mission(mission_number, summary):
    """Complete a mission (create PR, update status)"""
    try:
        manager = GitHubManager()
        
        # Get mission details
        mission = manager.get_mission_details(mission_number)
        
        click.echo(f"Completing mission #{mission_number}: {mission['title']}")
        
        # Determine branch name
        branch_name = f"away-mission-{mission_number}-{mission['title'][:30].replace(' ', '-').lower()}"
        
        # Create PR
        pr_number = manager.create_pull_request(
            mission_number,
            branch_name,
            summary
        )
        
        # Update mission status
        manager.update_mission_progress(
            mission_number,
            "complete",
            f"Mission completed. Pull request #{pr_number} created for review."
        )
        
        click.echo(f"✅ Mission #{mission_number} completed!")
        click.echo(f"📋 Pull Request #{pr_number} created")
        click.echo(f"🔗 Mission URL: {mission['url']}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('mission_number', type=int)
@click.argument('status')
@click.option('--details', default='', help='Additional details about the status update')
def update_status(mission_number, status, details):
    """Update mission status"""
    try:
        manager = GitHubManager()
        
        success = manager.update_mission_progress(mission_number, status, details)
        
        if success:
            click.echo(f"✅ Mission #{mission_number} status updated to: {status}")
        else:
            click.echo(f"❌ Failed to update mission #{mission_number} status")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('spec_path')
def get_spec(spec_path):
    """Get specification file content"""
    try:
        manager = GitHubManager()
        content = manager.get_specification(spec_path)
        click.echo(content)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
def test_connection():
    """Test GitHub connection and authentication"""
    try:
        manager = GitHubManager()
        click.echo("✅ GitHub connection successful!")
        click.echo(f"Repository: {manager.repo_name}")
        click.echo(f"API Rate Limit: {manager.github.get_rate_limit().core.remaining}")
    
    except Exception as e:
        click.echo(f"❌ Connection failed: {e}", err=True)
        sys.exit(1)

def _print_mission_details(mission: Dict[str, Any]):
    """Print detailed mission information in a formatted way"""
    click.echo(f"\n🚀 Mission #{mission['number']}: {mission['title']}")
    click.echo("=" * 60)
    
    # Basic info
    click.echo(f"Mission ID: {mission['mission_id']}")
    click.echo(f"Classification: {mission['classification']}")
    click.echo(f"Type: {mission['mission_type']}")
    click.echo(f"Status: {mission['state']}")
    click.echo(f"URL: {mission['url']}")
    click.echo(f"Created: {mission['created_at']}")
    click.echo(f"Updated: {mission['updated_at']}")
    
    # Objectives
    if mission['objectives']:
        click.echo(f"\n🎯 Mission Objectives:")
        for obj in mission['objectives']:
            marker = "🎯 PRIMARY" if obj['is_primary'] else "  • Secondary"
            click.echo(f"  {marker}: {obj['description']}")
            
            if obj.get('sub_objectives'):
                for sub_obj in obj['sub_objectives']:
                    click.echo(f"    - {sub_obj}")
    
    # Technical Specs
    if mission['technical_specs']:
        click.echo(f"\n🔧 Technical Specifications:")
        for key, value in mission['technical_specs'].items():
            click.echo(f"  {key}: {value}")
    
    # Acceptance Criteria
    if mission['acceptance_criteria']:
        click.echo(f"\n📋 Acceptance Criteria:")
        for ac in mission['acceptance_criteria']:
            status = "✅" if ac['is_complete'] else "❌"
            click.echo(f"  {status} {ac['description']}")
    
    # Referenced Docs
    if mission['referenced_docs']:
        click.echo(f"\n📄 Referenced Documentation:")
        for doc in mission['referenced_docs']:
            click.echo(f"  • {doc}")
    
    # Captain's Notes
    if mission.get('captains_notes'):
        click.echo(f"\n👨‍✈️ Captain's Notes:")
        click.echo(f"  {mission['captains_notes']}")
    
    click.echo()

if __name__ == '__main__':
    cli()