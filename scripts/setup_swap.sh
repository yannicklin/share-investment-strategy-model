#!/bin/bash
# setup_swap.sh
# Creates a 4GB Swap file for 6GB RAM instances on Oracle Cloud.

SWAP_FILE="/swapfile"

if [ -f "$SWAP_FILE" ]; then
    echo "✅ Swap file already exists at $SWAP_FILE."
    exit 0
fi

echo "⚠️  No swap file found. Creating 4GB swap for stability..."

# 1. Create the file (4GB = 4096MB)
sudo dd if=/dev/zero of=$SWAP_FILE bs=1M count=4096 status=progress

# 2. Set permissions (Security: Only root can read/write)
sudo chmod 600 $SWAP_FILE

# 3. Format as Swap
sudo mkswap $SWAP_FILE

# 4. Enable Swap
sudo swapon $SWAP_FILE

# 5. Persist across reboots
echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab

echo "✅ Swap created and enabled successfully."
free -h
