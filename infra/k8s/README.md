# Raw Kubernetes manifests

Plain YAML, applied directly with `kubectl` - written first, before the Helm chart in
`infra/helm/`, specifically so the underlying Kubernetes objects are visible and
understandable before Helm's templating layer sits on top of them. If you've never
read raw Kubernetes YAML before, start here; `infra/helm/` assumes you've seen this.

## Prerequisites

- A local Kubernetes cluster. This was built and tested against **OrbStack's built-in
  Kubernetes** (`orb start k8s` - if you're on OrbStack, no separate tool install
  needed). `kind` or `minikube` would also work, with one caveat below.
- Ollama running on your host with `qwen2.5:3b` and `nomic-embed-text` pulled (same
  requirement as every other sprint).
- Images built locally and tagged to match what the manifests reference:
  ```bash
  docker build -t fitness-coach-backend:local ./backend
  docker build -f frontend/Dockerfile.k8s -t fitness-coach-frontend:local \
    --build-arg VITE_API_URL=http://localhost:8001 ./frontend
  ```
  `imagePullPolicy: Never` in the manifests means Kubernetes uses this exact local
  image rather than trying to pull from a registry - this works on OrbStack because
  its Kubernetes cluster shares the same image store as `docker build` (verified
  empirically; not all local-cluster tools do this - `kind` specifically needs
  `kind load docker-image` to make a locally built image visible to its cluster).

## Deploy, in order

Order matters here in a way it won't for the Helm chart (which formalizes ordering
via hooks - see `infra/helm/README.md`):

```bash
kubectl apply -f namespace.yaml

kubectl apply -f postgres/secret.yaml -f postgres/service.yaml -f postgres/statefulset.yaml
kubectl -n fitness-coach rollout status statefulset/postgres

kubectl apply -f backend/configmap.yaml -f backend/secret.yaml
kubectl apply -f backend/migration-job.yaml
kubectl -n fitness-coach wait --for=condition=complete job/backend-migrate

kubectl apply -f backend/deployment.yaml -f backend/service.yaml
kubectl apply -f frontend/deployment.yaml -f frontend/service.yaml
kubectl -n fitness-coach rollout status deployment/backend
kubectl -n fitness-coach rollout status deployment/frontend
```

Postgres must be ready before the migration Job runs; the migration Job must complete
before the backend Deployment is useful (its pods will report `/health` as ready even
without the schema existing yet - the readiness check is generic DB connectivity, not
"does the schema this app needs exist").

## Access it

```bash
kubectl -n fitness-coach port-forward svc/backend 8001:8000
kubectl -n fitness-coach port-forward svc/frontend 8080:80
```

- Frontend: http://localhost:8080
- Backend: http://localhost:8001/health, http://localhost:8001/docs

(On OrbStack specifically, Service ClusterIPs are also directly reachable from the
host without port-forwarding at all - verified during development - but that's an
OrbStack-specific bonus, not something to rely on for a manifest set meant to be
reasonably portable to other clusters.)

## Ingest the knowledge base

This cluster's Postgres is a completely separate database from Docker Compose's (a
different PVC) - the RAG knowledge base has to be ingested into it separately:

```bash
kubectl -n fitness-coach port-forward svc/postgres 5433:5432 &
cd ../../backend
DATABASE_URL="postgresql+psycopg://fitness:fitness@localhost:5433/fitness_coach" \
  uv run python -m app.rag.ingest
```

## Tear down

```bash
kubectl delete namespace fitness-coach
```

Deletes everything in the namespace, including the PVC (and therefore all data).

## Why a Job for migrations, not baked into the image's startup command

See the comment in `../../backend/Dockerfile`. Short version: the backend Deployment
here runs 2 replicas deliberately, to make concrete why "run migrations on container
startup" (fine for Sprint 1-6's single-instance Docker Compose setup) breaks the
moment there's more than one instance - every replica would race to apply migrations
concurrently. The Job runs once, decoupled from replica count.

## Why `/health` and `/live` are different probes

See `../../backend/app/api/routes/health.py`. `/health` (readiness) checks real DB
connectivity; `/live` (liveness) deliberately doesn't, so a brief Postgres blip
doesn't cause Kubernetes to kill and restart backend pods that are themselves fine.
