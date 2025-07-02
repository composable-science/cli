# 🔧 Nix Setup Guide

This guide helps you get started with the Computational Science Attestation Platform using Nix.

## 🚀 Quick Start

### Prerequisites

1. **Install Nix** (if not already installed):
   ```bash
   # Multi-user installation (recommended)
   sh <(curl -L https://nixos.org/nix/install) --daemon
   
   # Single-user installation (if multi-user doesn't work)
   sh <(curl -L https://nixos.org/nix/install) --no-daemon
   ```

2. **Enable Flakes** (required for this project):
   ```bash
   # Create nix config directory
   mkdir -p ~/.config/nix
   
   # Enable flakes and new command
   echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
   ```

3. **Restart your shell** or run:
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```

### Launch the Platform

```bash
# Clone the repository
git clone <your-repo-url>
cd composci

# One command to start everything!
nix run

# Alternative: Enter development shell first
nix develop
start-dev
```

## 🔧 Troubleshooting

### Flakes Not Enabled
**Error**: `error: experimental Nix feature 'flakes' is disabled`

**Solution**:
```bash
# Enable flakes globally
echo "experimental-features = nix-command flakes" | sudo tee -a /etc/nix/nix.conf

# Or per-user
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf

# Restart Nix daemon (on multi-user installations)
sudo systemctl restart nix-daemon
```

### Permission Issues with PostgreSQL
**Error**: `could not create lock file "/tmp/.s.PGSQL.5432.lock"`

**Solution**:
```bash
# Clean up any existing PostgreSQL processes
pkill -f postgres

# Remove old data directory
rm -rf ./.nix-postgres-data

# Try again
nix run .#setup-db
```

### Port Already in Use
**Error**: `Port 9002 is already in use` or `Port 5432 is already in use`

**Solution**:
```bash
# Find what's using the ports
lsof -i :9002
lsof -i :5432

# Kill the processes or change ports in frontend/package.json
# For Next.js, change the dev script: "dev": "next dev --turbopack -p 9003"
```

### Node Modules Issues
**Error**: Various npm/Node.js related errors

**Solution**:
```bash
# Clean everything and start fresh
nix run .#stop-services
rm -rf frontend/node_modules
rm -rf ./.nix-postgres-data
nix develop
cd frontend && npm install && cd ..
nix run .#setup-db
```

### Nix Store Full
**Error**: `error: not enough free space in '/nix/store'`

**Solution**:
```bash
# Clean up Nix store
nix-collect-garbage -d

# If that's not enough, delete old profiles
sudo nix-collect-garbage -d
```

## 🎯 Alternative Launch Methods

### 1. Development Shell + Manual Commands
```bash
nix develop

# In the shell:
setup-db       # Set up database
dev            # Start Next.js only
db-shell       # Access PostgreSQL
```

### 2. Individual Commands
```bash
# Database setup only
nix run .#setup-db

# Production build
nix run .#build-app

# Stop services
nix run .#stop-services
```

### 3. Legacy Nix (without flakes)
```bash
# If you can't enable flakes
nix-shell

# Then manually:
# 1. Start PostgreSQL
# 2. cd frontend && npm install
# 3. npm run db:generate && npm run db:push && npm run db:seed
# 4. npm run dev
```

## 🐳 Docker Alternative

If Nix doesn't work on your system:

```bash
# Build Docker image (requires Nix)
nix build .#docker
docker load < result

# Or use the provided Dockerfile (if available)
docker build -t composci-platform .
docker run -p 9002:9002 composci-platform
```

## 🌍 Environment Variables

The Nix flake automatically sets these up, but you can override them:

```bash
export DATABASE_URL="postgresql://composci_user:composci_pass@localhost:5432/composci_db"
export PGUSER="composci_user"
export PGPASSWORD="composci_pass"
export PGDATABASE="composci_db"
export PGHOST="localhost"
export PGPORT="5432"
```

## 🔍 Debugging

### Check Service Status
```bash
# PostgreSQL running?
pgrep -f postgres

# Next.js running?
curl http://localhost:9002/api/attestations

# Database accessible?
psql -h localhost -U composci_user -d composci_db -c "SELECT COUNT(*) FROM attestations;"
```

### View Logs
```bash
# PostgreSQL logs
tail -f ./.nix-postgres-data/logfile

# Next.js logs are in the terminal where you ran nix run
```

### Reset Everything
```bash
# Nuclear option - start completely fresh
nix run .#stop-services
rm -rf ./.nix-postgres-data
rm -rf frontend/node_modules
rm -rf frontend/.next
nix run
```

## 📞 Getting Help

1. **Check logs** in the terminal output
2. **Try the reset steps** above
3. **Check GitHub issues** for similar problems
4. **Create a new issue** with:
   - Your operating system
   - Nix version (`nix --version`)
   - Full error message
   - Steps to reproduce

## 🎉 Success!

When everything works, you should see:
```
🎉 Setup complete! Starting development server...

📍 Application will be available at: http://localhost:9002
📍 API endpoints at: http://localhost:9002/api
```

Then visit http://localhost:9002 to explore the platform!