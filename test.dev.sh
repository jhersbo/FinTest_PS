#!/bin/bash
if [[ "$1" == "--build" ]]; then
  docker compose -f docker-compose.test.yml build
fi
docker compose -f docker-compose.test.yml run --rm fintest_ps_test
