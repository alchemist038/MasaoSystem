# digest_posts

This folder stores one Markdown record per digest upload.

Each record should capture:

- digest title
- source archive URLs
- local package folder in `D:\OBS\REC\digest\...`
- final uploaded video path
- thumbnail path
- publish time
- YouTube URL and video ID
- notes about timing offsets, comment-based extraction, and any manual adjustments
- final upload resolution, especially whether the master was `1920x1080`

Purpose:

- keep a Git-tracked audit trail of digest postings
- make it easy to revisit how a digest was assembled and uploaded
- avoid putting large binary outputs into the repo

Resolution policy:

- For future digest posts, treat `1920x1080` as the default target for the upload master.
- If a post ships below `1080p`, record the reason in that digest post file.
