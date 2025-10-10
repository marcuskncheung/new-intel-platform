#!/usr/bin/env python3
"""
Security Compliance Scanner
Automated security assessment tool for the Intelligence Platform
"""

import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path

class SecurityScanner:
    def __init__(self, workspace_path):
        self.workspace_path = Path(workspace_path)
        self.vulnerabilities = []
        self.security_score = 0
        self.total_checks = 0
        
    def scan_all(self):
        """Run comprehensive security scan"""
        print("🔍 Starting Security Compliance Scan...")
        print(f"📁 Workspace: {self.workspace_path}")
        print("=" * 60)
        
        # Run all security checks
        self.check_hardcoded_secrets()
        self.check_sql_injection()
        self.check_authentication()
        self.check_encryption()
        self.check_file_security()
        self.check_configuration()
        self.check_dependencies()
        
        # Generate report
        self.generate_report()
        
    def check_hardcoded_secrets(self):
        """Check for hardcoded secrets and credentials"""
        print("🔑 Checking for hardcoded secrets...")
        
        secret_patterns = [
            r'password\s*=\s*["\']([^"\']+)["\']',
            r'secret[_-]?key\s*=\s*["\']([^"\']+)["\']',
            r'api[_-]?key\s*=\s*["\']([^"\']+)["\']',
            r'token\s*=\s*["\']([^"\']+)["\']',
            r'dev-key-please-change',
            r'intelligence-platform-key',
        ]
        
        python_files = list(self.workspace_path.glob("**/*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for line_num, line in enumerate(content.splitlines(), 1):
                    for pattern in secret_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.add_vulnerability(
                                "HARDCODED_SECRET",
                                "HIGH",
                                f"Hardcoded secret found in {file_path}:{line_num}",
                                line.strip()
                            )
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
                
        self.total_checks += 1
        
    def check_sql_injection(self):
        """Check for SQL injection vulnerabilities"""
        print("💉 Checking for SQL injection vulnerabilities...")
        
        sql_patterns = [
            r'execute\s*\(\s*text\s*\(',
            r'query\s*\(\s*["\'][^"\']*%[^"\']*["\']',
            r'\.format\s*\([^)]*\)\s*\)',
            r'f["\'][^"\']*\{[^}]*\}[^"\']*["\']',
        ]
        
        python_files = list(self.workspace_path.glob("**/*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for line_num, line in enumerate(content.splitlines(), 1):
                    for pattern in sql_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.add_vulnerability(
                                "SQL_INJECTION_RISK",
                                "HIGH",
                                f"Potential SQL injection in {file_path}:{line_num}",
                                line.strip()
                            )
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
                
        self.total_checks += 1
        
    def check_authentication(self):
        """Check authentication implementation"""
        print("🔐 Checking authentication security...")
        
        auth_score = 0
        max_auth_score = 5
        
        # Check for password hashing
        if self.check_file_contains("werkzeug.security", "generate_password_hash"):
            auth_score += 1
            print("✅ Password hashing implemented")
        else:
            self.add_vulnerability(
                "WEAK_PASSWORD_STORAGE",
                "HIGH",
                "No password hashing found",
                "Passwords may be stored in plain text"
            )
            
        # Check for Flask-Login
        if self.check_file_contains("flask_login", "LoginManager"):
            auth_score += 1
            print("✅ Flask-Login implemented")
        else:
            self.add_vulnerability(
                "NO_SESSION_MANAGEMENT",
                "MEDIUM",
                "No session management found",
                "User sessions may not be properly managed"
            )
            
        # Check for login required decorators
        if self.check_file_contains("login_required", "@"):
            auth_score += 1
            print("✅ Login protection found")
        else:
            self.add_vulnerability(
                "UNPROTECTED_ROUTES",
                "MEDIUM",
                "No login protection found",
                "Routes may not be properly protected"
            )
            
        self.security_score += (auth_score / max_auth_score) * 20
        self.total_checks += 1
        
    def check_encryption(self):
        """Check encryption implementation"""
        print("🛡️  Checking encryption security...")
        
        encryption_score = 0
        max_encryption_score = 3
        
        # Check for Fernet encryption
        if self.check_file_contains("cryptography.fernet", "Fernet"):
            encryption_score += 1
            print("✅ Fernet encryption found")
        else:
            self.add_vulnerability(
                "NO_ENCRYPTION",
                "HIGH",
                "No encryption implementation found",
                "Sensitive data may not be encrypted"
            )
            
        # Check for proper key derivation
        if self.check_file_contains("PBKDF2HMAC", "kdf"):
            encryption_score += 1
            print("✅ Key derivation function found")
        else:
            self.add_vulnerability(
                "WEAK_KEY_DERIVATION",
                "MEDIUM",
                "No proper key derivation found",
                "Encryption keys may be weak"
            )
            
        # Check for random salt usage
        if self.check_file_contains("intelligence_platform_salt", "salt"):
            self.add_vulnerability(
                "FIXED_SALT",
                "MEDIUM",
                "Fixed salt found",
                "Should use random salts for better security"
            )
        else:
            encryption_score += 1
            print("✅ No fixed salt detected")
            
        self.security_score += (encryption_score / max_encryption_score) * 20
        self.total_checks += 1
        
    def check_file_security(self):
        """Check file handling security"""
        print("📁 Checking file security...")
        
        # Check for file upload validation
        upload_patterns = [
            r'allowed_file',
            r'secure_filename',
            r'werkzeug\.utils\.secure_filename',
        ]
        
        has_upload_security = False
        for pattern in upload_patterns:
            if self.check_pattern_in_files(pattern):
                has_upload_security = True
                break
                
        if not has_upload_security:
            self.add_vulnerability(
                "INSECURE_FILE_UPLOAD",
                "MEDIUM",
                "No file upload validation found",
                "File uploads may not be properly validated"
            )
            
        self.total_checks += 1
        
    def check_configuration(self):
        """Check configuration security"""
        print("⚙️  Checking configuration security...")
        
        # Check for debug mode
        if self.check_file_contains("debug=True", "app.run"):
            self.add_vulnerability(
                "DEBUG_MODE_ENABLED",
                "MEDIUM",
                "Debug mode may be enabled",
                "Debug mode should be disabled in production"
            )
            
        # Check for HTTPS configuration
        if not self.check_file_contains("ssl_context", "https"):
            self.add_vulnerability(
                "NO_HTTPS",
                "HIGH",
                "No HTTPS configuration found",
                "Application should use HTTPS in production"
            )
            
        self.total_checks += 1
        
    def check_dependencies(self):
        """Check for known vulnerable dependencies"""
        print("📦 Checking dependencies...")
        
        requirements_file = self.workspace_path / "requirements_production.txt"
        if requirements_file.exists():
            print("✅ Requirements file found")
            # Here you would integrate with safety or other vulnerability databases
        else:
            self.add_vulnerability(
                "NO_DEPENDENCY_MANAGEMENT",
                "LOW",
                "No requirements file found",
                "Dependencies should be properly managed"
            )
            
        self.total_checks += 1
        
    def check_file_contains(self, pattern1, pattern2=None):
        """Check if any Python file contains the given patterns"""
        python_files = list(self.workspace_path.glob("**/*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if pattern1 in content:
                        if pattern2 is None or pattern2 in content:
                            return True
            except Exception:
                continue
        return False
        
    def check_pattern_in_files(self, pattern):
        """Check if regex pattern exists in any Python file"""
        python_files = list(self.workspace_path.glob("**/*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if re.search(pattern, content, re.IGNORECASE):
                        return True
            except Exception:
                continue
        return False
        
    def add_vulnerability(self, vuln_type, severity, description, details):
        """Add a vulnerability to the list"""
        self.vulnerabilities.append({
            'type': vuln_type,
            'severity': severity,
            'description': description,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        severity_emoji = {
            'HIGH': '🚨',
            'MEDIUM': '⚠️',
            'LOW': '⚡'
        }
        
        print(f"{severity_emoji.get(severity, '❓')} {severity}: {description}")
        
    def calculate_security_score(self):
        """Calculate overall security score"""
        if self.total_checks == 0:
            return 0
            
        # Deduct points for vulnerabilities
        high_vulns = len([v for v in self.vulnerabilities if v['severity'] == 'HIGH'])
        medium_vulns = len([v for v in self.vulnerabilities if v['severity'] == 'MEDIUM'])
        low_vulns = len([v for v in self.vulnerabilities if v['severity'] == 'LOW'])
        
        deduction = (high_vulns * 20) + (medium_vulns * 10) + (low_vulns * 5)
        base_score = 100
        
        return max(0, base_score - deduction)
        
    def generate_report(self):
        """Generate security assessment report"""
        print("\n" + "=" * 60)
        print("📊 SECURITY ASSESSMENT REPORT")
        print("=" * 60)
        
        security_score = self.calculate_security_score()
        
        print(f"🏆 Security Score: {security_score}/100")
        print(f"🔍 Total Checks: {self.total_checks}")
        print(f"🚨 Vulnerabilities Found: {len(self.vulnerabilities)}")
        
        # Vulnerability summary
        high_count = len([v for v in self.vulnerabilities if v['severity'] == 'HIGH'])
        medium_count = len([v for v in self.vulnerabilities if v['severity'] == 'MEDIUM'])
        low_count = len([v for v in self.vulnerabilities if v['severity'] == 'LOW'])
        
        print(f"\n📋 Vulnerability Breakdown:")
        print(f"   🚨 HIGH:   {high_count}")
        print(f"   ⚠️  MEDIUM: {medium_count}")
        print(f"   ⚡ LOW:    {low_count}")
        
        # Security grade
        if security_score >= 90:
            grade = "A"
            grade_emoji = "🟢"
        elif security_score >= 80:
            grade = "B"
            grade_emoji = "🟡"
        elif security_score >= 70:
            grade = "C"
            grade_emoji = "🟠"
        else:
            grade = "F"
            grade_emoji = "🔴"
            
        print(f"\n{grade_emoji} Security Grade: {grade}")
        
        # Recommendations
        print(f"\n📝 Recommendations:")
        if high_count > 0:
            print("   1. Address HIGH severity vulnerabilities immediately")
        if medium_count > 0:
            print("   2. Plan to fix MEDIUM severity issues in next sprint")
        if security_score < 80:
            print("   3. Implement comprehensive security testing")
        if security_score < 70:
            print("   4. Consider security code review by expert")
            
        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'security_score': security_score,
            'grade': grade,
            'total_checks': self.total_checks,
            'vulnerabilities': self.vulnerabilities,
            'summary': {
                'high_severity': high_count,
                'medium_severity': medium_count,
                'low_severity': low_count
            }
        }
        
        report_file = self.workspace_path / "security_scan_results.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n💾 Detailed report saved to: {report_file}")
        print("\n🔧 Run this scanner regularly to maintain security compliance!")

def main():
    """Main function to run security scan"""
    workspace_path = os.path.dirname(os.path.abspath(__file__))
    scanner = SecurityScanner(workspace_path)
    scanner.scan_all()

if __name__ == "__main__":
    main()
