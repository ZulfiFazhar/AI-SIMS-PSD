#!/bin/bash
# Wait for MySQL to be ready

set -e

host="$1"
shift
cmd="$@"

until mysql -h "$host" -u inkubator -pinkubator inkubator_db -e "SELECT 1" >/dev/null 2>&1; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "MySQL is up - executing command"
exec $cmd
