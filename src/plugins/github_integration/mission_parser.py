import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class MissionObjective:
    """Represents a mission objective"""
    description: str
    is_primary: bool
    sub_objectives: List[str] = field(default_factory=list)

@dataclass
class AcceptanceCriteria:
    """Represents an acceptance criterion"""
    description: str
    is_complete: bool = False

@dataclass
class ParsedMission:
    """Complete parsed mission data"""
    number: int
    title: str
    mission_id: str
    classification: str
    mission_type: str
    objectives: List[MissionObjective]
    technical_specs: Dict[str, Any]
    acceptance_criteria: List[AcceptanceCriteria]
    captains_notes: Optional[str]
    referenced_docs: List[str]

class MissionParser:
    """Parse Away Mission format from issue body"""
    
    def parse_mission(self, issue_number: int, issue_title: str, 
                     issue_body: str) -> ParsedMission:
        """
        Parse GitHub issue into structured mission data
        
        Args:
            issue_number: GitHub issue number
            issue_title: Issue title
            issue_body: Issue body in markdown
            
        Returns:
            Parsed mission object
        """
        # Extract mission ID
        mission_id = self._extract_mission_id(issue_body)
        
        # Parse classification (priority level)
        classification = self._extract_classification(issue_body)
        
        # Extract mission type
        mission_type = self._extract_mission_type(issue_body)
        
        # Extract objectives section
        objectives = self.extract_objectives(issue_body)
        
        # Parse technical specifications
        technical_specs = self._extract_technical_specs(issue_body)
        
        # Extract acceptance criteria
        acceptance_criteria = self.extract_acceptance_criteria(issue_body)
        
        # Extract captain's notes
        captains_notes = self._extract_captains_notes(issue_body)
        
        # Find referenced documentation
        referenced_docs = self.extract_referenced_docs(issue_body)
        
        return ParsedMission(
            number=issue_number,
            title=issue_title,
            mission_id=mission_id,
            classification=classification,
            mission_type=mission_type,
            objectives=objectives,
            technical_specs=technical_specs,
            acceptance_criteria=acceptance_criteria,
            captains_notes=captains_notes,
            referenced_docs=referenced_docs
        )
    
    def _extract_mission_id(self, body: str) -> str:
        """Extract mission ID from body"""
        # Look for patterns like "Mission ID: AWAY-001" or "**Mission ID:** AWAY-001"
        patterns = [
            r'\*\*Mission ID:\*\*\s*([A-Z]+-\d+)',
            r'Mission ID:\s*([A-Z]+-\d+)',
            r'Mission ID:\s*`([A-Z]+-\d+)`',
            r'ID:\s*([A-Z]+-\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "UNKNOWN"
    
    def _extract_classification(self, body: str) -> str:
        """Extract classification/priority from body"""
        # Look for patterns like "Classification: 🔴 Priority One"
        patterns = [
            r'\*\*Classification:\*\*\s*([^\n]+)',
            r'Classification:\s*([^\n]+)',
            r'Priority:\s*([^\n]+)',
            r'🔴\s*Priority\s+One',
            r'🟠\s*Priority\s+Two',
            r'🟡\s*Priority\s+Three',
            r'🟢\s*Priority\s+Four',
            r'🔵\s*Priority\s+Five'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.lastindex else match.group(0)
        
        return "Standard"
    
    def _extract_mission_type(self, body: str) -> str:
        """Extract mission type from body"""
        # Look for patterns like "Type: Implementation" or "Mission Type: Bug Fix"
        patterns = [
            r'\*\*(?:Mission\s+)?Type:\*\*\s*([^\n]+)',
            r'(?:Mission\s+)?Type:\s*([^\n]+)',
            r'Category:\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Try to infer from content or title
        if re.search(r'\b(?:bug|fix|error|issue)\b', body, re.IGNORECASE):
            return "Bug Fix"
        elif re.search(r'\b(?:feature|implement|add|create)\b', body, re.IGNORECASE):
            return "Feature Implementation"
        elif re.search(r'\b(?:refactor|cleanup|optimize)\b', body, re.IGNORECASE):
            return "Refactoring"
        elif re.search(r'\b(?:doc|documentation)\b', body, re.IGNORECASE):
            return "Documentation"
        
        return "General"
    
    def extract_objectives(self, body: str) -> List[MissionObjective]:
        """Extract and parse mission objectives"""
        objectives = []
        
        # Find the objectives section
        objectives_match = re.search(r'#{1,4}\s*🎯\s*Mission\s+Objectives(.*?)(?=#{1,4}|$)', body, re.DOTALL | re.IGNORECASE)
        if not objectives_match:
            objectives_match = re.search(r'#{1,4}\s*Objectives(.*?)(?=#{1,4}|$)', body, re.DOTALL | re.IGNORECASE)
        
        if objectives_match:
            objectives_text = objectives_match.group(1)
            
            # Look for Primary Objective
            primary_match = re.search(r'#{1,4}\s*Primary\s+Objective[:\s]*(.*?)(?=#{1,4}|$)', objectives_text, re.DOTALL | re.IGNORECASE)
            if primary_match:
                primary_text = primary_match.group(1).strip()
                # Extract the main description (first line or paragraph)
                primary_desc = re.split(r'\n\s*\n', primary_text)[0].strip()
                objectives.append(MissionObjective(description=primary_desc, is_primary=True))
            
            # Look for Secondary Objectives
            secondary_match = re.search(r'#{1,4}\s*Secondary\s+Objectives?[:\s]*(.*?)(?=#{1,4}|$)', objectives_text, re.DOTALL | re.IGNORECASE)
            if secondary_match:
                secondary_text = secondary_match.group(1)
                # Extract list items
                sub_objectives = re.findall(r'[-*+]\s*\[[ x]\]\s*(.+)', secondary_text)
                if not sub_objectives:
                    sub_objectives = re.findall(r'[-*+]\s*(.+)', secondary_text)
                
                for sub_obj in sub_objectives:
                    objectives.append(MissionObjective(description=sub_obj.strip(), is_primary=False))
            
            # If no primary/secondary structure, look for general objectives
            if not objectives:
                general_objectives = re.findall(r'[-*+]\s*(?:\[[ x]\]\s*)?(.+)', objectives_text)
                for i, obj in enumerate(general_objectives):
                    objectives.append(MissionObjective(description=obj.strip(), is_primary=(i == 0)))
        
        return objectives
    
    def extract_acceptance_criteria(self, body: str) -> List[AcceptanceCriteria]:
        """Extract and parse acceptance criteria"""
        criteria = []
        
        # Find the acceptance criteria section
        criteria_match = re.search(r'#{1,4}\s*📋\s*Acceptance\s+Criteria(.*?)(?=#{1,4}|$)', body, re.DOTALL | re.IGNORECASE)
        if not criteria_match:
            criteria_match = re.search(r'#{1,4}\s*Acceptance\s+Criteria(.*?)(?=#{1,4}|$)', body, re.DOTALL | re.IGNORECASE)
        
        if criteria_match:
            criteria_text = criteria_match.group(1)
            
            # Extract checklist items
            checklist_items = re.findall(r'[-*+]\s*\[([x ])\]\s*(.+)', criteria_text)
            for is_checked, description in checklist_items:
                criteria.append(AcceptanceCriteria(
                    description=description.strip(),
                    is_complete=(is_checked.lower() == 'x')
                ))
            
            # If no checklist format, look for general list items
            if not criteria:
                general_items = re.findall(r'[-*+]\s*(.+)', criteria_text)
                for item in general_items:
                    criteria.append(AcceptanceCriteria(description=item.strip()))
        
        return criteria
    
    def _extract_technical_specs(self, body: str) -> Dict[str, Any]:
        """Extract technical specifications"""
        specs = {}
        
        # Find the technical specs section
        specs_match = re.search(r'#{1,4}\s*(?:🔧\s*)?Technical\s+Spec(?:ification)?s?(.*?)(?=#{1,4}|$)', body, re.DOTALL | re.IGNORECASE)
        if specs_match:
            specs_text = specs_match.group(1)
            
            # Extract key-value pairs
            kv_pairs = re.findall(r'[-*+]\s*\*\*([^*]+)\*\*:\s*(.+)', specs_text)
            for key, value in kv_pairs:
                specs[key.strip()] = value.strip()
            
            # Extract code blocks
            code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', specs_text, re.DOTALL)
            for lang, code in code_blocks:
                key = f"code_{lang}" if lang else "code"
                specs[key] = code.strip()
        
        return specs
    
    def _extract_captains_notes(self, body: str) -> Optional[str]:
        """Extract captain's notes section"""
        # Look for captain's notes, notes, or comments section
        patterns = [
            r'#{1,4}\s*👨‍✈️\s*Captain[\'\']?s?\s+Notes?(.*?)(?=#{1,4}|$)',
            r'#{1,4}\s*Captain[\'\']?s?\s+Notes?(.*?)(?=#{1,4}|$)',
            r'#{1,4}\s*Notes?(.*?)(?=#{1,4}|$)',
            r'#{1,4}\s*Comments?(.*?)(?=#{1,4}|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
            if match:
                notes = match.group(1).strip()
                if notes:
                    return notes
        
        return None
    
    def extract_referenced_docs(self, body: str) -> List[str]:
        """Find all referenced specification documents"""
        docs = []
        
        # Look for markdown links to .md files
        md_links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', body)
        for title, path in md_links:
            docs.append(path)
        
        # Look for direct references to spec files
        spec_refs = re.findall(r'(?:spec|specification|doc)(?:ument)?s?[:\s]*([^\s]+\.md)', body, re.IGNORECASE)
        docs.extend(spec_refs)
        
        # Look for crew-quarters references
        crew_refs = re.findall(r'crew-quarters/([^\s]+\.md)', body)
        docs.extend([f"crew-quarters/{ref}" for ref in crew_refs])
        
        # Remove duplicates and return
        return list(set(docs))