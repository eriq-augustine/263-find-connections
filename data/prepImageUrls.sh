#!/bin/sh

OUT_FILE='/media/nas/data/facebook/imageCache/__imageUrls.txt'

read -d '' query << EOF
	SELECT
		facebookId,
		imageUrl
	FROM Entities
EOF

psql facebook -q -A -t -F '	' -c "${query}" -o $OUT_FILE
