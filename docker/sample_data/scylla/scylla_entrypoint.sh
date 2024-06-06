#!/bin/bash

echo "######### Starting to populate sample scylla db... #########"

until cqlsh host.docker.internal -u cassandra -p cassandra -e "DESCRIBE KEYSPACES"; do
  echo "Waiting for Scylla DB..."
  sleep 10
done

cqlsh host.docker.internal -u cassandra -p cassandra -f /scylla/scylla_example.cql

echo "######### Execution of sh script is finished #########"
echo "######### Scylla temporary instance stopping #########"

