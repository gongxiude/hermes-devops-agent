# Jenkins Change Draft

Jenkins 配置草稿必须进入 `jenkins-pipeline` 仓库分支，不直接修改 Jenkins job。

完成前必须运行：

```bash
git diff --check
git status --short
```

如果仓库已有 Jenkinsfile validator 或 Groovy lint，必须运行并记录结果。
