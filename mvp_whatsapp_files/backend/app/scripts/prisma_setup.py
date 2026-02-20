#!/usr/bin/env python3
"""
Prisma Setup and Management Script
Handles database introspection, migrations, and client generation
"""
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
PRISMA_DIR = BACKEND_DIR / "prisma"


def run_command(cmd: list[str], description: str):
    """Execute a shell command with error handling."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(
            cmd,
            cwd=BACKEND_DIR,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} completed")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False


def introspect_database():
    """Pull current database schema into Prisma schema."""
    return run_command(
        ["python3", "-m", "prisma", "db", "pull"],
        "Introspecting database schema"
    )


def generate_client():
    """Generate Prisma Python client from schema."""
    return run_command(
        ["python3", "-m", "prisma", "generate"],
        "Generating Prisma client"
    )


def create_migration(name: str):
    """Create a new migration with given name."""
    if not name:
        print("❌ Migration name required")
        print("Usage: python prisma_setup.py migrate <migration_name>")
        return False
    
    return run_command(
        ["python3", "-m", "prisma", "migrate", "dev", "--name", name],
        f"Creating migration: {name}"
    )


def apply_migrations():
    """Apply pending migrations to production."""
    return run_command(
        ["python3", "-m", "prisma", "migrate", "deploy"],
        "Applying migrations"
    )


def reset_database():
    """Reset database and apply all migrations (DESTRUCTIVE)."""
    confirm = input("⚠️  This will DELETE all data. Type 'yes' to confirm: ")
    if confirm.lower() != 'yes':
        print("Cancelled")
        return False
    
    return run_command(
        ["python3", "-m", "prisma", "migrate", "reset", "--force"],
        "Resetting database"
    )


def format_schema():
    """Format Prisma schema file."""
    return run_command(
        ["python3", "-m", "prisma", "format"],
        "Formatting schema"
    )


def validate_schema():
    """Validate Prisma schema syntax."""
    return run_command(
        ["python3", "-m", "prisma", "validate"],
        "Validating schema"
    )


def show_help():
    """Display help message."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Prisma Database Management Tool                     ║
╚══════════════════════════════════════════════════════════════╝

SETUP COMMANDS:
  python prisma_setup.py init          - Initial setup (introspect + generate)
  python prisma_setup.py generate      - Generate Prisma client
  
MIGRATION COMMANDS:
  python prisma_setup.py migrate <name> - Create new migration
  python prisma_setup.py deploy         - Apply migrations to production
  python prisma_setup.py reset          - Reset DB (DESTRUCTIVE!)

UTILITY COMMANDS:
  python prisma_setup.py introspect    - Pull DB schema → Prisma
  python prisma_setup.py validate      - Check schema syntax
  python prisma_setup.py format        - Format schema file

EXAMPLES:
  # Initial setup
  $ python prisma_setup.py init
  
  # Add new column to Client table
  $ # 1. Edit prisma/schema.prisma
  $ # 2. Create migration
  $ python prisma_setup.py migrate add_email_to_clients
  
  # Deploy to production
  $ python prisma_setup.py deploy

DOCUMENTATION:
  Schema file: ./prisma/schema.prisma
  Migrations: ./prisma/migrations/
  Docs: https://prisma-client-py.readthedocs.io/
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    # Check .env file exists
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists() and command not in ['help', 'validate', 'format']:
        print("❌ .env file not found!")
        print("📝 Copy .env.example to .env and configure DATABASE_URL")
        print(f"   cp {BACKEND_DIR}/.env.example {env_file}")
        sys.exit(1)
    
    # Execute command
    success = False
    
    if command == "help":
        show_help()
        success = True
    elif command == "init":
        print("🚀 Initializing Prisma...")
        success = introspect_database() and generate_client()
    elif command == "generate":
        success = generate_client()
    elif command == "introspect":
        success = introspect_database()
    elif command == "migrate":
        if len(sys.argv) < 3:
            print("❌ Migration name required")
            print("Usage: python prisma_setup.py migrate <migration_name>")
            sys.exit(1)
        success = create_migration(sys.argv[2])
    elif command == "deploy":
        success = apply_migrations()
    elif command == "reset":
        success = reset_database()
    elif command == "format":
        success = format_schema()
    elif command == "validate":
        success = validate_schema()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)
    
    if success:
        print("\n✨ Done!")
        sys.exit(0)
    else:
        print("\n💥 Operation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
