#!/usr/bin/env python3
"""
Comprehensive Status Tests for IDF Creator
Tests the health and readiness of all system components
"""

import os
import sys
import json
import importlib
from pathlib import Path
from typing import Dict, List, Optional
import traceback

# Try importing requests for API tests
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class StatusChecker:
    """Comprehensive status checker for IDF Creator system"""
    
    def __init__(self):
        self.results = {
            'api': {},
            'components': {},
            'files': {},
            'dependencies': {},
            'directories': {},
            'overall': {'status': 'unknown', 'issues': []}
        }
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title.center(70)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    def print_result(self, name: str, status: bool, message: str = "", details: str = ""):
        """Print a formatted test result"""
        status_symbol = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.RED}✗{Colors.RESET}"
        status_text = f"{Colors.GREEN}PASS{Colors.RESET}" if status else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"{status_symbol} {name:.<50} {status_text}")
        if message:
            print(f"   {message}")
        if details:
            print(f"   {details}")
        return status
    
    def check_api_health(self, base_url: str = "http://localhost:5001") -> Dict:
        """Check API health endpoint"""
        results = {}
        
        try:
            if not HAS_REQUESTS:
                results['requests_available'] = False
                results['message'] = "requests library not available - skipping API tests"
                return results
            
            url = f"{base_url}/api/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results['status'] = 'healthy'
                results['service'] = data.get('service', 'Unknown')
                results['version'] = data.get('version', 'Unknown')
                results['available'] = True
            else:
                results['status'] = 'unhealthy'
                results['available'] = False
                results['error'] = f"HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            results['available'] = False
            results['status'] = 'not_running'
            results['message'] = "API server is not running"
        except Exception as e:
            results['available'] = False
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def check_component_imports(self) -> Dict:
        """Check if all core components can be imported"""
        components = {
            'main': 'main',
            'idf_generator': 'src.idf_generator',
            'professional_idf_generator': 'src.professional_idf_generator',
            'location_fetcher': 'src.location_fetcher',
            'enhanced_location_fetcher': 'src.enhanced_location_fetcher',
            'document_parser': 'src.document_parser',
            'building_estimator': 'src.building_estimator',
            'nlp_building_parser': 'src.nlp_building_parser',
            'config_manager': 'src.utils.config_manager',
            'nrel_fetcher': 'src.nrel_fetcher',
            'osm_fetcher': 'src.osm_fetcher',
        }
        
        results = {}
        for name, module_path in components.items():
            try:
                module = importlib.import_module(module_path)
                results[name] = {
                    'imported': True,
                    'has_classes': len([x for x in dir(module) if not x.startswith('_')]) > 0
                }
            except Exception as e:
                results[name] = {
                    'imported': False,
                    'error': str(e)
                }
        
        return results
    
    def check_component_initialization(self) -> Dict:
        """Check if core components can be initialized"""
        results = {}
        
        # Check IDFCreator initialization
        try:
            from main import IDFCreator
            creator = IDFCreator(enhanced=True, professional=True)
            results['idf_creator'] = {
                'initialized': True,
                'enhanced_mode': creator.enhanced,
                'professional_mode': creator.professional
            }
        except Exception as e:
            results['idf_creator'] = {
                'initialized': False,
                'error': str(e)
            }
        
        # Check LocationFetcher
        try:
            from src.location_fetcher import LocationFetcher
            fetcher = LocationFetcher()
            results['location_fetcher'] = {'initialized': True}
        except Exception as e:
            results['location_fetcher'] = {
                'initialized': False,
                'error': str(e)
            }
        
        # Check EnhancedLocationFetcher
        try:
            from src.enhanced_location_fetcher import EnhancedLocationFetcher
            enhanced_fetcher = EnhancedLocationFetcher()
            results['enhanced_location_fetcher'] = {'initialized': True}
        except Exception as e:
            results['enhanced_location_fetcher'] = {
                'initialized': False,
                'error': str(e)
            }
        
        # Check IDFGenerator
        try:
            from src.idf_generator import IDFGenerator
            generator = IDFGenerator()
            results['idf_generator'] = {'initialized': True}
        except Exception as e:
            results['idf_generator'] = {
                'initialized': False,
                'error': str(e)
            }
        
        # Check ProfessionalIDFGenerator
        try:
            from src.professional_idf_generator import ProfessionalIDFGenerator
            prof_generator = ProfessionalIDFGenerator()
            results['professional_idf_generator'] = {'initialized': True}
        except Exception as e:
            results['professional_idf_generator'] = {
                'initialized': False,
                'error': str(e)
            }
        
        return results
    
    def check_config_files(self) -> Dict:
        """Check if required configuration files exist"""
        files = {
            'config.yaml': 'Main configuration file',
            'requirements.txt': 'Python dependencies',
        }
        
        results = {}
        for filename, description in files.items():
            path = Path(filename)
            exists = path.exists()
            results[filename] = {
                'exists': exists,
                'description': description
            }
            if exists:
                try:
                    size = path.stat().st_size
                    results[filename]['size'] = size
                    results[filename]['readable'] = True
                except Exception as e:
                    results[filename]['readable'] = False
                    results[filename]['error'] = str(e)
        
        return results
    
    def check_directories(self) -> Dict:
        """Check if required directories exist and are writable"""
        directories = {
            'artifacts/desktop_files/idf': 'IDF output directory',
            'artifacts/desktop_files/weather': 'Weather files directory',
            'output': 'Output directory',
            'src': 'Source code directory',
        }
        
        results = {}
        for dir_path, description in directories.items():
            path = Path(dir_path)
            exists = path.exists()
            is_dir = path.is_dir() if exists else False
            results[dir_path] = {
                'exists': exists,
                'is_directory': is_dir,
                'description': description
            }
            
            if exists and is_dir:
                # Check if writable
                try:
                    test_file = path / '.write_test'
                    test_file.touch()
                    test_file.unlink()
                    results[dir_path]['writable'] = True
                except Exception:
                    results[dir_path]['writable'] = False
        
        return results
    
    def check_dependencies(self) -> Dict:
        """Check if required Python packages are installed"""
        required_packages = [
            'requests',
            'geopy',
            'pillow',
            'PyPDF2',
            'pdf2image',
            'opencv-python',
            'pandas',
            'numpy',
            'shapely',
            'yaml',
            'flask',
            'flask_cors',
        ]
        
        optional_packages = [
            'openai',
            'anthropic',
        ]
        
        results = {'required': {}, 'optional': {}}
        
        for package in required_packages:
            try:
                # Handle special cases
                if package == 'yaml':
                    importlib.import_module('yaml')
                elif package == 'opencv-python':
                    importlib.import_module('cv2')
                elif package == 'flask_cors':
                    importlib.import_module('flask_cors')
                elif package == 'pdf2image':
                    importlib.import_module('pdf2image')
                else:
                    importlib.import_module(package)
                results['required'][package] = {'installed': True}
            except ImportError:
                results['required'][package] = {'installed': False}
        
        for package in optional_packages:
            try:
                importlib.import_module(package)
                results['optional'][package] = {'installed': True}
            except ImportError:
                results['optional'][package] = {'installed': False}
        
        return results
    
    def check_weather_files(self) -> Dict:
        """Check if weather files are available"""
        weather_dir = Path('artifacts/desktop_files/weather')
        results = {
            'directory_exists': weather_dir.exists(),
            'files': []
        }
        
        if weather_dir.exists():
            epw_files = list(weather_dir.glob('*.epw'))
            results['file_count'] = len(epw_files)
            for epw_file in epw_files:
                file_info = {
                    'name': epw_file.name,
                    'size': epw_file.stat().st_size,
                    'readable': True
                }
                results['files'].append(file_info)
        else:
            results['file_count'] = 0
        
        return results
    
    def check_output_files(self) -> Dict:
        """Check for existing IDF output files"""
        output_dirs = [
            Path('artifacts/desktop_files/idf'),
            Path('output'),
        ]
        
        results = {
            'total_files': 0,
            'files': []
        }
        
        for output_dir in output_dirs:
            if output_dir.exists():
                idf_files = list(output_dir.glob('*.idf'))
                results['total_files'] += len(idf_files)
                for idf_file in idf_files[:10]:  # Limit to first 10
                    file_info = {
                        'name': idf_file.name,
                        'path': str(idf_file),
                        'size': idf_file.stat().st_size,
                    }
                    results['files'].append(file_info)
        
        return results
    
    def run_all_checks(self, check_api: bool = True) -> Dict:
        """Run all status checks"""
        self.print_header("IDF Creator System Status Check")
        
        # API Health Check
        if check_api:
            self.print_header("API Status")
            api_results = self.check_api_health()
            self.results['api'] = api_results
            
            if api_results.get('available'):
                self.print_result(
                    "API Health Endpoint",
                    True,
                    f"Service: {api_results.get('service')}, Version: {api_results.get('version')}"
                )
            else:
                self.print_result(
                    "API Health Endpoint",
                    False,
                    api_results.get('message', api_results.get('error', 'Unknown error'))
                )
        
        # Component Imports
        self.print_header("Component Imports")
        import_results = self.check_component_imports()
        self.results['components']['imports'] = import_results
        
        for component, result in import_results.items():
            if result.get('imported'):
                self.print_result(component, True)
            else:
                self.print_result(component, False, result.get('error', 'Import failed'))
        
        # Component Initialization
        self.print_header("Component Initialization")
        init_results = self.check_component_initialization()
        self.results['components']['initialization'] = init_results
        
        for component, result in init_results.items():
            if result.get('initialized'):
                details = ""
                if 'enhanced_mode' in result:
                    details = f"Enhanced: {result['enhanced_mode']}, Professional: {result['professional_mode']}"
                self.print_result(component, True, details)
            else:
                self.print_result(component, False, result.get('error', 'Initialization failed'))
        
        # Configuration Files
        self.print_header("Configuration Files")
        config_results = self.check_config_files()
        self.results['files']['config'] = config_results
        
        for filename, result in config_results.items():
            if result.get('exists') and result.get('readable'):
                size_kb = result.get('size', 0) / 1024
                self.print_result(filename, True, f"{size_kb:.1f} KB")
            else:
                self.print_result(filename, False, result.get('description', ''))
        
        # Directories
        self.print_header("Directory Structure")
        dir_results = self.check_directories()
        self.results['directories'] = dir_results
        
        for dir_path, result in dir_results.items():
            if result.get('exists') and result.get('is_directory'):
                writable = "writable" if result.get('writable') else "read-only"
                self.print_result(dir_path, True, writable)
            else:
                self.print_result(dir_path, False, result.get('description', ''))
        
        # Dependencies
        self.print_header("Python Dependencies")
        dep_results = self.check_dependencies()
        self.results['dependencies'] = dep_results
        
        required_missing = []
        for package, result in dep_results['required'].items():
            if result.get('installed'):
                self.print_result(f"Required: {package}", True)
            else:
                self.print_result(f"Required: {package}", False)
                required_missing.append(package)
        
        for package, result in dep_results['optional'].items():
            if result.get('installed'):
                self.print_result(f"Optional: {package}", True, "installed")
            else:
                self.print_result(f"Optional: {package}", False, "not installed (optional)")
        
        # Weather Files
        self.print_header("Weather Files")
        weather_results = self.check_weather_files()
        self.results['files']['weather'] = weather_results
        
        if weather_results.get('directory_exists'):
            file_count = weather_results.get('file_count', 0)
            self.print_result("Weather Directory", True, f"{file_count} EPW files found")
            for file_info in weather_results.get('files', [])[:5]:  # Show first 5
                size_kb = file_info['size'] / 1024
                self.print_result(f"  {file_info['name']}", True, f"{size_kb:.1f} KB")
        else:
            self.print_result("Weather Directory", False, "Directory not found")
        
        # Output Files
        self.print_header("Output Files")
        output_results = self.check_output_files()
        self.results['files']['output'] = output_results
        
        file_count = output_results.get('total_files', 0)
        if file_count > 0:
            self.print_result("IDF Output Files", True, f"{file_count} IDF files found")
            for file_info in output_results.get('files', [])[:5]:  # Show first 5
                size_kb = file_info['size'] / 1024
                self.print_result(f"  {file_info['name']}", True, f"{size_kb:.1f} KB")
        else:
            self.print_result("IDF Output Files", False, "No IDF files found")
        
        # Overall Status
        self.print_header("Overall Status Summary")
        issues = []
        
        # Check for critical issues
        if required_missing:
            issues.append(f"Missing required dependencies: {', '.join(required_missing)}")
        
        import_failures = [k for k, v in import_results.items() if not v.get('imported')]
        if import_failures:
            issues.append(f"Failed to import components: {', '.join(import_failures)}")
        
        init_failures = [k for k, v in init_results.items() if not v.get('initialized')]
        if init_failures:
            issues.append(f"Failed to initialize components: {', '.join(init_failures)}")
        
        config_missing = [k for k, v in config_results.items() if not v.get('exists')]
        if config_missing:
            issues.append(f"Missing config files: {', '.join(config_missing)}")
        
        if issues:
            self.results['overall']['status'] = 'degraded'
            self.results['overall']['issues'] = issues
            print(f"{Colors.YELLOW}⚠ System Status: DEGRADED{Colors.RESET}")
            print(f"{Colors.YELLOW}Issues found:{Colors.RESET}")
            for issue in issues:
                print(f"  • {issue}")
        else:
            self.results['overall']['status'] = 'healthy'
            print(f"{Colors.GREEN}✓ System Status: HEALTHY{Colors.RESET}")
            print(f"{Colors.GREEN}All critical components are operational{Colors.RESET}")
        
        return self.results
    
    def save_results(self, filename: str = "status_check_results.json"):
        """Save results to JSON file"""
        output_path = Path(filename)
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n{Colors.BLUE}Results saved to: {output_path}{Colors.RESET}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Check the status of IDF Creator system components'
    )
    parser.add_argument(
        '--no-api',
        action='store_true',
        help='Skip API health check (useful if server is not running)'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default='http://localhost:5001',
        help='Base URL for API health check (default: http://localhost:5001)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to JSON file'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON only (no human-readable output)'
    )
    
    args = parser.parse_args()
    
    checker = StatusChecker()
    
    if args.json:
        # JSON-only output
        results = checker.run_all_checks(check_api=not args.no_api)
        print(json.dumps(results, indent=2, default=str))
    else:
        # Human-readable output
        results = checker.run_all_checks(check_api=not args.no_api)
        
        if args.save:
            checker.save_results()
    
    # Exit with appropriate code
    if results['overall']['status'] == 'healthy':
        sys.exit(0)
    elif results['overall']['status'] == 'degraded':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()

