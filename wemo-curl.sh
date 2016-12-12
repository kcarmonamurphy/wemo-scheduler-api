#!/bin/bash
echo curl -u light:switch -X POST $1/api/device/$2?state="$3" | at -q $4 $5
