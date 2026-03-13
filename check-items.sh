#!/bin/bash
curl -s http://localhost:42002/items/ \
  -H 'Authorization: Bearer Abcd1234' | head -c 500
