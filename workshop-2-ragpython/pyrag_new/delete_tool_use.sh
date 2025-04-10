#!/bin/bash
# Script to delete all records related to 1-tool_use.pdf from Qdrant

curl -X POST "http://35.238.226.133:6333/collections/documentation/points/delete" \
-H "Content-Type: application/json" \
-d '{
  "filter": {
    "must": [
      {
        "key": "metadata.source",
        "match": {
          "value": "/Users/grizzlym1/Desktop/docs/1-tool_use.pdf"
        }
      }
    ]
  }
}'

echo "Done deleting records related to 1-tool_use.pdf"
