#!/usr/bin/env python3
"""
OMNIMESH Codebase Audit & Trinity Analysis
Complete analysis of what's Trinity vs old OMNIMESH
"""

import os
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class CodebaseAuditor:
    def __init__(self, root_path):
        self.root_path = Path(root_path)
        self.trinity_files = defaultdict(list)
        self.old_omnimesh_files = defaultdict(list) 
        self.infrastructure_files = defaultdict(list)
        self.bloat_files = defaultdict(list)
        self.test_files = defaultdict(list)
        
    def analyze_file(self, filepath):
        """Analyze a file to categorize it"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                
            file_info = {
                'path': str(filepath),
                'size': filepath.stat().st_size,
                'modified': datetime.fromtimestamp(filepath.stat().st_mtime)
            }
            
            # Check for Trinity indicators
            trinity_indicators = [
                'phase 1', 'phase 2', 'phase 3', 'phase 4',
                'trinity convergence', 'lol nexus god tier',
                'pig engine', 'drap module', 'proactive trigger',
                'ultimate trinity architecture'
            ]
            
            old_omnimesh_indicators = [
                'old omnimesh', 'legacy', 'deprecated',
                'ui-flutter', 'ui-solidjs', 'agents-ai',
                'agents-chromeos', 'data-fabric'
            ]
            
            test_indicators = [
                'test_', 'validate_', '_test.', 'test.py',
                'testing', 'validation', 'spec_'
            ]
            
            infrastructure_indicators = [
                'terraform', 'kubernetes', 'docker', 'makefile',
                'go.mod', 'cargo.toml', 'package.json',
                '.tf', '.yaml', '.yml'
            ]
            
            bloat_indicators = [
                'venv/', '__pycache__/', '.git/',
                'node_modules/', 'target/', 'build/',
                '.pyc', '.log', '.tmp'
            ]
            
            # Categorize file
            str_path = str(filepath).lower()
            
            if any(indicator in str_path for indicator in bloat_indicators):
                self.bloat_files['bloat'].append(file_info)
            elif any(indicator in content or indicator in str_path for indicator in test_indicators):
                self.test_files['tests'].append(file_info)
            elif any(indicator in content for indicator in trinity_indicators):
                if 'phase 4' in content:
                    self.trinity_files['phase_4'].append(file_info)
                elif 'phase 3' in content:
                    self.trinity_files['phase_3'].append(file_info)
                elif 'phase 2' in content:
                    self.trinity_files['phase_2'].append(file_info)
                elif 'phase 1' in content:
                    self.trinity_files['phase_1'].append(file_info)
                else:
                    self.trinity_files['general'].append(file_info)
            elif any(indicator in content or indicator in str_path for indicator in old_omnimesh_indicators):
                self.old_omnimesh_files['legacy'].append(file_info)
            elif any(indicator in str_path for indicator in infrastructure_indicators):
                self.infrastructure_files['infra'].append(file_info)
            else:
                # Check directory structure for classification
                if '/backend/' in str_path or '/frontend/' in str_path:
                    self.old_omnimesh_files['ui_components'].append(file_info)
                elif '/core/' in str_path or '/platform/' in str_path:
                    self.trinity_files['core'].append(file_info)
                elif '/scripts/' in str_path or '/automation/' in str_path:
                    self.infrastructure_files['scripts'].append(file_info)
                else:
                    self.infrastructure_files['misc'].append(file_info)
                    
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
    
    def scan_codebase(self):
        """Scan entire codebase"""
        print("🔍 Scanning OMNIMESH codebase...")
        
        for root, dirs, files in os.walk(self.root_path):
            # Skip certain directories entirely
            dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__', 'node_modules', 'target']]
            
            for file in files:
                filepath = Path(root) / file
                self.analyze_file(filepath)
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "="*80)
        print("🎯 OMNIMESH CODEBASE AUDIT REPORT")
        print("="*80)
        
        # Trinity Components Analysis
        print("\n🏗️ TRINITY ARCHITECTURE COMPONENTS:")
        print("-" * 50)
        
        total_trinity_files = 0
        for phase, files in self.trinity_files.items():
            count = len(files)
            total_trinity_files += count
            size_mb = sum(f['size'] for f in files) / (1024*1024)
            print(f"  📁 {phase.upper()}: {count} files ({size_mb:.1f}MB)")
            
            # Show key files
            for file_info in sorted(files, key=lambda x: x['size'], reverse=True)[:3]:
                filename = Path(file_info['path']).name
                size_kb = file_info['size'] / 1024
                print(f"     • {filename} ({size_kb:.1f}KB)")
        
        print(f"\n🎯 TOTAL TRINITY FILES: {total_trinity_files}")
        
        # Old OMNIMESH Analysis
        print("\n🗂️ OLD OMNIMESH COMPONENTS:")
        print("-" * 50)
        
        total_old_files = 0
        for category, files in self.old_omnimesh_files.items():
            count = len(files)
            total_old_files += count
            size_mb = sum(f['size'] for f in files) / (1024*1024)
            print(f"  📁 {category.upper()}: {count} files ({size_mb:.1f}MB)")
        
        print(f"\n🗑️ TOTAL OLD OMNIMESH FILES: {total_old_files}")
        
        # Infrastructure Analysis
        print("\n⚙️ INFRASTRUCTURE COMPONENTS:")
        print("-" * 50)
        
        total_infra_files = 0
        for category, files in self.infrastructure_files.items():
            count = len(files)
            total_infra_files += count
            size_mb = sum(f['size'] for f in files) / (1024*1024)
            print(f"  📁 {category.upper()}: {count} files ({size_mb:.1f}MB)")
        
        print(f"\n🏗️ TOTAL INFRASTRUCTURE FILES: {total_infra_files}")
        
        # Test Files Analysis
        print("\n🧪 TEST & VALIDATION FILES:")
        print("-" * 50)
        
        total_test_files = 0
        for category, files in self.test_files.items():
            count = len(files)
            total_test_files += count
            size_mb = sum(f['size'] for f in files) / (1024*1024)
            print(f"  📁 {category.upper()}: {count} files ({size_mb:.1f}MB)")
        
        print(f"\n🧪 TOTAL TEST FILES: {total_test_files}")
        
        # Recommendations
        print("\n" + "="*80)
        print("💡 CLEANUP RECOMMENDATIONS")
        print("="*80)
        
        print("\n✅ KEEP (Trinity Core):")
        keep_files = []
        for phase, files in self.trinity_files.items():
            for file_info in files:
                if any(important in file_info['path'].lower() for important in [
                    'nexus_orchestrator', 'pig_engine', 'drap_module', 
                    'proactive_trigger', 'drap_orchestration_proxy'
                ]):
                    keep_files.append(file_info['path'])
        
        for file_path in sorted(set(keep_files)):
            print(f"  📄 {Path(file_path).relative_to(self.root_path)}")
        
        print(f"\n🗑️ CONSIDER REMOVING ({total_old_files + len(self.bloat_files.get('bloat', []))} files):")
        print("  • All BACKEND/ and FRONTEND/ directories (old OMNIMESH)")
        print("  • Duplicate CLI implementations")  
        print("  • Unused infrastructure templates")
        print("  • Generated files and build artifacts")
        
        # Summary
        total_files = total_trinity_files + total_old_files + total_infra_files + total_test_files
        trinity_percentage = (total_trinity_files / total_files) * 100 if total_files > 0 else 0
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Files Analyzed: {total_files}")
        print(f"  Trinity Architecture: {total_trinity_files} files ({trinity_percentage:.1f}%)")
        print(f"  Cleanup Potential: {total_old_files + len(self.bloat_files.get('bloat', []))} files")
        
        return {
            'trinity_files': self.trinity_files,
            'old_omnimesh_files': self.old_omnimesh_files,  
            'infrastructure_files': self.infrastructure_files,
            'test_files': self.test_files
        }

def main():
    auditor = CodebaseAuditor('/home/pong/Documents/OMNIMESH')
    auditor.scan_codebase()
    results = auditor.generate_report()
    
    return results

if __name__ == "__main__":
    main()
