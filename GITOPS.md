# GitOps: what it would take from here (conceptual - not implemented)

Everything in `infra/` gets deployed by *you* running `kubectl apply` or `helm
install`/`helm upgrade` from your own machine. That's fine for a learning project, but
it has a real gap: the cluster's actual state and the manifests in this repo can drift
apart silently - someone (or something) runs a manual `kubectl edit`, or forgets to
run `helm upgrade` after a change gets merged, and now what's running doesn't match
what's in git. GitOps is the pattern that closes that gap.

## The core idea

A GitOps controller (Argo CD and Flux are the two common ones) runs *inside* the
cluster and continuously compares two things:

1. **Desired state**: whatever's in a git repo (this repo's `infra/helm/fitness-coach`,
   or a dedicated "deploy config" repo, depending on how a team structures it).
2. **Actual state**: what's really running in the cluster right now.

When they diverge, the controller reconciles - either automatically applying the
git-defined state (the common default), or flagging the drift for a human to approve,
depending on configuration. The controller is polling/watching git, not the other way
around: nobody runs `kubectl apply` by hand anymore, and nobody grants CI a
kubeconfig with cluster-admin either - the only thing that needs cluster access is the
controller already running inside it.

## What would actually change here

- A new git repo (or a subdirectory of this one) holding rendered manifests or Helm
  values - "what should be running," decoupled from "how to build the images."
- An Argo CD `Application` (or Flux `Kustomization`/`HelmRelease`) resource pointing
  at this repo's `infra/helm/fitness-coach` chart and a `values.yaml` per environment
  (a `values-prod.yaml` alongside the current dev-shaped `values.yaml`, for instance).
- CI's job shrinks to: build and push images, then update an image tag reference in
  the deploy repo (a commit, not a deploy) - the actual "make it live" step becomes
  the GitOps controller noticing that commit and reconciling, not a CI step directly
  touching the cluster.
- Rollback becomes `git revert` instead of `helm rollback` run by a human with direct
  cluster access.

## Why not implemented in this project

Two honest reasons, not just "out of scope":

1. **It needs a cluster that's actually running continuously with something watching
   it** - meaningful GitOps benefits (drift detection, audit trail, no direct human
   cluster access) require the controller to be a long-lived thing, which fits a
   real team's shared cluster far better than a local OrbStack cluster you start and
   stop on your laptop as needed.
2. **It needs a real git remote** - Argo CD/Flux poll an actual pushed repository,
   not a local working directory. This project has stayed local-only and commit-free
   by design throughout (see `README.md`'s ground rules) - adding GitOps would be the
   first thing in the whole project requiring a hosted remote to demonstrate properly.

## Secrets, while we're here

The `Secret` manifests in `infra/k8s/` and `infra/helm/` use plain `stringData` -
readable by anyone with `kubectl get secret -o yaml` access, not encrypted, fine for a
local learning cluster only. A GitOps setup makes this sharper: now the *plaintext*
would need to sit in a git repo, not just a cluster, which is a meaningfully worse
exposure. Real GitOps setups pair with one of:

- **Sealed Secrets** - encrypt a Secret client-side into a `SealedSecret` object that's
  safe to commit; only the in-cluster controller holds the private key to decrypt it.
- **External Secrets Operator** - the cluster pulls actual secret values from an
  external store (AWS Secrets Manager, Vault, etc.) at runtime; git never holds them
  at all, only a *reference* to where they live.

Neither implemented here, for the same reasons as GitOps itself - both need
infrastructure (a running controller, an external secret store) beyond a local
learning cluster's scope.
