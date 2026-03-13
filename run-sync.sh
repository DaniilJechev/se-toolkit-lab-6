#!/bin/bash
curl -X POST http://localhost:42002/pipeline/sync \
  -H 'Authorization: Bearer Abcd1234' \
  -H 'Content-Type: application/json' \
  -d '{}'
