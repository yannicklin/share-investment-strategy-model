# 🚀 Multi-Market Deployment Guide (OCI)

This guide details how to deploy the **AI Trading System (ASX, USA, TWN)** on an Oracle Cloud Infrastructure (OCI) instance.

## 📋 System Requirements

| Component | Minimum Spec | Recommended Spec |
| :--- | :--- | :--- |
| **CPU** | 1 OCPU (AMD) | 4 OCPU (ARM Ampere) |
| **RAM** | 6 GB | 24 GB |
| **Storage** | 47 GB (Boot Volume) | 100 GB+ |
| **OS** | Oracle Linux 8 / Ubuntu 22.04 | **Ubuntu 24.04 Minimal** (Recommended) |

> **Note on 6GB RAM Instances**: This guide includes an automated SWAP file creation script (4GB) to prevent crashes during ML model training.

---

## 🛠️ Phase 1: OCI Instance Creation & SSH Setup

### 1. Generate SSH Keys (Local Machine)
Before creating the instance, you need an SSH key pair. We have provided a script to generate a secure one.

```bash
./scripts/generate_ssh_keys.sh
```
This will create a `keys/` folder with:
- `oci_trading_key.pub` (Upload this to Oracle)
- `oci_trading_key` (Keep this safe!)

### 2. Create the Instance on OCI
1. **Login** to Oracle Cloud Console.
2. Go to **Compute** -> **Instances** -> **Create Instance**.
3. **Image & Shape**:
   - Image: **Ubuntu 24.04 Minimal**
   - Shape: **VM.Standard.E2.1.Micro** (Always Free AMD) or **VM.Standard.A1.Flex** (Always Free ARM).
4. **Networking**: 
   - Ensure "Assign a public IPv4 address" is checked.
5. **Add SSH Keys**:
   - Select **"Upload public key files (.pub)"**.
   - Upload the `keys/oci_trading_key.pub` file you just generated.
6. Click **Create**.

### 3. Connect to the Server
Wait for the instance to show "Running" and copy its **Public IP**.

#### Option A: Direct Connection
```bash
# Set correct permissions for the key (First time only)
chmod 600 keys/oci_trading_key

# Connect
ssh -i keys/oci_trading_key ubuntu@<YOUR_INSTANCE_IP>
```

#### Option B: Configure Local SSH Shortcut (Recommended for Mac)
Instead of typing the full command every time, configure your local SSH.

1. **Move the key to your SSH folder**:
   ```bash
   mv keys/oci_trading_key ~/.ssh/id_oci_trading
   chmod 600 ~/.ssh/id_oci_trading
   ```

2. **Edit your SSH Config**:
   Open `~/.ssh/config` in a text editor:
   ```bash
   nano ~/.ssh/config
   ```

3. **Add this configuration block**:
   ```text
   Host oci
       HostName <YOUR_INSTANCE_IP>
       User ubuntu
       IdentityFile ~/.ssh/id_oci_trading
   ```

4. **Connect simply**:
   ```bash
   ssh oci
   ```

---

## 🛠️ Phase 2: Initial Server Setup (On the Remote Server)

### 1. Update System & Install Dependencies
Run the following commands to install Git, Docker, and Docker Compose:

```bash
# Update package list
sudo apt-get update && sudo apt-get upgrade -y

# Install Git, Nano, and essential tools
sudo apt-get install -y git nano curl build-essential

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to the docker group (avoids using sudo for docker commands)
sudo usermod -aG docker $USER

# Install Docker Compose (if not included in Docker plugin)
sudo apt-get install -y docker-compose-plugin
# Verify installation
docker compose version
```

**⚠️ Important:** Log out and log back in for the group changes to take effect.
```bash
exit
# SSH back in
ssh ...
```

---

## 🏗️ Phase 2: Deploying the Application

### 1. Clone the Repository (Playground Branch)
Clone the `playground` branch to your server (this branch contains the deployment scripts).

```bash
git clone -b playground https://github.com/YourUsername/share-investment-strategy-model.git
cd share-investment-strategy-model
```

### 2. Configure Environment Variables
Copy the example configuration and edit it with your secrets.

```bash
cp .env.example .env
nano .env
```

**Key Variables to Set:**
- `OCI_REGION`, `OCI_COMPARTMENT_ID`: Your Oracle Cloud details.

### 3. Run the Automated Setup Script
This script handles the heavy lifting:
- Checks system readiness.
- **Creates a 4GB Swap File** (crucial for 6GB RAM instances).
- Sets up Git Worktrees for `asx`, `usa`, and `twn` branches.
- Builds and launches the Docker containers.

```bash
chmod +x setup_multimarket_server.sh
./setup_multimarket_server.sh
```

---

## 🌐 Phase 3: Network Configuration (Cloudflare Tunnel)

### 1. Why Cloudflare Tunnel?
We are using **Cloudflare Tunnel** instead of opening ports. This is safer because:
- No ports (80/443) need to be opened on Oracle Cloud.
- Your server IP remains hidden.
- It handles SSL automatically.

### 2. Get Your Tunnel Token
1. Go to **Cloudflare Zero Trust Dashboard** -> **Networks** -> **Tunnels**.
2. Click **Create a Tunnel**.
   - Name: `trading-server`
   - Save the tunnel.
3. Choose **Docker** as the environment.
4. **Copy the token** from the command shown (it looks like `eyJhIjoi...`).
   - **CRITICAL**: The token must be copied exactly. An incorrect token will cause an "Error 1003" or "Invalid Tunnel token" error.
   - Do NOT run the command. Just copy the long token string.




5. Paste this token into your `.env` file:
   ```bash
   CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoi...
   ```

### 3. Configure Public Hostnames
In the Cloudflare Tunnel configuration screen (Public Hostname tab), add three rules:

| Domain | Service Type | URL |
| :--- | :--- | :--- |
| `asx-lab.twoudia.top` | HTTP | `lab-asx:8501` |
| `usa-lab.twoudia.top` | HTTP | `lab-usa:8502` |
| `twn-lab.twoudia.top` | HTTP | `lab-twn:8503` |

> **Note**: We use the container names (`lab-asx`) as the hostname because Cloudflare is running inside the Docker network.

---

## 📊 Phase 4: Verification & Monitoring

### Check Container Status
Verify all labs are running:
```bash
docker ps
```
You should see:
- `trading-tunnel` (Up)
- `trading-lab-asx` (Port 8501)
- `trading-lab-usa` (Port 8502)
- `trading-lab-twn` (Port 8503)

### Monitor Resource Usage
Keep an eye on memory usage to ensure you stay within the 6GB limit:
```bash
docker stats
```

### View Logs
If a lab isn't loading, check its logs:
```bash
# For ASX Lab
docker logs -f trading-lab-asx

# For USA Lab
docker logs -f trading-lab-usa
```

---

## 🧹 Maintenance

### Updating the Code
To update a specific lab (e.g., ASX) with the latest code from GitHub:

```bash
# Go to the branch directory
cd asx
git pull origin asx

# Rebuild the specific container
cd ..
docker-compose up -d --build lab-asx
```

### Cleaning Up Disk Space
Over time, Docker images can consume space. Run this monthly:
```bash
docker system prune -a
```
