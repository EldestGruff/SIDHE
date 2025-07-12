import click
import json
import yaml
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .plugin_interface import WorkflowGenerator, WorkflowStatus
from .templates.library import TemplateLibrary
from .storage.redis_store import RedisWorkflowStore

@click.group()
def cli():
    """SIDHE Workflow Generator CLI"""
    pass

@cli.command()
@click.argument('description')
@click.option('--context', type=str, help='Optional context as JSON string')
@click.option('--output', '-o', type=str, help='Output file path for generated workflow')
@click.option('--format', 'output_format', default='yaml', help='Output format: yaml, json')
@click.option('--dry-run', is_flag=True, help='Generate workflow without saving')
def generate(description, context, output, output_format, dry_run):
    """Generate a workflow from natural language description"""
    try:
        # Parse context if provided
        context_dict = None
        if context:
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                click.echo(f"Error: Invalid JSON in context parameter", err=True)
                sys.exit(1)
        
        # Initialize generator
        generator = WorkflowGenerator()
        
        # Generate workflow
        click.echo(f"Generating workflow from: {description}")
        workflow = generator.generate_from_text(description, context_dict)
        
        # Format output
        if output_format == 'json':
            workflow_content = json.dumps(workflow.to_dict(), indent=2)
        else:
            workflow_content = yaml.dump(workflow.to_dict(), default_flow_style=False, indent=2)
        
        # Save or display
        if output and not dry_run:
            Path(output).write_text(workflow_content, encoding='utf-8')
            click.echo(f"✅ Workflow saved to: {output}")
        else:
            click.echo("\n" + "=" * 50)
            click.echo("GENERATED WORKFLOW")
            click.echo("=" * 50)
            click.echo(workflow_content)
        
        # Save to Redis if not dry run
        if not dry_run:
            workflow_id = generator.save_workflow(workflow)
            if workflow_id:
                click.echo(f"✅ Workflow saved to Redis with ID: {workflow_id}")
            else:
                click.echo("⚠️  Warning: Could not save workflow to Redis")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('workflow_file')
@click.option('--inputs', type=str, help='Workflow inputs as JSON string')
@click.option('--inputs-file', type=str, help='Path to JSON file containing inputs')
@click.option('--dry-run', is_flag=True, help='Simulate execution without running commands')
@click.option('--output', '-o', type=str, help='Output file for execution results')
def execute(workflow_file, inputs, inputs_file, dry_run, output):
    """Execute a workflow from file"""
    try:
        # Load workflow
        if not os.path.exists(workflow_file):
            click.echo(f"Error: Workflow file not found: {workflow_file}", err=True)
            sys.exit(1)
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            if workflow_file.endswith('.json'):
                workflow_dict = json.load(f)
            else:
                workflow_dict = yaml.safe_load(f)
        
        # Parse inputs
        inputs_dict = {}
        if inputs:
            try:
                inputs_dict = json.loads(inputs)
            except json.JSONDecodeError:
                click.echo(f"Error: Invalid JSON in inputs parameter", err=True)
                sys.exit(1)
        elif inputs_file:
            if not os.path.exists(inputs_file):
                click.echo(f"Error: Inputs file not found: {inputs_file}", err=True)
                sys.exit(1)
            with open(inputs_file, 'r', encoding='utf-8') as f:
                inputs_dict = json.load(f)
        
        # Initialize generator and execute
        generator = WorkflowGenerator()
        workflow = generator._dict_to_workflow(workflow_dict)
        
        click.echo(f"Executing workflow: {workflow.name} v{workflow.version}")
        if dry_run:
            click.echo("🔍 DRY RUN MODE - No commands will be executed")
        
        result = generator.execute_workflow(workflow, inputs_dict, dry_run)
        
        # Display results
        _display_execution_result(result)
        
        # Save results if requested
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=str)
            click.echo(f"✅ Results saved to: {output}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('workflow_name')
@click.option('--version', type=str, help='Specific version (latest if not specified)')
@click.option('--inputs', type=str, help='Workflow inputs as JSON string')
@click.option('--inputs-file', type=str, help='Path to JSON file containing inputs')
@click.option('--dry-run', is_flag=True, help='Simulate execution without running commands')
def run(workflow_name, version, inputs, inputs_file, dry_run):
    """Execute a workflow from Redis storage"""
    try:
        # Parse inputs
        inputs_dict = {}
        if inputs:
            try:
                inputs_dict = json.loads(inputs)
            except json.JSONDecodeError:
                click.echo(f"Error: Invalid JSON in inputs parameter", err=True)
                sys.exit(1)
        elif inputs_file:
            if not os.path.exists(inputs_file):
                click.echo(f"Error: Inputs file not found: {inputs_file}", err=True)
                sys.exit(1)
            with open(inputs_file, 'r', encoding='utf-8') as f:
                inputs_dict = json.load(f)
        
        # Initialize generator and load workflow
        generator = WorkflowGenerator()
        workflow = generator.load_workflow(f"workflow:{workflow_name}:{version or 'latest'}")
        
        if not workflow:
            click.echo(f"Error: Workflow not found: {workflow_name}", err=True)
            sys.exit(1)
        
        click.echo(f"Executing workflow: {workflow.name} v{workflow.version}")
        if dry_run:
            click.echo("🔍 DRY RUN MODE - No commands will be executed")
        
        result = generator.execute_workflow(workflow, inputs_dict, dry_run)
        
        # Display results
        _display_execution_result(result)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('workflow_file')
def validate(workflow_file):
    """Validate a workflow file"""
    try:
        # Load workflow
        if not os.path.exists(workflow_file):
            click.echo(f"Error: Workflow file not found: {workflow_file}", err=True)
            sys.exit(1)
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            if workflow_file.endswith('.json'):
                workflow_dict = json.load(f)
            else:
                workflow_dict = yaml.safe_load(f)
        
        # Initialize generator and validate
        generator = WorkflowGenerator()
        workflow = generator._dict_to_workflow(workflow_dict)
        
        validation_result = generator.validator.validate(workflow)
        
        if validation_result.is_valid:
            click.echo("✅ Workflow validation passed!")
            click.echo(f"Workflow: {workflow.name} v{workflow.version}")
            click.echo(f"Steps: {len(workflow.steps)}")
            click.echo(f"Inputs: {len(workflow.inputs)}")
            
            if validation_result.warnings:
                click.echo("\n⚠️  Warnings:")
                for warning in validation_result.warnings:
                    click.echo(f"  • {warning}")
        else:
            click.echo("❌ Workflow validation failed!")
            click.echo("\nErrors:")
            for error in validation_result.errors:
                click.echo(f"  • {error}")
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--format', 'output_format', default='table', help='Output format: table, json')
@click.option('--limit', type=int, default=20, help='Maximum number of workflows to list')
def list_workflows(output_format, limit):
    """List all available workflows"""
    try:
        generator = WorkflowGenerator()
        workflows = generator.list_workflows()
        
        if output_format == 'json':
            click.echo(json.dumps(workflows, indent=2))
        else:
            if not workflows:
                click.echo("No workflows found")
                return
            
            click.echo(f"\n🔧 Available Workflows ({len(workflows)} total)")
            click.echo("=" * 60)
            
            for workflow in workflows[:limit]:
                click.echo(f"\n📋 {workflow['name']} v{workflow['version']}")
                click.echo(f"   Description: {workflow['description']}")
                click.echo(f"   Status: {workflow['status']}")
                click.echo(f"   Created: {workflow['created_at']}")
                click.echo(f"   Updated: {workflow['updated_at']}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--format', 'output_format', default='table', help='Output format: table, json')
@click.option('--limit', type=int, default=20, help='Maximum number of templates to list')
def list_templates(output_format, limit):
    """List all available workflow templates"""
    try:
        template_library = TemplateLibrary()
        templates = template_library.list_templates()
        
        if output_format == 'json':
            templates_data = [template.to_dict() for template in templates]
            click.echo(json.dumps(templates_data, indent=2))
        else:
            if not templates:
                click.echo("No templates found")
                return
            
            click.echo(f"\n📚 Available Templates ({len(templates)} total)")
            click.echo("=" * 60)
            
            for template in templates[:limit]:
                click.echo(f"\n📄 {template.name}")
                click.echo(f"   Description: {template.description}")
                click.echo(f"   Keywords: {', '.join(template.keywords)}")
                click.echo(f"   Usage Count: {template.usage_count}")
                click.echo(f"   Rating: {template.rating:.1f}/5.0")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('template_name')
@click.option('--output', '-o', type=str, help='Output file for template')
@click.option('--format', 'output_format', default='yaml', help='Output format: yaml, json')
def get_template(template_name, output, output_format):
    """Get a specific template by name"""
    try:
        template_library = TemplateLibrary()
        template = template_library.get_template(template_name)
        
        if not template:
            click.echo(f"Error: Template not found: {template_name}", err=True)
            sys.exit(1)
        
        # Format output
        if output_format == 'json':
            template_content = json.dumps(template.to_dict(), indent=2)
        else:
            template_content = yaml.dump(template.to_dict(), default_flow_style=False, indent=2)
        
        # Save or display
        if output:
            Path(output).write_text(template_content, encoding='utf-8')
            click.echo(f"✅ Template saved to: {output}")
        else:
            click.echo(f"\n📄 Template: {template.name}")
            click.echo("=" * 50)
            click.echo(template_content)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('workflow_name')
@click.option('--version', type=str, help='Specific version (latest if not specified)')
@click.option('--limit', type=int, default=10, help='Maximum number of executions to show')
@click.option('--format', 'output_format', default='table', help='Output format: table, json')
def list_executions(workflow_name, version, limit, output_format):
    """List executions for a workflow"""
    try:
        store = RedisWorkflowStore()
        executions = store.list_executions(workflow_name, limit)
        
        if output_format == 'json':
            click.echo(json.dumps(executions, indent=2))
        else:
            if not executions:
                click.echo(f"No executions found for workflow: {workflow_name}")
                return
            
            click.echo(f"\n🔄 Executions for {workflow_name} ({len(executions)} total)")
            click.echo("=" * 60)
            
            for execution in executions:
                status_icon = _get_status_icon(execution['status'])
                click.echo(f"\n{status_icon} {execution['execution_id']}")
                click.echo(f"   Status: {execution['status']}")
                click.echo(f"   Started: {execution['started_at']}")
                if execution['completed_at']:
                    click.echo(f"   Completed: {execution['completed_at']}")
                if execution['error']:
                    click.echo(f"   Error: {execution['error']}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('execution_id')
@click.option('--format', 'output_format', default='detailed', help='Output format: detailed, json')
def show_execution(execution_id, output_format):
    """Show details of a specific execution"""
    try:
        store = RedisWorkflowStore()
        execution = store.load_execution(execution_id)
        
        if not execution:
            click.echo(f"Error: Execution not found: {execution_id}", err=True)
            sys.exit(1)
        
        if output_format == 'json':
            click.echo(json.dumps(execution.to_dict(), indent=2, default=str))
        else:
            _display_execution_details(execution)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
def storage_stats():
    """Display storage statistics"""
    try:
        store = RedisWorkflowStore()
        stats = store.get_storage_stats()
        
        if not stats:
            click.echo("Error: Could not retrieve storage statistics", err=True)
            sys.exit(1)
        
        click.echo("\n📊 Storage Statistics")
        click.echo("=" * 30)
        click.echo(f"Total Workflows: {stats['total_workflows']}")
        click.echo(f"Total Executions: {stats['total_executions']}")
        click.echo(f"Redis Memory Usage: {stats['redis_memory_usage']}")
        click.echo(f"Connected Clients: {stats['redis_connected_clients']}")
        
        if stats.get('workflow_status_counts'):
            click.echo("\nWorkflow Status Counts:")
            for status, count in stats['workflow_status_counts'].items():
                click.echo(f"  {status}: {count}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.confirmation_option(prompt='Are you sure you want to cleanup expired data?')
def cleanup():
    """Clean up expired workflow and execution data"""
    try:
        store = RedisWorkflowStore()
        stats = store.cleanup_expired_data()
        
        click.echo(f"✅ Cleanup completed:")
        click.echo(f"  Workflows cleaned: {stats['workflows']}")
        click.echo(f"  Executions cleaned: {stats['executions']}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
def test_connection():
    """Test Redis connection"""
    try:
        store = RedisWorkflowStore()
        if store.is_connected():
            click.echo("✅ Redis connection successful!")
            stats = store.get_storage_stats()
            click.echo(f"Memory Usage: {stats.get('redis_memory_usage', 'N/A')}")
            click.echo(f"Connected Clients: {stats.get('redis_connected_clients', 'N/A')}")
        else:
            click.echo("❌ Redis connection failed")
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"❌ Connection error: {e}", err=True)
        sys.exit(1)

# Helper functions

def _display_execution_result(result: Dict[str, Any]):
    """Display execution result in a formatted way"""
    status_icon = _get_status_icon(result['status'])
    
    click.echo(f"\n{status_icon} Execution Result")
    click.echo("=" * 40)
    click.echo(f"Execution ID: {result['execution_id']}")
    click.echo(f"Status: {result['status']}")
    
    if result.get('error'):
        click.echo(f"Error: {result['error']}")
    
    if result.get('outputs'):
        click.echo(f"\nOutputs:")
        for key, value in result['outputs'].items():
            click.echo(f"  {key}: {value}")
    
    if result.get('step_results'):
        click.echo(f"\nStep Results:")
        for step_id, step_result in result['step_results'].items():
            step_status = "✅" if step_result.get('success') else "❌"
            click.echo(f"  {step_status} {step_id}: {step_result.get('message', 'N/A')}")

def _display_execution_details(execution):
    """Display detailed execution information"""
    status_icon = _get_status_icon(execution.status)
    
    click.echo(f"\n{status_icon} Execution Details")
    click.echo("=" * 50)
    click.echo(f"Execution ID: {execution.execution_id}")
    click.echo(f"Workflow: {execution.workflow_name} v{execution.workflow_version}")
    click.echo(f"Status: {execution.status}")
    click.echo(f"Started: {execution.started_at}")
    
    if execution.completed_at:
        click.echo(f"Completed: {execution.completed_at}")
        duration = execution.completed_at - execution.started_at
        click.echo(f"Duration: {duration}")
    
    if execution.error:
        click.echo(f"Error: {execution.error}")
    
    if execution.inputs:
        click.echo(f"\nInputs:")
        for key, value in execution.inputs.items():
            click.echo(f"  {key}: {value}")
    
    if execution.outputs:
        click.echo(f"\nOutputs:")
        for key, value in execution.outputs.items():
            click.echo(f"  {key}: {value}")
    
    if execution.step_results:
        click.echo(f"\nStep Results:")
        for step_id, step_result in execution.step_results.items():
            step_status = "✅" if step_result.get('success') else "❌"
            click.echo(f"  {step_status} {step_id}: {step_result.get('message', 'N/A')}")

def _get_status_icon(status: str) -> str:
    """Get icon for execution status"""
    status_icons = {
        'draft': '📝',
        'validated': '✅',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'rolled_back': '↩️'
    }
    return status_icons.get(status.lower(), '❓')

if __name__ == '__main__':
    cli()