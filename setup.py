#!/usr/bin/env python3
"""Setup script for Daily Astrological Pipeline"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def check_docker():
    """Check if Docker is installed"""
    if shutil.which("docker"):
        print("✅ Docker is installed")
        return True
    else:
        print("⚠️  Docker not found (optional for containerized deployment)")
        return False


def check_docker_compose():
    """Check if Docker Compose is installed"""
    if shutil.which("docker-compose"):
        print("✅ Docker Compose is installed")
        return True
    else:
        print("⚠️  Docker Compose not found (optional for containerized deployment)")
        return False


def create_env_file():
    """Create .env file from template"""
    env_example = Path("env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        response = input("\n.env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("   ⚠️  Please edit .env with your actual credentials")
        return True
    else:
        print("❌ env.example not found")
        return False


def create_virtual_environment():
    """Create Python virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        return False


def install_dependencies():
    """Install Python dependencies"""
    print("Installing dependencies...")
    
    # Determine pip path based on OS
    if sys.platform == "win32":
        pip_path = Path("venv/Scripts/pip")
    else:
        pip_path = Path("venv/bin/pip")
    
    if not pip_path.exists():
        print("❌ Virtual environment pip not found")
        print("   Please activate the virtual environment and run: pip install -r requirements.txt")
        return False
    
    try:
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "monitoring/grafana/dashboards",
        "monitoring/grafana/datasources"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")
    return True


def main():
    """Main setup process"""
    print_header("Sacred Journey Pipeline Setup")
    
    # Check prerequisites
    print("Checking prerequisites...")
    if not check_python_version():
        sys.exit(1)
    
    docker_available = check_docker()
    docker_compose_available = check_docker_compose()
    
    # Create environment file
    print_header("Environment Configuration")
    if not create_env_file():
        sys.exit(1)
    
    # Create virtual environment
    print_header("Python Environment")
    if not create_virtual_environment():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    # Create directories
    print_header("Directory Structure")
    create_directories()
    
    # Print next steps
    print_header("Setup Complete!")
    
    print("Next steps:")
    print("\n1. Edit .env file with your credentials:")
    print("   - Swiss Ephemeris API key")
    print("   - OpenAI API key and Assistant IDs")
    print("   - Neo4j credentials")
    print("   - Email SMTP settings")
    print("   - Location coordinates")
    
    print("\n2. Create OpenAI Assistants:")
    print("   - Go to https://platform.openai.com/assistants")
    print("   - Create three assistants as described in README.md")
    print("   - Copy their IDs to .env file")
    
    print("\n3. Activate virtual environment:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("\n4. Run the application:")
    print("   python main.py")
    
    if docker_available and docker_compose_available:
        print("\n5. Or use Docker:")
        print("   docker-compose up -d")
    
    print("\n6. Access the API:")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs (Swagger UI)")
    
    print("\n7. Test the setup:")
    print("   curl -X POST http://localhost:8000/test/email")
    print("   curl -X POST http://localhost:8000/test/neo4j")
    
    print("\n✨ Happy Sacred Journey! ✨")


if __name__ == "__main__":
    main()
