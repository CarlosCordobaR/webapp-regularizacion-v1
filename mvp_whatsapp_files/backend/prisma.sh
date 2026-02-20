#!/bin/bash
# Prisma CLI wrapper - Auto-configures PATH for Prisma commands
# Usage: ./prisma.sh [command]
# Example: ./prisma.sh generate
#          ./prisma.sh db pull
#          ./prisma.sh migrate dev --name add_field

export PATH="/Users/PhD/Library/Python/3.9/bin:$PATH"

if [ -z "$1" ]; then
    echo "Prisma CLI Helper"
    echo ""
    echo "Usage: ./prisma.sh [command]"
    echo ""
    echo "Common commands:"
    echo "  generate          - Generate Prisma Client"
    echo "  db pull           - Introspect database schema"
    echo "  migrate dev       - Create and apply migration"
    echo "  migrate deploy    - Apply pending migrations"
    echo "  studio            - Open Prisma Studio (DB browser)"
    echo "  format            - Format schema.prisma"
    echo "  validate          - Validate schema.prisma"
    echo ""
    echo "Examples:"
    echo "  ./prisma.sh generate"
    echo "  ./prisma.sh db pull"
    echo "  ./prisma.sh migrate dev --name add_email"
    echo "  ./prisma.sh studio"
    exit 0
fi

python3 -m prisma "$@"
