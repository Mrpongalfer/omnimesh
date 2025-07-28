#!/usr/bin/env python3
"""
COMPLETE OMNIMESH AUDIT - EVERY SINGLE FILE AND DIRECTORY
========================================================

This script audits EVERY file and directory in the workspace to ensure
we haven't missed ANY valuable components, including:
- Agent Exwork
- UMCC
- ALL Backend components  
- ALL Frontend components
- Automation systems
- EVERYTHING else
"""

import os
from pathlib import Path
import json
from collections import defaultdict

class CompleteOmnimeshAudit:
    def __init__(self, workspace_root):
        self.workspace_root = Path(workspace_root)
        self.trinity_dir = self.workspace_root / "trinity"
        
        # Track everything
        self.all_files = {}
        self.all_directories = {}
        self.missing_components = {}
        self.critical_findings = []
        
    def audit_everything(self):
        """Audit EVERY single file and directory"""
        print("🔍 COMPLETE OMNIMESH AUDIT - CHECKING EVERYTHING")
        print("=" * 70)
        
        # Get EVERYTHING in workspace
        print("📊 SCANNING ALL FILES AND DIRECTORIES...")
        
        for root, dirs, files in os.walk(self.workspace_root):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.workspace_root)
            
            # Skip trinity directory for now (we'll audit it separately)
            if str(rel_root).startswith('trinity'):
                continue
                
            if files:
                self.all_files[str(rel_root)] = files
            if dirs:
                self.all_directories[str(rel_root)] = dirs
        
        print(f"   📁 Found {len(self.all_directories)} directories with content")
        print(f"   📄 Found {len(self.all_files)} directories with files")
        
        return self.detailed_audit()
    
    def detailed_audit(self):
        """Detailed audit of every component"""
        audit_results = {}
        
        # 1. AGENT EXWORK AUDIT
        audit_results['agent_exwork'] = self.audit_agent_exwork()
        
        # 2. UMCC AUDIT  
        audit_results['umcc'] = self.audit_umcc()
        
        # 3. COMPLETE BACKEND AUDIT
        audit_results['backend_complete'] = self.audit_backend_complete()
        
        # 4. COMPLETE FRONTEND AUDIT
        audit_results['frontend_complete'] = self.audit_frontend_complete()
        
        # 5. AUTOMATION SYSTEMS AUDIT
        audit_results['automation_systems'] = self.audit_automation_systems()
        
        # 6. CORE DIRECTORY AUDIT
        audit_results['core_systems'] = self.audit_core_systems()
        
        # 7. ROOT LEVEL FILES AUDIT
        audit_results['root_files'] = self.audit_root_files()
        
        # 8. SPECIALIZED DIRECTORIES AUDIT
        audit_results['specialized_dirs'] = self.audit_specialized_directories()
        
        # 9. TRINITY COMPARISON
        audit_results['trinity_coverage'] = self.audit_trinity_coverage()
        
        return audit_results
    
    def audit_agent_exwork(self):
        """Audit for Agent Exwork components"""
        print("\n🤖 AGENT EXWORK AUDIT:")
        print("-" * 40)
        
        exwork_findings = {
            'found_components': [],
            'missing_in_trinity': [],
            'status': 'searching'
        }
        
        # Search for exwork references
        exwork_patterns = ['exwork', 'ex_work', 'Exwork', 'EX_WORK']
        
        for dir_path, files in self.all_files.items():
            for file in files:
                file_lower = file.lower()
                for pattern in exwork_patterns:
                    if pattern.lower() in file_lower:
                        component = f"{dir_path}/{file}"
                        exwork_findings['found_components'].append(component)
                        print(f"   🔍 FOUND: {component}")
        
        # Check specific locations
        exwork_locations = [
            'core/agents',
            'BACKEND/agents-ai', 
            'core/bin',
            'interfaces/cli'
        ]
        
        for location in exwork_locations:
            location_path = self.workspace_root / location
            if location_path.exists():
                for file in location_path.glob("**/*"):
                    if file.is_file():
                        content_check = str(file).lower()
                        for pattern in exwork_patterns:
                            if pattern.lower() in content_check:
                                exwork_findings['found_components'].append(str(file.relative_to(self.workspace_root)))
                                print(f"   🔍 FOUND: {file.relative_to(self.workspace_root)}")
        
        # Check if in Trinity
        trinity_exwork = []
        if self.trinity_dir.exists():
            for file in self.trinity_dir.glob("**/*"):
                if file.is_file():
                    file_content = str(file).lower()
                    for pattern in exwork_patterns:
                        if pattern.lower() in file_content:
                            trinity_exwork.append(str(file.relative_to(self.trinity_dir)))
        
        print(f"   📊 Exwork components found: {len(exwork_findings['found_components'])}")
        print(f"   📊 Exwork in Trinity: {len(trinity_exwork)}")
        
        if len(exwork_findings['found_components']) > len(trinity_exwork):
            print("   🚨 EXWORK COMPONENTS MISSING FROM TRINITY!")
        
        exwork_findings['trinity_components'] = trinity_exwork
        exwork_findings['status'] = 'found' if exwork_findings['found_components'] else 'not_found'
        
        return exwork_findings
    
    def audit_umcc(self):
        """Audit for UMCC components"""
        print("\n🏛️ UMCC AUDIT:")
        print("-" * 40)
        
        umcc_findings = {
            'found_components': [],
            'missing_in_trinity': [],
            'status': 'searching'
        }
        
        # Search for UMCC references
        umcc_patterns = ['umcc', 'UMCC', 'umcc_', 'UMCC_']
        
        for dir_path, files in self.all_files.items():
            for file in files:
                file_lower = file.lower()
                for pattern in umcc_patterns:
                    if pattern.lower() in file_lower:
                        component = f"{dir_path}/{file}"
                        umcc_findings['found_components'].append(component)
                        print(f"   🔍 FOUND: {component}")
        
        # Check for UMCC in file contents (sample key files)
        key_files_to_check = [
            'core/nexus_orchestrator.py',
            'nexus_cli.py',
            'omni-c2-center.py'
        ]
        
        for file_path in key_files_to_check:
            full_path = self.workspace_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in umcc_patterns:
                            if pattern in content:
                                umcc_findings['found_components'].append(f"{file_path} (content)")
                                print(f"   🔍 FOUND in {file_path}: UMCC references in content")
                                break
                except Exception as e:
                    print(f"   ⚠️ Could not read {file_path}: {e}")
        
        # Check Trinity coverage
        trinity_umcc = []
        if self.trinity_dir.exists():
            for file in self.trinity_dir.glob("**/*"):
                if file.is_file():
                    file_name = str(file.name).lower()
                    for pattern in umcc_patterns:
                        if pattern.lower() in file_name:
                            trinity_umcc.append(str(file.relative_to(self.trinity_dir)))
        
        print(f"   📊 UMCC components found: {len(umcc_findings['found_components'])}")
        print(f"   📊 UMCC in Trinity: {len(trinity_umcc)}")
        
        umcc_findings['trinity_components'] = trinity_umcc
        umcc_findings['status'] = 'found' if umcc_findings['found_components'] else 'not_found'
        
        return umcc_findings
    
    def audit_backend_complete(self):
        """Complete audit of BACKEND directory"""
        print("\n🦀 COMPLETE BACKEND AUDIT:")
        print("-" * 40)
        
        backend_dir = self.workspace_root / "BACKEND"
        backend_audit = {
            'directories': {},
            'total_files': 0,
            'missing_from_trinity': [],
            'status': 'not_found'
        }
        
        if backend_dir.exists():
            backend_audit['status'] = 'found'
            
            # Audit each subdirectory
            for item in backend_dir.iterdir():
                if item.is_dir():
                    files = []
                    file_count = 0
                    for file in item.glob("**/*"):
                        if file.is_file():
                            rel_path = file.relative_to(backend_dir)
                            files.append(str(rel_path))
                            file_count += 1
                    
                    backend_audit['directories'][item.name] = {
                        'file_count': file_count,
                        'files': files[:10] if len(files) > 10 else files  # Sample first 10
                    }
                    backend_audit['total_files'] += file_count
                    
                    print(f"   📂 {item.name}/: {file_count} files")
                    if file_count > 0:
                        print(f"      Sample files: {', '.join(files[:3])}")
                elif item.is_file():
                    backend_audit['total_files'] += 1
                    print(f"   📄 {item.name}")
            
            print(f"   📊 Total BACKEND files: {backend_audit['total_files']}")
            
            # Check Trinity coverage
            trinity_backend_files = 0
            if self.trinity_dir.exists():
                trinity_backend_files = len(list(self.trinity_dir.glob("**/*")))
            
            if backend_audit['total_files'] > trinity_backend_files * 0.1:  # If backend has >10% of trinity files
                print("   🚨 BACKEND may have significant components not fully integrated!")
        else:
            print("   ❌ BACKEND directory not found")
        
        return backend_audit
    
    def audit_frontend_complete(self):
        """Complete audit of FRONTEND directory"""
        print("\n🎨 COMPLETE FRONTEND AUDIT:")
        print("-" * 40)
        
        frontend_dir = self.workspace_root / "FRONTEND"
        frontend_audit = {
            'directories': {},
            'total_files': 0,
            'missing_from_trinity': [],
            'status': 'not_found'
        }
        
        if frontend_dir.exists():
            frontend_audit['status'] = 'found'
            
            # Audit each subdirectory
            for item in frontend_dir.iterdir():
                if item.is_dir():
                    files = []
                    file_count = 0
                    for file in item.glob("**/*"):
                        if file.is_file():
                            rel_path = file.relative_to(frontend_dir)
                            files.append(str(rel_path))
                            file_count += 1
                    
                    frontend_audit['directories'][item.name] = {
                        'file_count': file_count,
                        'files': files[:10] if len(files) > 10 else files
                    }
                    frontend_audit['total_files'] += file_count
                    
                    print(f"   📂 {item.name}/: {file_count} files")
                    if file_count > 0:
                        print(f"      Sample files: {', '.join(files[:3])}")
                elif item.is_file():
                    frontend_audit['total_files'] += 1
                    print(f"   📄 {item.name}")
            
            print(f"   📊 Total FRONTEND files: {frontend_audit['total_files']}")
            
            # Check Trinity web-ui coverage
            trinity_webui = self.trinity_dir / "web-ui"
            trinity_webui_files = 0
            if trinity_webui.exists():
                trinity_webui_files = len(list(trinity_webui.glob("**/*")))
            
            print(f"   📊 Trinity web-ui files: {trinity_webui_files}")
            
            if frontend_audit['total_files'] > trinity_webui_files:
                print("   🚨 FRONTEND has more files than Trinity web-ui!")
        else:
            print("   ❌ FRONTEND directory not found")
        
        return frontend_audit
    
    def audit_automation_systems(self):
        """Audit ALL automation systems"""
        print("\n🤖 AUTOMATION SYSTEMS AUDIT:")
        print("-" * 40)
        
        automation_audit = {
            'automation_dir': {},
            'scripts_dir': {},
            'root_automation': [],
            'total_automation_files': 0,
            'status': 'searching'
        }
        
        # Check automation/ directory
        automation_dir = self.workspace_root / "automation"
        if automation_dir.exists():
            automation_audit['status'] = 'found'
            files = []
            for file in automation_dir.glob("**/*"):
                if file.is_file():
                    rel_path = file.relative_to(automation_dir)
                    files.append(str(rel_path))
            
            automation_audit['automation_dir'] = {
                'file_count': len(files),
                'files': files
            }
            automation_audit['total_automation_files'] += len(files)
            print(f"   📂 automation/: {len(files)} files")
            for file in files:
                print(f"      • {file}")
        
        # Check scripts/ directory  
        scripts_dir = self.workspace_root / "scripts"
        if scripts_dir.exists():
            files = []
            for file in scripts_dir.glob("**/*"):
                if file.is_file():
                    rel_path = file.relative_to(scripts_dir)
                    files.append(str(rel_path))
            
            automation_audit['scripts_dir'] = {
                'file_count': len(files),
                'files': files
            }
            automation_audit['total_automation_files'] += len(files)
            print(f"   📂 scripts/: {len(files)} files")
            for file in files[:10]:  # Show first 10
                print(f"      • {file}")
        
        # Check root-level automation files
        root_automation_patterns = ['.sh', '.py', 'deploy', 'install', 'setup', 'bootstrap']
        for file in self.workspace_root.glob("*"):
            if file.is_file():
                for pattern in root_automation_patterns:
                    if pattern in file.name.lower():
                        automation_audit['root_automation'].append(file.name)
                        print(f"   📄 Root automation: {file.name}")
                        break
        
        automation_audit['total_automation_files'] += len(automation_audit['root_automation'])
        
        print(f"   📊 Total automation files: {automation_audit['total_automation_files']}")
        
        # Check Trinity coverage
        trinity_automation_files = 0
        trinity_dirs = ['automation', 'deployment-scripts', 'scripts']
        for dir_name in trinity_dirs:
            trinity_dir_path = self.trinity_dir / dir_name
            if trinity_dir_path.exists():
                trinity_automation_files += len(list(trinity_dir_path.glob("**/*")))
        
        print(f"   📊 Trinity automation files: {trinity_automation_files}")
        
        if automation_audit['total_automation_files'] > trinity_automation_files:
            print("   🚨 MISSING AUTOMATION COMPONENTS IN TRINITY!")
        
        return automation_audit
    
    def audit_core_systems(self):
        """Audit core/ directory completely"""
        print("\n🏗️ CORE SYSTEMS AUDIT:")
        print("-" * 40)
        
        core_dir = self.workspace_root / "core"
        core_audit = {
            'directories': {},
            'total_files': 0,
            'status': 'not_found'
        }
        
        if core_dir.exists():
            core_audit['status'] = 'found'
            
            for item in core_dir.iterdir():
                if item.is_dir():
                    files = list(item.glob("**/*"))
                    file_count = sum(1 for f in files if f.is_file())
                    
                    core_audit['directories'][item.name] = file_count
                    core_audit['total_files'] += file_count
                    
                    print(f"   📂 core/{item.name}/: {file_count} files")
                elif item.is_file():
                    core_audit['total_files'] += 1
                    print(f"   📄 core/{item.name}")
            
            print(f"   📊 Total core files: {core_audit['total_files']}")
            
            # Check Trinity core coverage
            trinity_core = self.trinity_dir / "core"
            trinity_core_files = 0
            if trinity_core.exists():
                trinity_core_files = len(list(trinity_core.glob("**/*")))
            
            print(f"   📊 Trinity core files: {trinity_core_files}")
        
        return core_audit
    
    def audit_root_files(self):
        """Audit all root-level files"""
        print("\n📄 ROOT FILES AUDIT:")
        print("-" * 40)
        
        root_files = {
            'python_files': [],
            'shell_scripts': [],
            'config_files': [],
            'other_files': [],
            'total_count': 0
        }
        
        for file in self.workspace_root.glob("*"):
            if file.is_file():
                root_files['total_count'] += 1
                
                if file.suffix == '.py':
                    root_files['python_files'].append(file.name)
                    print(f"   🐍 {file.name}")
                elif file.suffix == '.sh':
                    root_files['shell_scripts'].append(file.name)
                    print(f"   📜 {file.name}")
                elif file.suffix in ['.json', '.toml', '.yaml', '.yml', '.txt', '.md']:
                    root_files['config_files'].append(file.name)
                    print(f"   ⚙️ {file.name}")
                else:
                    root_files['other_files'].append(file.name)
                    print(f"   📄 {file.name}")
        
        print(f"   📊 Total root files: {root_files['total_count']}")
        
        return root_files
    
    def audit_specialized_directories(self):
        """Audit specialized directories"""
        print("\n🎯 SPECIALIZED DIRECTORIES AUDIT:")
        print("-" * 40)
        
        specialized_dirs = [
            'interfaces', 'platform', 'kubernetes', 'infrastructure',
            'config', 'docs', 'tests'
        ]
        
        specialized_audit = {}
        
        for dir_name in specialized_dirs:
            dir_path = self.workspace_root / dir_name
            if dir_path.exists():
                file_count = sum(1 for f in dir_path.glob("**/*") if f.is_file())
                specialized_audit[dir_name] = file_count
                print(f"   📂 {dir_name}/: {file_count} files")
            else:
                specialized_audit[dir_name] = 0
                print(f"   ❌ {dir_name}/: Not found")
        
        return specialized_audit
    
    def audit_trinity_coverage(self):
        """Compare Trinity coverage against everything else"""
        print("\n🔍 TRINITY COVERAGE ANALYSIS:")
        print("-" * 40)
        
        # Count all non-Trinity files
        total_workspace_files = 0
        for root, dirs, files in os.walk(self.workspace_root):
            if 'trinity' not in root:
                total_workspace_files += len(files)
        
        # Count Trinity files
        trinity_files = 0
        if self.trinity_dir.exists():
            trinity_files = sum(1 for f in self.trinity_dir.glob("**/*") if f.is_file())
        
        coverage_percentage = (trinity_files / total_workspace_files * 100) if total_workspace_files > 0 else 0
        
        print(f"   📊 Total workspace files (non-Trinity): {total_workspace_files}")
        print(f"   📊 Trinity files: {trinity_files}")
        print(f"   📊 Coverage: {coverage_percentage:.1f}%")
        
        if coverage_percentage < 50:
            print("   🚨 TRINITY COVERAGE IS LOW - MAJOR COMPONENTS MISSING!")
        
        return {
            'total_workspace_files': total_workspace_files,
            'trinity_files': trinity_files,
            'coverage_percentage': coverage_percentage
        }

def main():
    workspace = "/home/pong/Documents/OMNIMESH"
    auditor = CompleteOmnimeshAudit(workspace)
    
    print("🎯 COMPLETE OMNIMESH AUDIT - CHECKING EVERYTHING!")
    print("=" * 80)
    
    audit_results = auditor.audit_everything()
    
    # Generate summary report
    print("\n📋 COMPLETE AUDIT SUMMARY:")
    print("=" * 50)
    
    critical_findings = []
    
    # Agent Exwork findings
    if audit_results['agent_exwork']['status'] == 'found':
        if len(audit_results['agent_exwork']['found_components']) > len(audit_results['agent_exwork']['trinity_components']):
            critical_findings.append("🚨 AGENT EXWORK components missing from Trinity!")
    
    # UMCC findings  
    if audit_results['umcc']['status'] == 'found':
        if len(audit_results['umcc']['found_components']) > len(audit_results['umcc']['trinity_components']):
            critical_findings.append("🚨 UMCC components missing from Trinity!")
    
    # Backend findings
    if audit_results['backend_complete']['total_files'] > 50:
        critical_findings.append(f"🚨 BACKEND has {audit_results['backend_complete']['total_files']} files - check integration!")
    
    # Frontend findings
    if audit_results['frontend_complete']['total_files'] > 10:
        critical_findings.append(f"🚨 FRONTEND has {audit_results['frontend_complete']['total_files']} files - check integration!")
    
    # Automation findings
    if audit_results['automation_systems']['total_automation_files'] > 20:
        critical_findings.append(f"🚨 Found {audit_results['automation_systems']['total_automation_files']} automation files!")
    
    # Trinity coverage
    if audit_results['trinity_coverage']['coverage_percentage'] < 50:
        critical_findings.append("🚨 Trinity coverage is LOW - major components missing!")
    
    print("\n🚨 CRITICAL FINDINGS:")
    for finding in critical_findings:
        print(f"   {finding}")
    
    if not critical_findings:
        print("   ✅ No critical issues found - integration appears complete!")
    
    # Save audit results
    audit_file = Path(workspace) / "COMPLETE_OMNIMESH_AUDIT.json"
    with open(audit_file, 'w') as f:
        json.dump(audit_results, f, indent=2, default=str)
    
    print(f"\n📋 Complete audit saved to: {audit_file}")
    
    return audit_results

if __name__ == "__main__":
    main()
