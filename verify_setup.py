"""
vanna AI Dashboard - Verification & Testing Script
This script verifies all dependencies are installed and database connection works.

Usage:
    python verify_setup.py

The script will:
1. Check all required Python packages
2. Test database connection
3. Verify environment variables
4. Display diagnostic information
"""

import sys
import os
from pathlib import Path
from typing import Tuple, List
import subprocess

# Color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Configuration
REQUIRED_PACKAGES = {
    'streamlit': '1.28.0',
    'pandas': '2.0.0',
    'psycopg2': '2.9.0',
}

OPTIONAL_PACKAGES = {
    'google.generativeai': 'google-generativeai',
    'openai': 'openai',
    'sqlalchemy': 'sqlalchemy',
}


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{text:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}? {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}FAIL {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}? {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}? {text}{RESET}")


def check_python_version() -> bool:
    """Check if Python version is 3.8+"""
    print_header("Python Version Check")
    
    version = sys.version_info
    version_string = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version_string} (>=3.8 required)")
        return True
    else:
        print_error(f"Python {version_string} (>=3.8 required)")
        return False


def check_required_packages() -> bool:
    """Check if all required packages are installed"""
    print_header("Required Packages Check")
    
    all_installed = True
    
    for package, min_version in REQUIRED_PACKAGES.items():
        try:
            __import__(package)
            try:
                # Get version
                module = __import__(package)
                if hasattr(module, '__version__'):
                    version = module.__version__
                    print_success(f"{package:<20} {version}")
                else:
                    print_success(f"{package:<20} (version info not available)")
            except:
                print_success(f"{package:<20} (installed)")
        except ImportError:
            print_error(f"{package:<20} NOT INSTALLED")
            print_info(f"  -> Install with: pip install {package}")
            all_installed = False
    
    return all_installed


def check_optional_packages() -> List[str]:
    """Check if optional packages are installed"""
    print_header("Optional Packages Check")
    
    installed_llm_providers = []
    
    for import_name, package_name in OPTIONAL_PACKAGES.items():
        try:
            parts = import_name.split('.')
            __import__(import_name)
            print_success(f"{package_name:<20} installed")
            installed_llm_providers.append(package_name)
        except ImportError:
            print_warning(f"{package_name:<20} not installed")
            print_info(f"  -> Install with: pip install {package_name}")
    
    if not installed_llm_providers:
        print_warning("No LLM providers installed!")
        print_info("  -> For Google Gemini: pip install google-generativeai")
        print_info("  -> For OpenAI: pip install openai")
        print_info("  -> For Ollama: No pip install needed (requires separate setup)")
    
    return installed_llm_providers


def check_environment_variables() -> Tuple[bool, dict]:
    """Check important environment variables"""
    print_header("Environment Variables Check")
    
    env_vars = {
        'GOOGLE_API_KEY': 'Google Gemini API key',
        'OPENAI_API_KEY': 'OpenAI API key',
        'DB_HOST': 'Database host',
        'DB_USER': 'Database user',
        'DB_PASSWORD': 'Database password',
        'DB_NAME': 'Database name',
    }
    
    found_vars = {}
    all_found = True
    
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            # Don't print actual API keys for security
            if 'KEY' in var or 'PASSWORD' in var:
                masked_value = value[:5] + '*' * (len(value) - 8) + value[-3:]
                print_success(f"{var:<20} set ({masked_value})")
            else:
                print_success(f"{var:<20} set ({value})")
            found_vars[var] = value
        else:
            print_warning(f"{var:<20} not set")
    
    # Check if .env file exists
    env_file = Path('.env')
    if env_file.exists():
        print_info(".env file found")
    else:
        print_warning(".env file not found")
        print_info("  -> Copy .env.example to .env and fill in your values")
    
    return len(found_vars) > 0, found_vars


def check_database_connection(config: dict = None) -> bool:
    """Test PostgreSQL database connection"""
    print_header("Database Connection Test")
    
    # Use provided config or environment variables
    if config is None:
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'postgres'),
        }
    
    try:
        import psycopg2
        
        # Attempt connection
        connection = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        
        # Test query
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
        
        print_success("Database connection successful")
        print_info(f"  -> {version[:60]}...")
        
        # Get table count
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = cursor.fetchone()[0]
        
        print_info(f"  -> Found {table_count} tables in public schema")
        
        connection.close()
        return True
        
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        print_info("  -> Check database credentials in .env")
        print_info("  -> Ensure PostgreSQL is running")
        if config['host'] != 'localhost':
            print_info(f"  -> Connection string: {config['user']}@{config['host']}:{config['port']}/{config['database']}")
        return False


def check_streamlit_installation() -> bool:
    """Verify Streamlit is properly installed"""
    print_header("Streamlit Configuration Check")
    
    streamlit_dir = Path('.streamlit')
    config_file = streamlit_dir / 'config.toml'
    
    if streamlit_dir.exists():
        print_success(f".streamlit directory exists")
    else:
        print_warning(f".streamlit directory not found")
        return False
    
    if config_file.exists():
        print_success(f"config.toml exists")
        return True
    else:
        print_warning(f"config.toml not found")
        return False


def check_file_structure() -> bool:
    """Check if all necessary files are present"""
    print_header("File Structure Check")
    
    required_files = [
        'vanna_dashboard.py',
        'requirements_dashboard.txt',
        'README_DASHBOARD.md',
        'vanna_integration_examples.py',
        'docker-compose.yml',
        'init-db.sql',
        'QUICK_START.md',
    ]
    
    all_exist = True
    
    for filename in required_files:
        filepath = Path(filename)
        if filepath.exists():
            size = filepath.stat().st_size
            print_success(f"{filename:<30} ({size:,} bytes)")
        else:
            print_error(f"{filename:<30} NOT FOUND")
            all_exist = False
    
    return all_exist


def run_diagnostics() -> None:
    """Run comprehensive diagnostics"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}vanna AI Dashboard - Setup Verification{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")
    
    results = {
        'Python Version': check_python_version(),
        'Required Packages': check_required_packages(),
        'Optional Packages': check_optional_packages(),
        'Streamlit Config': check_streamlit_installation(),
        'File Structure': check_file_structure(),
    }
    
    # Check environment variables and database
    env_ok, found_vars = check_environment_variables()
    database_ok = False
    
    if found_vars and all(k in found_vars for k in ['DB_HOST', 'DB_USER', 'DB_NAME']):
        database_ok = check_database_connection(
            {
                'host': found_vars.get('DB_HOST', 'localhost'),
                'port': int(found_vars.get('DB_PORT', 5432)),
                'user': found_vars.get('DB_USER', 'postgres'),
                'password': found_vars.get('DB_PASSWORD', ''),
                'database': found_vars.get('DB_NAME', 'postgres'),
            }
        )
    elif not env_ok:
        print_warning("Skipping database check (credentials not configured)")
        # Try default localhost connection
        print_info("Attempting connection with default settings...")
        database_ok = check_database_connection()
    
    results['Database'] = database_ok
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for v in results.values() if v is True)
    total = len(results)
    
    for check, result in results.items():
        if result is True or result is False:
            status = f"{GREEN}? PASS{RESET}" if result else f"{RED}FAIL FAIL{RESET}"
            print(f"{check:<25} {status}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    # Recommendations
    if passed < total:
        print(f"\n{BOLD}{YELLOW}Recommendations:{RESET}")
        
        if not results['Python Version']:
            print(f"  * Upgrade Python to 3.8+")
        
        if not results['Required Packages']:
            print(f"  * Run: pip install -r requirements_dashboard.txt")
        
        if not results['File Structure']:
            print(f"  * Check that all files are present in the project directory")
        
        if not database_ok:
            print(f"  * Configure database connection in .env file")
            print(f"  * Or start PostgreSQL with: docker-compose up -d")
        
        print(f"\n{BOLD}{YELLOW}To proceed:{RESET}")
        print(f"  1. Fix all FAIL items above")
        print(f"  2. Review QUICK_START.md for setup instructions")
        print(f"  3. Run: streamlit run vanna_dashboard.py")
    else:
        print(f"\n{BOLD}{GREEN}? All checks passed! Ready to use.{RESET}")
        print(f"\n{BOLD}Next steps:{RESET}")
        print(f"  1. Run: streamlit run vanna_dashboard.py")
        print(f"  2. Connect to your database via the UI")
        print(f"  3. Ask natural language questions")
        print(f"  4. See results in real-time")
    
    print(f"\n{BOLD}{BLUE}Need Help?{RESET}")
    print(f"  * Quick Start: See QUICK_START.md")
    print(f"  * Documentation: See README_DASHBOARD.md")
    print(f"  * Integration: See vanna_integration_examples.py")
    print(f"  * Troubleshooting: See README_DASHBOARD.md#Troubleshooting")
    
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}\n")


if __name__ == "__main__":
    try:
        run_diagnostics()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Verification cancelled by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error during verification: {str(e)}")
        sys.exit(1)
