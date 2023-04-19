#!/bin/sh
if [ -d config ]; then
  echo "Recompiling with custom configuration..."
  cd /fides/clients
  npm run build-pc
  cd /fides/clients/privacy-center
fi;

npm run start
