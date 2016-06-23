#!/bin/bash

HOST="http://localhost:8000/submit"

curl -v -H 'Host: crash-reports' \
     -F 'ProductName=Test' \
     -F 'Version=1.0' \
     -F upload_file_minidump=@testcrash/raw/7d381dc5-51e2-4887-956b-1ae9c2130109.dump \
     "$HOST"
