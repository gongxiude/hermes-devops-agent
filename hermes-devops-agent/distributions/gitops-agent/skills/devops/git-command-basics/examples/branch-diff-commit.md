# Branch, Diff, Commit Example

Use this sequence when a draft workflow has already approved repository mutation.

```bash
git status --short --branch
git fetch --prune origin
git pull --ff-only origin master
git checkout -b hermes/t_123456/update-gateway-resource
git diff -- workloads/intlsms/gateway/test/resources.yaml
git add workloads/intlsms/gateway/test/resources.yaml
git commit -m "gitops: update gateway test resources"
git push origin HEAD:hermes/t_123456/update-gateway-resource
```

Stop if:

- the branch is not the expected base branch
- unrelated dirty files exist
- validation fails
- the requested branch name targets master/main directly
