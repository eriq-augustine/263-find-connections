#!/bin/sh

OUTDIR='../psl/data'

mkdir -p $OUTDIR

# Observations
psql facebook -q -A -t -F '	' -c 'SELECT DISTINCT userId, workId FROM Employment' -o $OUTDIR/employment.txt
psql facebook -q -A -t -F '	' -c 'SELECT DISTINCT userId, schoolId FROM Education' -o $OUTDIR/education.txt
psql facebook -q -A -t -F '	' -c 'SELECT DISTINCT userId, placeId FROM Lived' -o $OUTDIR/lived.txt

# Targets

read -d '' targetQuery << EOF
   SELECT
      fromEntityId,
      toEntityId
   FROM Edges
   WHERE isInner = TRUE
EOF

psql facebook -q -A -t -F '	' -c "${targetQuery}" -o $OUTDIR/friends_targets.txt
