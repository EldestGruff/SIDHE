import click
import json
import sys
from typing import Dict, Any
from .plugin_interface import QuestTracker
from .quest_parser import QuestParser

@click.group()
def cli():
    """SIDHE GitHub Integration CLI"""
    pass

@cli.command()
@click.option('--state', default='open', help='Quest state: open, closed, all')
@click.option('--format', 'output_format', default='table', help='Output format: table, json')
def list_quests(state, output_format):
    """List all Quests"""
    try:
        manager = QuestTracker()
        missions = manager.get_away_quests(state)
        
        if output_format == 'json':
            click.echo(json.dumps(missions, indent=2))
        else:
            if not missions:
                click.echo(f"No quests found in state: {state}")
                return
            
            click.echo(f"\n🚀 Quests ({state.upper()})")
            click.echo("=" * 50)
            
            for quest in missions:
                click.echo(f"\n#{quest['number']}: {quest['title']}")
                click.echo(f"  Quest ID: {quest['quest_id']}")
                click.echo(f"  Status: {quest['state']}")
                click.echo(f"  Priority: {quest['classification']}")
                click.echo(f"  Type: {quest['quest_type']}")
                click.echo(f"  URL: {quest['url']}")
                
                if quest['objectives']:
                    click.echo("  Objectives:")
                    for obj in quest['objectives']:
                        marker = "🎯" if obj['is_primary'] else "  •"
                        click.echo(f"    {marker} {obj['description']}")
                
                if quest['acceptance_criteria']:
                    pending = sum(1 for ac in quest['acceptance_criteria'] if not ac['is_complete'])
                    total = len(quest['acceptance_criteria'])
                    click.echo(f"  Acceptance Criteria: {total - pending}/{total} complete")
                
                click.echo()
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('quest_number', type=int)
@click.option('--format', 'output_format', default='detailed', help='Output format: detailed, json')
def show_quest(quest_number, output_format):
    """Show detailed quest information"""
    try:
        manager = QuestTracker()
        quest = manager.get_quest_details(quest_number)
        
        if output_format == 'json':
            click.echo(json.dumps(quest, indent=2))
        else:
            _print_quest_details(quest)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('quest_number', type=int)
def start_quest(quest_number):
    """Start working on a quest (create branch, update status)"""
    try:
        manager = QuestTracker()
        
        # Get quest details
        quest = manager.get_quest_details(quest_number)
        
        click.echo(f"Starting quest #{quest_number}: {quest['title']}")
        
        # Create feature branch
        branch_name = manager.create_feature_branch(
            quest_number, 
            quest['title']
        )
        
        # Update quest status
        manager.update_quest_progress(
            quest_number,
            "in-progress",
            f"Apprentice has begun implementation on branch `{branch_name}`"
        )
        
        click.echo(f"✅ Quest #{quest_number} started on branch: {branch_name}")
        click.echo(f"🔗 Quest URL: {quest['url']}")
        click.echo(f"\nNext steps:")
        click.echo(f"1. git checkout {branch_name}")
        click.echo(f"2. Implement the quest objectives")
        click.echo(f"3. Run: sidhe-github complete-quest {quest_number}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('quest_number', type=int)
@click.option('--summary', prompt='Changes summary', help='Summary of changes made')
def complete_quest(quest_number, summary):
    """Complete a quest (create PR, update status)"""
    try:
        manager = QuestTracker()
        
        # Get quest details
        quest = manager.get_quest_details(quest_number)
        
        click.echo(f"Completing quest #{quest_number}: {quest['title']}")
        
        # Determine branch name
        branch_name = f"quest-{quest_number}-{quest['title'][:30].replace(' ', '-').lower()}"
        
        # Create PR
        pr_number = manager.create_pull_request(
            quest_number,
            branch_name,
            summary
        )
        
        # Update quest status
        manager.update_quest_progress(
            quest_number,
            "complete",
            f"Quest completed. Pull request #{pr_number} created for review."
        )
        
        click.echo(f"✅ Quest #{quest_number} completed!")
        click.echo(f"📋 Pull Request #{pr_number} created")
        click.echo(f"🔗 Quest URL: {quest['url']}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('quest_number', type=int)
@click.argument('status')
@click.option('--details', default='', help='Additional details about the status update')
def update_status(quest_number, status, details):
    """Update quest status"""
    try:
        manager = QuestTracker()
        
        success = manager.update_quest_progress(quest_number, status, details)
        
        if success:
            click.echo(f"✅ Quest #{quest_number} status updated to: {status}")
        else:
            click.echo(f"❌ Failed to update quest #{quest_number} status")
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('spec_path')
def get_spec(spec_path):
    """Get specification file content"""
    try:
        manager = QuestTracker()
        content = manager.get_specification(spec_path)
        click.echo(content)
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
def test_connection():
    """Test GitHub connection and authentication"""
    try:
        manager = QuestTracker()
        click.echo("✅ GitHub connection successful!")
        click.echo(f"Repository: {manager.repo_name}")
        click.echo(f"API Rate Limit: {manager.github.get_rate_limit().core.remaining}")
    
    except Exception as e:
        click.echo(f"❌ Connection failed: {e}", err=True)
        sys.exit(1)

def _print_quest_details(quest: Dict[str, Any]):
    """Print detailed quest information in a formatted way"""
    click.echo(f"\n🚀 Quest #{quest['number']}: {quest['title']}")
    click.echo("=" * 60)
    
    # Basic info
    click.echo(f"Quest ID: {quest['quest_id']}")
    click.echo(f"Classification: {quest['classification']}")
    click.echo(f"Type: {quest['quest_type']}")
    click.echo(f"Status: {quest['state']}")
    click.echo(f"URL: {quest['url']}")
    click.echo(f"Created: {quest['created_at']}")
    click.echo(f"Updated: {quest['updated_at']}")
    
    # Objectives
    if quest['objectives']:
        click.echo(f"\n🎯 Quest Objectives:")
        for obj in quest['objectives']:
            marker = "🎯 PRIMARY" if obj['is_primary'] else "  • Secondary"
            click.echo(f"  {marker}: {obj['description']}")
            
            if obj.get('sub_objectives'):
                for sub_obj in obj['sub_objectives']:
                    click.echo(f"    - {sub_obj}")
    
    # Technical Specs
    if quest['technical_specs']:
        click.echo(f"\n🔧 Technical Specifications:")
        for key, value in quest['technical_specs'].items():
            click.echo(f"  {key}: {value}")
    
    # Acceptance Criteria
    if quest['acceptance_criteria']:
        click.echo(f"\n📋 Acceptance Criteria:")
        for ac in quest['acceptance_criteria']:
            status = "✅" if ac['is_complete'] else "❌"
            click.echo(f"  {status} {ac['description']}")
    
    # Referenced Docs
    if quest['referenced_docs']:
        click.echo(f"\n📄 Referenced Documentation:")
        for doc in quest['referenced_docs']:
            click.echo(f"  • {doc}")
    
    # Archmage's Notes
    if quest.get('captains_notes'):
        click.echo(f"\n👨‍✈️ Archmage's Notes:")
        click.echo(f"  {quest['captains_notes']}")
    
    click.echo()

if __name__ == '__main__':
    cli()