# Jenkinsfile And Shared Library

涉及 `jenkins-pipeline` 时必须先 refresh：

```bash
git -C "$SOFTWARE_DELIVERY_WORKSPACE_ROOT/jenkins-pipeline" fetch --prune origin
git -C "$SOFTWARE_DELIVERY_WORKSPACE_ROOT/jenkins-pipeline" pull --ff-only origin "${GITOPS_JENKINS_PIPELINE_BRANCH:-master}"
```

国际短信服务清单真源：

```text
jenkins-pipeline/share-library/resources/configs/intlsms.json
```

不要只看 Jenkins UI；需要回到仓库配置确认 SCM、job folder、module 和 deploy env。
