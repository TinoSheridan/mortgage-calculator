#!/bin/bash
# Deployment script for MortgageCalc to Render
# Ensures all features are properly included in the deployment

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Mortgage Calculator Deployment Checklist${NC}"
echo -e "${YELLOW}=====================================${NC}"

# Step 1: Verify features
echo -e "\n${YELLOW}Step 1: Verifying features...${NC}"
if python3 verify_deployment.py; then
  echo -e "${GREEN}✓ Feature verification passed${NC}"
else
  echo -e "${RED}✗ Feature verification failed. Fix issues before continuing.${NC}"
  exit 1
fi

# Step 2: Check git status
echo -e "\n${YELLOW}Step 2: Checking git status...${NC}"
if git status --porcelain | grep -q .; then
  echo -e "${YELLOW}⚠ You have uncommitted changes:${NC}"
  git status --short
  echo
  read -p "Do you want to commit these changes? (y/n): " commit_choice
  if [[ $commit_choice =~ ^[Yy]$ ]]; then
    read -p "Enter commit message: " commit_msg
    git add .
    git commit -m "$commit_msg"
    echo -e "${GREEN}✓ Changes committed${NC}"
  else
    echo -e "${YELLOW}⚠ Continuing with uncommitted changes${NC}"
  fi
else
  echo -e "${GREEN}✓ Working directory clean${NC}"
fi

# Step 3: Check current branch
echo -e "\n${YELLOW}Step 3: Checking current branch...${NC}"
current_branch=$(git rev-parse --abbrev-ref HEAD)
echo -e "Current branch: ${GREEN}$current_branch${NC}"
read -p "Is this the correct branch for deployment? (y/n): " branch_choice
if [[ ! $branch_choice =~ ^[Yy]$ ]]; then
  read -p "Enter the branch to switch to: " target_branch
  git checkout $target_branch
  echo -e "${GREEN}✓ Switched to branch $target_branch${NC}"
  current_branch=$target_branch
fi

# Step 4: Pull latest changes
echo -e "\n${YELLOW}Step 4: Pulling latest changes from remote...${NC}"
git pull origin $current_branch
echo -e "${GREEN}✓ Pulled latest changes${NC}"

# Step 5: Push to GitHub
echo -e "\n${YELLOW}Step 5: Pushing to GitHub...${NC}"
read -p "Ready to push to GitHub? This will trigger a Render deployment. (y/n): " push_choice
if [[ $push_choice =~ ^[Yy]$ ]]; then
  git push origin $current_branch
  echo -e "${GREEN}✓ Changes pushed to GitHub${NC}"
else
  echo -e "${RED}✗ Push canceled. Deployment aborted.${NC}"
  exit 1
fi

# Step 6: Verify Render deployment
echo -e "\n${YELLOW}Step 6: Verifying Render deployment...${NC}"
echo "After Render deployment completes, check the application at your Render URL."
echo -e "${YELLOW}⚠ Important checks:${NC}"
echo "1. Visit the /health endpoint to verify version ($VERSION)"
echo "2. Confirm seller credits and lender credits appear in the UI"
echo "3. Test the calculator with different credit values"
echo "4. Check for any errors in the Render logs"

echo -e "\n${GREEN}Deployment process completed!${NC}"
