#!/bin/bash
set -e

BRANCH="develop"
BASE_DIR="download/${BRANCH}/"
REPO_URL="https://github.com/nervosnetwork/ckb.git"

if [ ! -d "$BASE_DIR" ]; then
  mkdir -p "$BASE_DIR"
fi

cd "$BASE_DIR"
git clone -b $BRANCH $REPO_URL

cd ckb/
make prod
