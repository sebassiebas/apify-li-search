#!/usr/bin/env python3
"""Search LinkedIn Jobs for postings that match a candidate profile.

Scores each result by how many of the candidate's own skills (extracted from
the profile text using a fixed list of common tech terms) also appear in the
job posting, and writes a plain-text file with one "Fit" line per posting
explaining the overlap.

Requires an Apify API token (see README.md for how to get one -- the free
signup credit is enough to run this many times over).

    python3 profile_match.py --profile cv.txt \
        --keywords "Node.js TypeScript Backend Engineer" \
        --location Netherlands --period month -o matches.txt
"""
import argparse,json,os,re,sys,urllib.request,urllib.error
from pathlib import Path

ACTOR="curious_coder~linkedin-jobs-scraper"
BASE="https://api.apify.com/v2"

PERIODS={'day':'past24Hours','week':'pastWeek','month':'pastMonth','any':'anyTime'}

# Broad enough for most software profiles, not meant to be exhaustive.
# A term missing here simply won't show up in the fit line -- a limitation
# to be aware of, not a bug.
TERMS=['TypeScript','JavaScript','Node.js','Python','Java','Go','Rust','C#',
 '.NET','PHP','Ruby','Kotlin','Swift','GraphQL','REST','gRPC','microservices',
 'serverless','event-driven','Pub/Sub','WebSockets','Kafka','RabbitMQ','Temporal',
 'Kubernetes','Docker','Terraform','CloudFormation','Ansible','AWS','Azure','GCP',
 'Lambda','CI/CD','GitHub Actions','GitLab','Jenkins','PostgreSQL','MySQL',
 'MongoDB','Redis','Elasticsearch','DynamoDB','Prisma','React','Vue','Angular',
 'Next.js','Django','Flask','Spring','FastAPI']

def token():
    t=os.environ.get('APIFY_TOKEN')
    if t: return t.strip()
    sys.exit("No token found. Set the APIFY_TOKEN environment variable -- see README.md.")

def fetch(payload,tok,timeout=180):
    r=urllib.request.Request(
        f"{BASE}/acts/{ACTOR}/run-sync-get-dataset-items",
        data=json.dumps(payload).encode(),
        headers={'Authorization':f'Bearer {tok}','Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(r,timeout=timeout) as f: return json.loads(f.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Apify returned {e.code}: {e.read()[:300].decode(errors='replace')}")

def terms_in(text):
    t=text or ''
    return {s for s in TERMS if re.search(r'(?<![\w-])'+re.escape(s)+r'(?![\w-])',t,re.I)}

def fit_line(candidate_terms,job):
    text=(job.get('title') or '')+' '+(job.get('descriptionText') or '')
    overlap=terms_in(text) & candidate_terms
    if not overlap:
        return "Fit: weak match -- no clear overlap with the candidate's listed skills."
    senior=bool(re.search(r'senior|lead|principal|staff',text,re.I))
    level='senior-level role' if senior else 'role'
    return f"Fit: {level} matching candidate's {', '.join(sorted(overlap)[:6])} background."

def main():
    p=argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--profile',required=True,help='text file with the candidate profile/CV')
    p.add_argument('--keywords',required=True,help='LinkedIn search query, e.g. "Node.js TypeScript Backend Engineer"')
    p.add_argument('--location',default='Netherlands')
    p.add_argument('--period',choices=list(PERIODS),default='month')
    p.add_argument('--limit',type=int,default=30)
    p.add_argument('-o','--out',default='profile-match.txt')
    a=p.parse_args()

    profile_text=Path(a.profile).read_text(encoding='utf-8')
    candidate_terms=terms_in(profile_text)
    if not candidate_terms:
        print("  note: none of the known terms were found in the profile; "
              "the fit line will say 'weak match' for everything as a result")

    tok=token()
    print(f"searching: {a.keywords!r} in {a.location}, period {a.period}, up to {a.limit}",flush=True)
    items=fetch({'keywords':a.keywords,'location':a.location,
                 'datePosted':PERIODS[a.period],'limitPerSource':a.limit,
                 'scrapeCompany':False},tok)
    if not isinstance(items,list):
        sys.exit(f"unexpected response: {str(items)[:300]}")
    print(f"  {len(items)} postings")

    def relevance(j): return len(terms_in((j.get('title') or '')+' '+(j.get('descriptionText') or '')) & candidate_terms)
    items.sort(key=lambda j:-relevance(j))

    lines=[f"{a.keywords} -- {a.location}, past {a.period}",
           f"{len(items)} results, sorted by relevance to the candidate profile\n"]
    for j in items:
        lines.append('='*80)
        lines.append(f"{j.get('title','')}  —  {j.get('companyName','')}")
        lines.append(f"location: {j.get('location','')}  |  posted: {j.get('postedAt','')}  |  "
                      f"employment type: {j.get('employmentType','')}  |  seniority: {j.get('seniorityLevel','')}")
        if j.get('applicantsCount') is not None:
            lines.append(f"applicants: {j.get('applicantsCount')}")
        if j.get('jobPosterName'):
            lines.append(f"contact: {j.get('jobPosterName')} ({j.get('jobPosterTitle','')})")
        lines.append(f"link: {j.get('link','')}")
        lines.append(fit_line(candidate_terms,j))
        lines.append('')
        lines.append(' '.join((j.get('descriptionText') or '').split())[:1200])
        lines.append('')

    Path(a.out).write_text('\n'.join(lines),encoding='utf-8')
    print(f"\n{len(items)} postings -> {a.out}")
main()
