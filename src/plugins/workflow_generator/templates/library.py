from typing import Dict, List, Optional, Any, Tuple
import yaml
import json
import re
import logging
from dataclasses import dataclass
from pathlib import Path
import os
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class WorkflowTemplate:
    """Represents a workflow template with metadata"""
    name: str
    description: str
    keywords: List[str]
    workflow_dict: Dict[str, Any]
    usage_count: int = 0
    rating: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords,
            "workflow": self.workflow_dict,
            "usage_count": self.usage_count,
            "rating": self.rating
        }

@dataclass
class TemplateMatch:
    """Represents a template match with confidence score"""
    template: WorkflowTemplate
    confidence: float
    matched_keywords: List[str]
    
    def __lt__(self, other):
        """Sort by confidence score (descending)"""
        return self.confidence > other.confidence

class TemplateLibrary:
    """
    Manages workflow templates with pattern matching and application
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.templates_dir = templates_dir or self._get_default_templates_dir()
        self._load_built_in_templates()
        
    def _get_default_templates_dir(self) -> str:
        """Get default templates directory"""
        current_dir = Path(__file__).parent
        patterns_dir = current_dir / "patterns"
        return str(patterns_dir)
        
    def _load_built_in_templates(self):
        """Load built-in workflow templates"""
        # Load templates from patterns directory
        patterns_dir = Path(self.templates_dir)
        if patterns_dir.exists():
            for template_file in patterns_dir.glob("*.yaml"):
                try:
                    self._load_template_file(template_file)
                except Exception as e:
                    logger.error(f"Failed to load template {template_file}: {e}")
        
        # Load built-in templates if no files found
        if not self.templates:
            self._load_default_templates()
    
    def _load_template_file(self, file_path: Path):
        """Load a single template file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            # Extract template metadata
            template_name = template_data.get('name', file_path.stem)
            template_desc = template_data.get('description', '')
            keywords = template_data.get('keywords', [])
            
            # Create template object
            template = WorkflowTemplate(
                name=template_name,
                description=template_desc,
                keywords=keywords,
                workflow_dict=template_data.get('workflow', template_data)
            )
            
            self.templates[template_name] = template
            logger.info(f"Loaded template: {template_name}")
            
        except Exception as e:
            logger.error(f"Error loading template file {file_path}: {e}")
            raise
    
    def _load_default_templates(self):
        """Load default built-in templates"""
        # Python Project Setup Template
        python_template = WorkflowTemplate(
            name="python-project-setup",
            description="Initialize a Python project with best practices",
            keywords=["python", "project", "setup", "initialize", "venv", "pip", "requirements"],
            workflow_dict={
                "name": "python-project-setup",
                "version": "1.0",
                "description": "Initialize a Python project with best practices",
                "inputs": [
                    {"name": "project_name", "type": "string", "required": True},
                    {"name": "python_version", "type": "string", "default": "3.11"},
                    {"name": "include_tests", "type": "boolean", "default": True}
                ],
                "steps": [
                    {
                        "id": "create_structure",
                        "type": "command",
                        "description": "Create project directory structure",
                        "command": "mkdir -p ${project_name}/{src,tests,docs} && touch ${project_name}/README.md && touch ${project_name}/.gitignore"
                    },
                    {
                        "id": "setup_venv",
                        "type": "command",
                        "description": "Create virtual environment",
                        "command": "python${python_version} -m venv venv",
                        "working_dir": "${project_name}"
                    },
                    {
                        "id": "create_requirements",
                        "type": "command",
                        "description": "Create requirements.txt",
                        "command": "touch requirements.txt",
                        "working_dir": "${project_name}"
                    }
                ]
            }
        )
        
        # React App Deployment Template
        react_template = WorkflowTemplate(
            name="react-app-deploy",
            description="Build and deploy React application",
            keywords=["react", "deploy", "build", "npm", "test", "frontend"],
            workflow_dict={
                "name": "react-app-deploy",
                "version": "1.0",
                "description": "Build and deploy React application",
                "inputs": [
                    {"name": "app_path", "type": "string", "required": True},
                    {"name": "environment", "type": "string", "required": True, "validation": {"values": ["development", "staging", "production"]}}
                ],
                "steps": [
                    {
                        "id": "install_deps",
                        "type": "command",
                        "description": "Install dependencies",
                        "command": "npm ci",
                        "working_dir": "${app_path}"
                    },
                    {
                        "id": "run_tests",
                        "type": "command",
                        "description": "Run tests",
                        "command": "npm test -- --watchAll=false",
                        "working_dir": "${app_path}",
                        "on_failure": "abort"
                    },
                    {
                        "id": "build",
                        "type": "command",
                        "description": "Build application",
                        "command": "npm run build",
                        "working_dir": "${app_path}",
                        "environment": {"REACT_APP_ENV": "${environment}"}
                    }
                ]
            }
        )
        
        # Git Workflow Template
        git_template = WorkflowTemplate(
            name="git-workflow",
            description="Common Git operations workflow",
            keywords=["git", "commit", "push", "branch", "merge", "version control"],
            workflow_dict={
                "name": "git-workflow",
                "version": "1.0",
                "description": "Common Git operations workflow",
                "inputs": [
                    {"name": "branch_name", "type": "string", "required": True},
                    {"name": "commit_message", "type": "string", "required": True},
                    {"name": "create_pr", "type": "boolean", "default": False}
                ],
                "steps": [
                    {
                        "id": "create_branch",
                        "type": "command",
                        "description": "Create and checkout new branch",
                        "command": "git checkout -b ${branch_name}"
                    },
                    {
                        "id": "add_changes",
                        "type": "command",
                        "description": "Add all changes",
                        "command": "git add ."
                    },
                    {
                        "id": "commit_changes",
                        "type": "command",
                        "description": "Commit changes",
                        "command": "git commit -m \"${commit_message}\""
                    },
                    {
                        "id": "push_branch",
                        "type": "command",
                        "description": "Push branch to remote",
                        "command": "git push -u origin ${branch_name}"
                    }
                ]
            }
        )
        
        # Docker Build Template
        docker_template = WorkflowTemplate(
            name="docker-build-deploy",
            description="Build and deploy Docker container",
            keywords=["docker", "build", "deploy", "container", "image"],
            workflow_dict={
                "name": "docker-build-deploy",
                "version": "1.0",
                "description": "Build and deploy Docker container",
                "inputs": [
                    {"name": "image_name", "type": "string", "required": True},
                    {"name": "tag", "type": "string", "default": "latest"},
                    {"name": "dockerfile_path", "type": "string", "default": "Dockerfile"},
                    {"name": "push_to_registry", "type": "boolean", "default": False}
                ],
                "steps": [
                    {
                        "id": "build_image",
                        "type": "command",
                        "description": "Build Docker image",
                        "command": "docker build -f ${dockerfile_path} -t ${image_name}:${tag} .",
                        "timeout": 600
                    },
                    {
                        "id": "push_image",
                        "type": "conditional",
                        "description": "Push image to registry if requested",
                        "condition": "${push_to_registry}",
                        "then_steps": [
                            {
                                "id": "push_to_registry",
                                "type": "command",
                                "command": "docker push ${image_name}:${tag}"
                            }
                        ]
                    }
                ]
            }
        )
        
        # Add templates to library
        self.templates["python-project-setup"] = python_template
        self.templates["react-app-deploy"] = react_template
        self.templates["git-workflow"] = git_template
        self.templates["docker-build-deploy"] = docker_template
        
        logger.info(f"Loaded {len(self.templates)} built-in templates")
    
    def find_matches(self, description: str, threshold: float = 0.1) -> List[TemplateMatch]:
        """
        Find templates that match the given description
        
        Args:
            description: Natural language description
            threshold: Minimum confidence threshold (0.0 to 1.0)
            
        Returns:
            List of template matches sorted by confidence
        """
        matches = []
        description_lower = description.lower()
        
        for template in self.templates.values():
            confidence, matched_keywords = self._calculate_match_confidence(
                description_lower, template
            )
            
            if confidence >= threshold:
                matches.append(TemplateMatch(
                    template=template,
                    confidence=confidence,
                    matched_keywords=matched_keywords
                ))
        
        # Sort by confidence (descending)
        matches.sort()
        
        logger.info(f"Found {len(matches)} template matches for description")
        return matches
    
    def _calculate_match_confidence(self, description: str, template: WorkflowTemplate) -> Tuple[float, List[str]]:
        """
        Calculate confidence score for template match
        
        Args:
            description: Normalized description text
            template: Template to match against
            
        Returns:
            Tuple of (confidence_score, matched_keywords)
        """
        matched_keywords = []
        keyword_scores = []
        
        # Check exact keyword matches
        for keyword in template.keywords:
            if keyword.lower() in description:
                matched_keywords.append(keyword)
                keyword_scores.append(1.0)
        
        # Check partial keyword matches
        for keyword in template.keywords:
            if keyword.lower() not in description:
                # Check for partial matches (e.g., "react" in "reactjs")
                if any(keyword.lower() in word for word in description.split()):
                    matched_keywords.append(keyword)
                    keyword_scores.append(0.7)
        
        # Calculate base confidence from keyword matches
        if not template.keywords:
            base_confidence = 0.0
        else:
            base_confidence = sum(keyword_scores) / len(template.keywords)
        
        # Boost confidence based on template popularity
        popularity_boost = min(template.usage_count * 0.01, 0.2)
        
        # Boost confidence based on template rating
        rating_boost = template.rating * 0.1
        
        # Final confidence score
        confidence = min(base_confidence + popularity_boost + rating_boost, 1.0)
        
        return confidence, matched_keywords
    
    def apply_template(self, template_match: TemplateMatch, workflow_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply template to workflow dictionary, merging with existing content
        
        Args:
            template_match: Template match to apply
            workflow_dict: Existing workflow dictionary
            
        Returns:
            Merged workflow dictionary
        """
        template = template_match.template
        template_workflow = template.workflow_dict.copy()
        
        # Merge basic properties
        merged = {
            "name": workflow_dict.get("name", template_workflow.get("name", "generated-workflow")),
            "version": workflow_dict.get("version", template_workflow.get("version", "1.0")),
            "description": workflow_dict.get("description", template_workflow.get("description", "")),
        }
        
        # Merge inputs
        template_inputs = template_workflow.get("inputs", [])
        workflow_inputs = workflow_dict.get("inputs", [])
        merged_inputs = self._merge_inputs(template_inputs, workflow_inputs)
        merged["inputs"] = merged_inputs
        
        # Merge steps
        template_steps = template_workflow.get("steps", [])
        workflow_steps = workflow_dict.get("steps", [])
        merged_steps = self._merge_steps(template_steps, workflow_steps)
        merged["steps"] = merged_steps
        
        # Merge other properties
        merged["outputs"] = workflow_dict.get("outputs", template_workflow.get("outputs"))
        merged["metadata"] = workflow_dict.get("metadata", template_workflow.get("metadata", {}))
        
        # Update template usage
        template.usage_count += 1
        
        logger.info(f"Applied template '{template.name}' to workflow")
        return merged
    
    def _merge_inputs(self, template_inputs: List[Dict], workflow_inputs: List[Dict]) -> List[Dict]:
        """Merge template inputs with workflow inputs"""
        merged = template_inputs.copy()
        
        # Add workflow inputs that don't exist in template
        template_names = {inp["name"] for inp in template_inputs}
        for workflow_input in workflow_inputs:
            if workflow_input["name"] not in template_names:
                merged.append(workflow_input)
        
        return merged
    
    def _merge_steps(self, template_steps: List[Dict], workflow_steps: List[Dict]) -> List[Dict]:
        """Merge template steps with workflow steps"""
        merged = template_steps.copy()
        
        # Add workflow steps that don't exist in template
        template_ids = {step["id"] for step in template_steps}
        for workflow_step in workflow_steps:
            if workflow_step["id"] not in template_ids:
                merged.append(workflow_step)
        
        return merged
    
    def get_template(self, name: str) -> Optional[WorkflowTemplate]:
        """Get template by name"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[WorkflowTemplate]:
        """List all available templates"""
        return list(self.templates.values())
    
    def add_template(self, template: WorkflowTemplate) -> bool:
        """
        Add a new template to the library
        
        Args:
            template: Template to add
            
        Returns:
            True if added successfully
        """
        try:
            self.templates[template.name] = template
            logger.info(f"Added template: {template.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add template: {e}")
            return False
    
    def remove_template(self, name: str) -> bool:
        """
        Remove a template from the library
        
        Args:
            name: Template name to remove
            
        Returns:
            True if removed successfully
        """
        if name in self.templates:
            del self.templates[name]
            logger.info(f"Removed template: {name}")
            return True
        else:
            logger.warning(f"Template not found: {name}")
            return False
    
    def update_template_rating(self, name: str, rating: float) -> bool:
        """
        Update template rating
        
        Args:
            name: Template name
            rating: New rating (0.0 to 5.0)
            
        Returns:
            True if updated successfully
        """
        if name in self.templates:
            self.templates[name].rating = max(0.0, min(5.0, rating))
            logger.info(f"Updated rating for template {name}: {rating}")
            return True
        else:
            logger.warning(f"Template not found: {name}")
            return False
    
    def save_template(self, template: WorkflowTemplate, file_path: Optional[str] = None) -> bool:
        """
        Save template to YAML file
        
        Args:
            template: Template to save
            file_path: Optional file path, defaults to patterns directory
            
        Returns:
            True if saved successfully
        """
        try:
            if file_path is None:
                patterns_dir = Path(self.templates_dir)
                patterns_dir.mkdir(parents=True, exist_ok=True)
                file_path = patterns_dir / f"{template.name}.yaml"
            
            template_data = {
                "name": template.name,
                "description": template.description,
                "keywords": template.keywords,
                "workflow": template.workflow_dict
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"Saved template '{template.name}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            return False
    
    def export_library(self, export_path: str) -> bool:
        """
        Export entire template library to JSON
        
        Args:
            export_path: Path to export file
            
        Returns:
            True if exported successfully
        """
        try:
            export_data = {
                "templates": {name: template.to_dict() for name, template in self.templates.items()},
                "metadata": {
                    "total_templates": len(self.templates),
                    "exported_at": str(datetime.now().isoformat())
                }
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported template library to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export library: {e}")
            return False