#!/bin/sh
if [ -d config ]; then
  echo "Recompiling with custom configuration..."
  npm run build
fi;

npm run start
