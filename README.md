# apify-li-search

Search LinkedIn Jobs for postings that match your own profile, and get a
plain-text file back with a one-line "fit" explanation per posting (based on
overlap between your listed skills and the job description).

## 1. Get an Apify API token

This script uses [Apify](https://apify.com) to run the LinkedIn search. Apify
gives every new account **free signup credit ($5)**, which is enough to run
this script many times over -- each search costs a few cents.

1. Create a free account at [apify.com](https://console.apify.com/sign-up).
2. Go to **Settings → Integrations** (or [console.apify.com/account?tab=integrations](https://console.apify.com/account?tab=integrations)).
3. Copy your **Personal API token**.
4. Set it as an environment variable in your terminal:

   ```
   export APIFY_TOKEN=your_token_here
   ```

## 2. Prepare your profile

Save your CV / LinkedIn summary as a plain text file, e.g. `profile.txt`.
The script scans it for known tech terms (languages, frameworks, cloud
tools) to figure out what to compare job postings against.

## 3. Run it

```
python3 profile_match.py --profile profile.txt \
    --keywords "Node.js TypeScript Backend Engineer" \
    --location Netherlands --period month -o matches.txt
```

- `--profile`: path to your profile/CV text file
- `--keywords`: the LinkedIn search query (job title, skills, free text)
- `--location`: default `Netherlands`
- `--period`: `day`, `week`, `month` (default), or `any`
- `--limit`: max number of postings to fetch (default 30)
- `-o` / `--out`: output file (default `profile-match.txt`)

Requires Python 3 and no extra packages -- just the standard library.

## What it doesn't do

It doesn't filter out recruitment agencies or duplicate postings, and the
"fit" line is a simple keyword-overlap heuristic, not a judgment call --
read the actual posting before deciding anything.
