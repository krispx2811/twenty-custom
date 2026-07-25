#!/usr/bin/env python3
# Point the Railway Twenty + Twenty Worker services at an image tag and redeploy.
#
# Usage:
#   export RAILWAY_TOKEN=<Railway Project-Access-Token>   # project Settings -> Tokens
#   python3 deploy/railway-set-image.py ghcr.io/krispx2811/twenty-custom:2.22.0
#   python3 deploy/railway-set-image.py twentycrm/twenty:v2.22.0     # rollback to stock
#
# The token is read from the environment and never stored. Uses curl (no python TLS deps).

import json, os, subprocess, sys

ENV = "7662b4a3-cc57-4510-8f46-0924af9d4a12"
SERVICES = {
    "Twenty": "30cc3ce4-a586-4364-9f11-04069c10b635",
    "Twenty Worker": "7931605c-5189-451c-889c-644b07070c8c",
}
ENDPOINT = "https://backboard.railway.app/graphql/v2"


def gql(token, query, variables):
    payload = json.dumps({"query": query, "variables": variables})
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", ENDPOINT,
         "-H", "Project-Access-Token: " + token,
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True, text=True,
    )
    return json.loads(r.stdout)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: railway-set-image.py <image>  (e.g. ghcr.io/krispx2811/twenty-custom:2.22.0)")
    image = sys.argv[1]
    token = os.environ.get("RAILWAY_TOKEN")
    if not token:
        sys.exit("set RAILWAY_TOKEN (a Railway Project-Access-Token) in the environment first")

    upd = ("mutation($e:String!,$s:String!,$i:ServiceInstanceUpdateInput!){"
           " serviceInstanceUpdate(environmentId:$e, serviceId:$s, input:$i) }")
    dep = "mutation($e:String!,$s:String!){ serviceInstanceDeploy(environmentId:$e, serviceId:$s) }"

    for name, sid in SERVICES.items():
        r = gql(token, upd, {"e": ENV, "s": sid, "i": {"source": {"image": image}}})
        if "errors" in r:
            sys.exit(f"update {name} failed: {json.dumps(r['errors'])[:400]}")
        print(f"set {name:14s} -> {image}")

    for name, sid in SERVICES.items():
        r = gql(token, dep, {"e": ENV, "s": sid})
        if "errors" in r:
            sys.exit(f"deploy {name} failed: {json.dumps(r['errors'])[:400]}")
        print(f"redeploy {name:14s}: triggered")

    print("\nDone. Watch the deploys in the Railway dashboard.")


if __name__ == "__main__":
    main()
