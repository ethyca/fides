#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VAULT_NAME="github-actions"
INTEGRATIONS_ENV_FILE=".env.integrations"

# Check if op is installed
if ! command -v op &> /dev/null; then
  echo -e "${RED}op could not be found. Please install it and try again.${NC}"
  exit 1
fi

echo -e "${BLUE}Signing in to 1Password${NC}"
$(op signin) || exit 1

echo -e "${YELLOW}Clearing integrations.env${NC}"
# Clear the integrations.env file
> $INTEGRATIONS_ENV_FILE

echo -e "${BLUE}Getting all items in the $VAULT_NAME vault${NC}"
# Get all item IDs in the vault, sorted by title
item_ids=$(op item list --vault "$VAULT_NAME" --format json | jq -r 'sort_by(.title) | .[].id')

echo -e "${BLUE}Looping through each item${NC}"
# Loop through each item
for id in $item_ids; do
  # Get the full item JSON
  ITEM_JSON=$(op item get "$id" --vault "$VAULT_NAME" --format json)
  echo "$ITEM_JSON" | jq -r '.fields[] | select(.value) | {value, reference} | select((.reference | split("/")[-1]) | test("^[A-Z0-9_]+$")) | .reference | split("/")[-1]'
  # Process each field in the JSON response:
  # 1. Select only fields that have a value
  # 2. Create an object with value and reference properties
  # 3. Filter references that end with uppercase letters, numbers, or underscores
  # 4. Format the output as an environment variable export statement
  echo "$ITEM_JSON" | \
    jq -r '.fields[] | select(.value) | {value, reference} | select((.reference | split("/")[-1]) | test("^[A-Z0-9_]+$")) | "export \(.reference | split("/")[-1])='\''\(.value)'\''"' >> $INTEGRATIONS_ENV_FILE
done

echo -e "${GREEN}Done. integrations.env has been updated with the new values.${NC}"
