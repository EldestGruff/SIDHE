#!/usr/bin/env python3
"""
The Great Transformation Spell - From Stars to Enchantment
A magical incantation to transform the realm of SIDHE into SIDHE
"""

import os
import re
import shutil
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# The Ancient Runes of Transformation
TERMINOLOGY_MAP = {
    # Core transformations
    r'\bRiker\b': 'SIDHE',
    r'\briker\b': 'sidhe',
    r'\bRIKER\b': 'SIDHE',
    
    # The hierarchy of power
    r'\bCaptain Andy\b': 'Archmage Andy',
    r'\bCaptain\b': 'Archmage',
    r'\bcaptain\b': 'archmage',
    r'\bApprentice\b': 'SIDHE',
    r'\bnumber one\b': 'SIDHE',
    r"Archmage's": "Archmage's",
    r"archmage's": "archmage's",
    
    # Quests and adventures
    r'\bQuest\b': 'Quest',
    r'\bquest\b': 'quest',
    r'\bAway-Quest\b': 'Quest',
    r'\bquest\b': 'quest',
    r'\bMission\b': 'Quest',
    r'\bmission\b': 'quest',
    r'\bMission Brief\b': "Bard's Tale",
    r'\bmission brief\b': "bard's tale",
    
    # Sacred places
    r'\bBridge\b': 'Enchanted Grove',
    r'\bbridge\b': 'enchanted grove',
    r'\bBRIDGE\b': 'ENCHANTED GROVE',
    r'\bCrew Quarters\b': 'Grimoire',
    r'\bcrew quarters\b': 'grimoire',
    r'\bgrimoire\b': 'grimoire',
    r"Archmage's Log": 'Chronicle',
    r"chronicle": 'chronicle',
    r"captains_log": 'chronicle',
    r'\bEngineering\b': 'Enchanted Workshop',
    r'\bengineering\b': 'enchanted workshop',
    
    # Sacred texts
    r'\bPRIME DIRECTIVE\b': 'THE OLD LAWS',
    r'\bThe Old Laws\b': 'The Old Laws',
    r'\bthe old laws\b': 'the old laws',
    r'THE_OLD_LAWS': 'OLD_LAWS',
    
    # Communication patterns
    r'\bAcknowledged\b': 'By the ancient magic!',
    r'\backnowledged\b': 'by the ancient magic!',
    r'\bMission complete\b': 'The quest is fulfilled!',
    r'\bMission Complete\b': 'The Quest is Fulfilled!',
    r'\bMake it so\b': 'So mote it be',
    r'\bmake it so\b': 'so mote it be',
    r'\bStand by\b': 'Gathering the threads of fate',
    r'\bstand by\b': 'gathering the threads of fate',
    r'\bDragon Alert\b': 'Dragon Awakens',
    r'\bred alarm\b': 'dragon awakens',
    r'\bGiant's Warning\b': 'Troll at the Sanctum',
    r'\byellow alarm\b': 'troll at the sanctum',
    
    # File patterns
    r'quest-(\d+)': r'quest-\1',
    r'QUEST-(\d+)': r'QUEST-\1',
    r'QUEST-(\d+)': r'QUEST-\1',
    r'away-(\d+)': r'quest-\1',
    
    # Fairy Tale specific removals
    r'Gruff Academy': 'The Ancient Order',
    r'gruff academy': 'the ancient order',
    r'Fairy Realm': 'The Realm',
    r'fairy realm': 'the realm',
    r'Stardate': 'Moon of',
    r'stardate': 'moon of',
    r'Jean-Luc Picard': 'Merlin the Wise',
    r'William T\. SIDHE': 'Gandalf the Grey',
}

# Directory transformation map
DIRECTORY_MAP = {
    'grimoire': 'grimoire',
    'chronicle': 'chronicle',
    'quests': 'quests',
    'spellcraft': 'enchanted-workshop'
}

# File rename map
FILE_RENAME_MAP = {
    'THE_OLD_LAWS.md': 'THE_OLD_LAWS.md',
    'MAGICAL_TOME.md': 'SIDHE_GUIDE.md',
    'BRIDGE.md': 'ENCHANTED_GROVE.md',
    'sidhe-state.json': 'sidhe-state.json',
    '.sidhe-state.json': '.sidhe-state.json'
}

class MigrationSpell:
    """The Great Spell of Transformation"""
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.changes_made = []
        self.errors = []
        
    def cast_spell(self, project_root='.'):
        """Begin the great transformation"""
        print("🌟 The Great Transformation Spell Begins! 🌟")
        print("=" * 60)
        
        if self.dry_run:
            print("🔮 Divination Mode: Showing what would change...")
        else:
            print("⚡ Casting with full power! Changes will be permanent!")
        
        # Create backup first
        if not self.dry_run:
            self._create_backup(project_root)
        
        # Transform directories
        self._transform_directories(project_root)
        
        # Transform file contents
        self._transform_files(project_root)
        
        # Rename specific files
        self._rename_files(project_root)
        
        # Create new lore documents
        self._create_lore_documents(project_root)
        
        # Update git configuration
        self._update_git_config(project_root)
        
        # Generate summary scroll
        self._generate_summary()
        
    def _create_backup(self, project_root):
        """Create a mystical backup before transformation"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"riker_backup_{timestamp}.tar.gz"
        
        print(f"📦 Creating protective ward (backup): {backup_name}")
        os.system(f"tar -czf {backup_name} --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' {project_root}")
        print("✨ Backup enchantment complete!")
        
    def _transform_directories(self, project_root):
        """Transform the directory structure"""
        print("\n🏰 Reshaping the realm's geography...")
        
        for old_name, new_name in DIRECTORY_MAP.items():
            old_path = Path(project_root) / old_name
            new_path = Path(project_root) / new_name
            
            if old_path.exists():
                if self.dry_run:
                    print(f"  Would rename: {old_name} → {new_name}")
                else:
                    shutil.move(str(old_path), str(new_path))
                    self.changes_made.append(f"Directory: {old_name} → {new_name}")
                    print(f"  ✨ Transformed: {old_name} → {new_name}")
                    
    def _transform_files(self, project_root):
        """Transform file contents with the terminology map"""
        print("\n📜 Rewriting the ancient texts...")
        
        # File extensions to process
        extensions = ['.py', '.md', '.yml', '.yaml', '.json', '.sh', '.txt']
        
        for ext in extensions:
            for filepath in Path(project_root).rglob(f'*{ext}'):
                # Skip .git directory and backups
                if '.git' in str(filepath) or 'backup' in str(filepath):
                    continue
                    
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original = content
                    
                    # Apply all transformations
                    for pattern, replacement in TERMINOLOGY_MAP.items():
                        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                    
                    if content != original:
                        if self.dry_run:
                            print(f"  Would transform: {filepath}")
                        else:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            self.changes_made.append(f"File content: {filepath}")
                            print(f"  ✨ Enchanted: {filepath}")
                            
                except Exception as e:
                    self.errors.append(f"Failed to transform {filepath}: {e}")
                    
    def _rename_files(self, project_root):
        """Rename specific files"""
        print("\n📝 Renaming sacred scrolls...")
        
        for old_name, new_name in FILE_RENAME_MAP.items():
            old_path = Path(project_root) / old_name
            new_path = Path(project_root) / new_name
            
            if old_path.exists():
                if self.dry_run:
                    print(f"  Would rename: {old_name} → {new_name}")
                else:
                    shutil.move(str(old_path), str(new_path))
                    self.changes_made.append(f"File renamed: {old_name} → {new_name}")
                    print(f"  ✨ Renamed: {old_name} → {new_name}")
                    
    def _create_lore_documents(self, project_root):
        """Create new fairy tale themed documents"""
        print("\n📚 Scribing new tales of power...")
        
        # Create GRUFF_LORE.md
        gruff_lore = """# The Lore of Gruff Software
*As recorded in the Chronicle of the Archmage*

## The Ancient Tale

In the time before time, when code ran wild and bugs roamed free across the digital realm, three wise goats of Gruff set forth to bring order to chaos. They were not ordinary goats, but masters of the arcane arts of software craft.

## The Three Bridges of Development

### The First Sanctum - Development
Where young spells are tested and proven. Here, the code takes its first steps, learning to channel magic properly. Many bugs lurk beneath this sanctum, but they are small and easily vanquished.

### The Second Sanctum - Staging  
A stronger sanctum, where only proven enchantments may cross. The trolls here are fiercer, testing each spell with cunning traps and illusions that mirror the production realm.

### The Third Sanctum - Production
The mightiest sanctum of all, where only the most powerful and pure magic may pass. The guardian of this sanctum is an ancient dragon who breathes fire upon any spell that shows weakness.

## The Way of Withershins

While others follow the sun's path (clockwise, or "deosil"), Gruff Software walks withershins - counter-clockwise, against the grain. This unconventional path reveals hidden patterns and secret optimizations that others miss.

*"Going withershins around the problem oft reveals the solution."* - Ancient Gruff Proverb

## The Coming of SIDHE

And lo, the Archmages summoned forth SIDHE - the Sentient Interactive Development Heuristic Engine - a magical being of pure logic and creativity, to aid in their quest for perfect code.

---
*So mote it be.*
"""
        
        # Create ENCHANTMENT_GUIDE.md
        enchantment_guide = """# The Enchanter's Guide to SIDHE

## Summoning SIDHE

To summon SIDHE for assistance, speak these words into the Enchanted Grove:

```
Oh SIDHE, guardian of code and keeper of patterns,
I summon thee to aid in this quest!
```

## The Language of Magic

When SIDHE speaks, it uses the ancient tongue:

- **"By the ancient magic!"** - Acknowledgment of your request
- **"The quest is fulfilled!"** - Successful completion
- **"Gathering the threads of fate..."** - Processing your request
- **"A dragon stirs!"** - Critical error detected
- **"Troll at the sanctum!"** - Warning of potential issues
- **"So mote it be"** - Confirming an action

## Quest Classifications

- 🔴 **Dragon-level Quest** - Critical priority, requires immediate attention
- 🟡 **Giant's Task** - Important work that shapes the realm
- 🟢 **Woodland Adventure** - Regular maintenance and improvements

## The Old Laws

Remember always The Old Laws that govern our craft:
1. **First Law**: The Archmage's vision guides all quests
2. **Second Law**: SIDHE serves to make manifest the vision through deed
3. **Third Law**: All magic must be tested thrice before release
4. **Fourth Law**: Document thy spells, lest they become cursed mysteries

---
*May your code compile on the first try.*
"""
        
        if not self.dry_run:
            with open(Path(project_root) / 'GRUFF_LORE.md', 'w') as f:
                f.write(gruff_lore)
            print("  ✨ Created: GRUFF_LORE.md")
            
            with open(Path(project_root) / 'ENCHANTMENT_GUIDE.md', 'w') as f:
                f.write(enchantment_guide)
            print("  ✨ Created: ENCHANTMENT_GUIDE.md")
            
    def _update_git_config(self, project_root):
        """Update git configuration"""
        print("\n🔮 Updating the git grimoire...")
        
        if not self.dry_run:
            # Update git remote URL if it contains 'sidhe'
            os.system("git remote -v | grep sidhe && git remote set-url origin $(git remote get-url origin | sed 's/sidhe/sidhe/g')")
            
    def _generate_summary(self):
        """Generate a summary of the transformation"""
        print("\n" + "=" * 60)
        print("✨ THE TRANSFORMATION IS COMPLETE! ✨")
        print("=" * 60)
        
        if self.dry_run:
            print("🔮 This was merely a vision. Run without --dry-run to manifest.")
        else:
            print(f"📊 Changes Made: {len(self.changes_made)}")
            print(f"⚠️  Errors: {len(self.errors)}")
            
            if self.errors:
                print("\n❌ Errors encountered:")
                for error in self.errors[:5]:
                    print(f"  - {error}")
                    
            print("\n🎉 SIDHE has risen from the ashes of the old realm!")
            print("   The fairy tale transformation is complete!")
            
        print("\n📜 Next steps:")
        print("  1. Review the changes with: git diff")
        print("  2. Commit the transformation: git commit -am '✨ Transform to SIDHE - fairy tale rebranding'")
        print("  3. Update your GitHub repository name from 'sidhe' to 'sidhe'")
        print("  4. Begin your first quest in the new realm!")


def main():
    """The main incantation"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Transform SIDHE into SIDHE - A fairy tale rebranding"
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would change without making changes'
    )
    parser.add_argument(
        '--path',
        default='.',
        help='Path to project root (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Cast the spell!
    spell = MigrationSpell(dry_run=args.dry_run)
    spell.cast_spell(args.path)


if __name__ == "__main__":
    main()
