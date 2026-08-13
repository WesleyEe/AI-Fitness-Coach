# Helm chart

Wraps `infra/k8s`'s raw manifests into a templated, configurable, versioned release.
Read `infra/k8s/README.md` first if you haven't - this assumes you've seen the plain
YAML underneath.

## Prerequisites

Same as `infra/k8s`: a local cluster (built/tested against OrbStack's), Ollama running
on the host, and the two images built and tagged `:local`:

```bash
docker build -t fitness-coach-backend:local ../../backend
docker build -f ../../frontend/Dockerfile.k8s -t fitness-coach-frontend:local \
  --build-arg VITE_API_URL=http://localhost:8001 ../../frontend
```

## Install

```bash
cd infra/helm
helm install fitness-coach fitness-coach --namespace fitness-coach --create-namespace --wait --timeout 3m
```

No manual ordering needed this time - unlike the raw manifests, the migration Job is
a **Helm hook** (`helm.sh/hook: post-install,post-upgrade` on
`templates/backend/migration-job.yaml`), and `--wait` makes Helm wait for it to
succeed as part of the install itself.

**Note it's `post-install`, not `pre-install`** - getting this right took two attempts
during development, and it's worth understanding why: `pre-install` hooks run *before
any of the chart's normal resources exist at all*, including the postgres
StatefulSet - a pre-install migration Job raced to connect to a Postgres that hadn't
been created yet and hung. `post-install` hooks run after normal resources are
created (though not necessarily *ready* - hence the Job's `initContainer` that waits
for Postgres to actually accept connections before running `alembic upgrade head`).

## Upgrade

```bash
helm upgrade fitness-coach fitness-coach --namespace fitness-coach --wait --timeout 3m
```

Runs the same migration Job again (`post-upgrade`) before considering the upgrade
complete. `hook-delete-policy: before-hook-creation,hook-succeeded` deletes the
previous run's Job first (Job specs are immutable, so a leftover completed Job would
make the next one fail with "already exists") and cleans up after success.

## Configuration

See `values.yaml` for everything overridable - image tags, replica counts, resource
requests/limits, Ollama settings, Postgres credentials. Override with `--set` or
`-f my-values.yaml`, e.g.:

```bash
helm upgrade fitness-coach fitness-coach -n fitness-coach --set backend.replicas=3
```

## Access it / ingest the knowledge base

Same as the raw manifests - see `infra/k8s/README.md`'s "Access it" and "Ingest the
knowledge base" sections. Same port-forward commands, same separate-database caveat
(this chart's Postgres PVC is independent of both Docker Compose's and the raw
manifests' - ingest into whichever one you're actually pointed at).

## Uninstall

```bash
helm uninstall fitness-coach --namespace fitness-coach
kubectl delete namespace fitness-coach
```

`helm uninstall` removes everything the chart created; the namespace itself isn't
chart-owned (see the note in `templates/` - no `namespace.yaml` template, created via
`--create-namespace` on install instead, the idiomatic Helm pattern), so it's deleted
separately.

## Known limitation, not solved here

There's a small window on a brand-new cluster's first `helm install` where backend
pods can report ready (their readiness probe only checks generic DB connectivity, not
whether this migration's tables exist yet) slightly before the migration Job
finishes, since both are created in roughly the same phase. See the long comment in
`templates/backend/migration-job.yaml` for the full reasoning - this is a genuinely
known-hard problem for charts that own both an app and its database, and production
setups often sidestep it by deploying the database as a separately-managed dependency
rather than solving the ordering within one chart. Not fixed here; documented
honestly instead, consistent with this whole project's approach to LLM reliability
findings in Sprints 5-6.

## GitOps

See `../../GITOPS.md` for a conceptual (not implemented) explanation of how a tool
like Argo CD or Flux would take over from here.
