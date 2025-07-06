import re
import logging
from typing import List, Dict, Any, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SafetyResult:
    is_safe: bool
    violations: List[str]
    warnings: List[str]
    
    def __bool__(self):
        return self.is_safe

class SafetyChecker:
    """Security and safety validation for workflows"""
    
    def __init__(self):
        # Dangerous commands patterns
        self.dangerous_patterns = {
            # System destructive commands
            r'\brm\s+-[rf]+': "Dangerous file deletion command",
            r'\bdd\s+if=': "Dangerous disk operation",
            r'\bformat\s+[A-Z]:': "Dangerous format command",
            r'\bfdisk\s+': "Dangerous disk partitioning",
            r'\bmkfs\s+': "Dangerous filesystem creation",
            
            # Network/security risks
            r'\bcurl\s+.*\|\s*(sh|bash|zsh)': "Dangerous pipe to shell from network",
            r'\bwget\s+.*\|\s*(sh|bash|zsh)': "Dangerous pipe to shell from network",
            r'\bssh\s+.*\|\s*(sh|bash)': "Dangerous SSH command execution",
            r'\bsudo\s+': "Privilege escalation command",
            r'\bsu\s+': "User switching command",
            
            # Process manipulation
            r'\bkill\s+-9': "Forceful process termination",
            r'\bkillall\s+': "Mass process termination",
            r'\bpkill\s+': "Pattern-based process killing",
            
            # System modification
            r'\bchmod\s+777': "Dangerous permission setting",
            r'\bchown\s+.*root': "Dangerous ownership change",
            r'\bmount\s+': "Filesystem mounting",
            r'\bumount\s+': "Filesystem unmounting",
            
            # Code execution risks
            r'\beval\s+': "Dynamic code evaluation",
            r'\bexec\s+': "Code execution",
            r'`[^`]*`': "Command substitution",
            r'\$\([^)]*\)': "Command substitution",
            
            # File system risks
            r'/etc/passwd': "Access to password file",
            r'/etc/shadow': "Access to shadow file",
            r'/etc/sudoers': "Access to sudo configuration",
            r'/root/': "Access to root directory",
            r'/boot/': "Access to boot partition",
            
            # Environment manipulation
            r'\bexport\s+PATH=': "PATH manipulation",
            r'\bexport\s+LD_LIBRARY_PATH=': "Library path manipulation",
            r'\bunset\s+': "Environment variable removal",
        }
        
        # Suspicious patterns (warnings, not errors)
        self.suspicious_patterns = {
            r'\bfind\s+/\s+': "Searching entire filesystem",
            r'\bgrep\s+-r\s+.*\s+/': "Recursive search on filesystem",
            r'\btar\s+.*\s+/': "Archiving from root",
            r'\bcp\s+-r\s+.*\s+/': "Recursive copy to/from root",
            r'\bmv\s+.*\s+/': "Moving files to root",
            r'\bchmod\s+\+x': "Making files executable",
            r'\bnohup\s+': "Background process creation",
            r'\bscreen\s+': "Screen session creation",
            r'\btmux\s+': "Terminal multiplexer usage",
            r'\bsystemctl\s+': "System service management",
            r'\bservice\s+': "Service management",
            r'\bcrontab\s+': "Cron job management",
            r'\bat\s+': "Scheduled task creation",
            r'\biptables\s+': "Firewall rule modification",
            r'\bufw\s+': "Firewall management",
            r'\bpsql\s+': "Database access",
            r'\bmysql\s+': "Database access",
            r'\bmongo\s+': "Database access",
            r'\bredis-cli\s+': "Redis access",
        }
        
        # Allowed commands for common operations
        self.allowed_commands = {
            'ls', 'cat', 'head', 'tail', 'less', 'more', 'wc', 'sort', 'uniq',
            'grep', 'sed', 'awk', 'cut', 'tr', 'tee', 'echo', 'printf',
            'pwd', 'cd', 'mkdir', 'touch', 'date', 'whoami', 'id',
            'ps', 'top', 'df', 'du', 'free', 'uptime', 'uname',
            'git', 'npm', 'pip', 'python', 'node', 'java', 'gcc',
            'make', 'cmake', 'go', 'rust', 'cargo', 'docker',
            'kubectl', 'helm', 'terraform', 'ansible'
        }
        
        # File path restrictions
        self.restricted_paths = {
            '/etc/', '/root/', '/boot/', '/sys/', '/proc/', '/dev/',
            '/var/log/', '/var/spool/', '/tmp/', '/var/tmp/'
        }
        
        # Environment variable restrictions
        self.restricted_env_vars = {
            'PATH', 'LD_LIBRARY_PATH', 'PYTHONPATH', 'JAVA_HOME',
            'HOME', 'USER', 'SHELL', 'SUDO_USER'
        }
        
        logger.info("SafetyChecker initialized with security rules")
    
    def check(self, workflow) -> SafetyResult:
        """
        Perform comprehensive safety check on workflow
        
        Args:
            workflow: Workflow object to check
            
        Returns:
            SafetyResult with security assessment
        """
        logger.info(f"Performing safety check on workflow: {workflow.name}")
        
        violations = []
        warnings = []
        
        # Check workflow metadata
        meta_violations, meta_warnings = self._check_metadata(workflow)
        violations.extend(meta_violations)
        warnings.extend(meta_warnings)
        
        # Check each step
        for step in workflow.steps:
            step_violations, step_warnings = self._check_step(step)
            violations.extend(step_violations)
            warnings.extend(step_warnings)
        
        # Check overall workflow patterns
        workflow_violations, workflow_warnings = self._check_workflow_patterns(workflow)
        violations.extend(workflow_violations)
        warnings.extend(workflow_warnings)
        
        result = SafetyResult(
            is_safe=len(violations) == 0,
            violations=violations,
            warnings=warnings
        )
        
        logger.info(f"Safety check completed: {'SAFE' if result.is_safe else 'UNSAFE'}")
        return result
    
    def _check_metadata(self, workflow) -> tuple[List[str], List[str]]:
        """Check workflow metadata for safety issues"""
        violations = []
        warnings = []
        
        # Check for suspicious names
        if workflow.name:
            if any(word in workflow.name.lower() for word in ['hack', 'exploit', 'attack', 'malware']):
                warnings.append(f"Suspicious workflow name: {workflow.name}")
        
        # Check metadata for sensitive information
        if workflow.metadata:
            if any(key.lower() in ['password', 'key', 'token', 'secret'] for key in workflow.metadata.keys()):
                violations.append("Workflow metadata contains sensitive information")
        
        return violations, warnings
    
    def _check_step(self, step) -> tuple[List[str], List[str]]:
        """Check individual step for safety issues"""
        violations = []
        warnings = []
        
        step_id = step.id or "unnamed_step"
        
        # Check command steps
        if step.type == "command" and step.command:
            cmd_violations, cmd_warnings = self._check_command(step.command, step_id)
            violations.extend(cmd_violations)
            warnings.extend(cmd_warnings)
        
        # Check working directory
        if step.working_dir:
            if any(step.working_dir.startswith(path) for path in self.restricted_paths):
                violations.append(f"Step '{step_id}' uses restricted path: {step.working_dir}")
        
        # Check environment variables
        if step.params and isinstance(step.params, dict):
            env_vars = step.params.get('environment', {})
            if env_vars:
                for var_name in env_vars.keys():
                    if var_name in self.restricted_env_vars:
                        violations.append(f"Step '{step_id}' modifies restricted environment variable: {var_name}")
        
        # Check timeout (security DoS prevention)
        if step.timeout > 3600:  # 1 hour
            warnings.append(f"Step '{step_id}' has very long timeout ({step.timeout}s)")
        
        # Check plugin actions
        if step.type == "plugin_action":
            if step.plugin and step.plugin not in ['github_integration', 'memory_manager', 'conversation_engine']:
                warnings.append(f"Step '{step_id}' uses external plugin: {step.plugin}")
        
        return violations, warnings
    
    def _check_command(self, command: str, step_id: str) -> tuple[List[str], List[str]]:
        """Check command for security issues"""
        violations = []
        warnings = []
        
        # Check for dangerous patterns
        for pattern, description in self.dangerous_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                violations.append(f"Step '{step_id}' contains dangerous command: {description}")
        
        # Check for suspicious patterns
        for pattern, description in self.suspicious_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                warnings.append(f"Step '{step_id}' contains suspicious command: {description}")
        
        # Check for unknown commands
        cmd_violations, cmd_warnings = self._check_command_allowlist(command, step_id)
        violations.extend(cmd_violations)
        warnings.extend(cmd_warnings)
        
        # Check for secrets in command
        if self._contains_secrets(command):
            violations.append(f"Step '{step_id}' command contains potential secrets")
        
        return violations, warnings
    
    def _check_command_allowlist(self, command: str, step_id: str) -> tuple[List[str], List[str]]:
        """Check if command uses only allowed programs"""
        violations = []
        warnings = []
        
        # Extract main command (first word)
        main_cmd = command.strip().split()[0] if command.strip() else ""
        
        # Remove common prefixes
        if main_cmd.startswith('./'):
            main_cmd = main_cmd[2:]
        elif main_cmd.startswith('/'):
            # Absolute path - extract command name
            main_cmd = main_cmd.split('/')[-1]
        
        # Check if command is in allowlist
        if main_cmd and main_cmd not in self.allowed_commands:
            # Check if it's a shell builtin or common utility
            shell_builtins = {'cd', 'echo', 'exit', 'export', 'pwd', 'test', 'true', 'false'}
            if main_cmd not in shell_builtins:
                warnings.append(f"Step '{step_id}' uses non-allowlisted command: {main_cmd}")
        
        return violations, warnings
    
    def _check_workflow_patterns(self, workflow) -> tuple[List[str], List[str]]:
        """Check overall workflow patterns"""
        violations = []
        warnings = []
        
        # Check for privilege escalation patterns
        has_sudo = any(
            step.type == "command" and step.command and "sudo" in step.command.lower()
            for step in workflow.steps
        )
        
        if has_sudo:
            violations.append("Workflow contains privilege escalation commands")
        
        # Check for network operations
        network_steps = [
            step for step in workflow.steps
            if step.type == "command" and step.command and 
            any(net_cmd in step.command.lower() for net_cmd in ['curl', 'wget', 'nc', 'telnet', 'ssh'])
        ]
        
        if len(network_steps) > 3:
            warnings.append("Workflow contains many network operations")
        
        # Check for file system operations
        fs_steps = [
            step for step in workflow.steps
            if step.type == "command" and step.command and 
            any(fs_cmd in step.command.lower() for fs_cmd in ['rm', 'cp', 'mv', 'chmod', 'chown'])
        ]
        
        if len(fs_steps) > 5:
            warnings.append("Workflow contains many file system operations")
        
        # Check for long-running workflows
        total_timeout = sum(step.timeout for step in workflow.steps)
        if total_timeout > 7200:  # 2 hours
            warnings.append(f"Workflow has very long total timeout ({total_timeout}s)")
        
        return violations, warnings
    
    def _contains_secrets(self, text: str) -> bool:
        """Check if text contains potential secrets"""
        secret_patterns = [
            r'password[=:]\s*[\'"]?[^\s\'"]+',
            r'token[=:]\s*[\'"]?[^\s\'"]+',
            r'key[=:]\s*[\'"]?[^\s\'"]+',
            r'secret[=:]\s*[\'"]?[^\s\'"]+',
            r'api_key[=:]\s*[\'"]?[^\s\'"]+',
            r'auth[=:]\s*[\'"]?[^\s\'"]+',
            r'[A-Za-z0-9+/]{40,}',  # Base64-like strings
            r'[A-Fa-f0-9]{32,}',    # Hex strings
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def get_safety_summary(self, result: SafetyResult) -> str:
        """Get human-readable safety summary"""
        summary = []
        
        if result.is_safe:
            summary.append("🛡️  Workflow safety check PASSED")
        else:
            summary.append("⚠️  Workflow safety check FAILED")
        
        if result.violations:
            summary.append(f"\nSecurity Violations ({len(result.violations)}):")
            for violation in result.violations:
                summary.append(f"  🚨 {violation}")
        
        if result.warnings:
            summary.append(f"\nSecurity Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                summary.append(f"  ⚠️  {warning}")
        
        return "\n".join(summary)
    
    def suggest_mitigations(self, result: SafetyResult) -> List[str]:
        """Suggest security mitigations"""
        suggestions = []
        
        if not result.is_safe:
            suggestions.append("Review and remove dangerous commands")
            suggestions.append("Use sandboxed execution environment")
            suggestions.append("Implement command allowlisting")
            suggestions.append("Add approval gates for sensitive operations")
        
        if result.warnings:
            suggestions.append("Add monitoring and logging for suspicious operations")
            suggestions.append("Implement resource limits and timeouts")
            suggestions.append("Use least privilege principles")
            suggestions.append("Validate all inputs and outputs")
        
        return suggestions