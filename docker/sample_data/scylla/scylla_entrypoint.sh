#!/bin/bash

echo "######### Starting to populate sample scylla db... #########"

until cqlsh host.docker.internal -e "DESCRIBE KEYSPACES"; do
  echo "Waiting for Scylla DB..."
  sleep 10
done

cqlsh host.docker.internal -f /scylla/scylla_example.cql

echo "######### Execution of sh script is finished #########"
echo "######### Scylla temporary instance stopping #########"

