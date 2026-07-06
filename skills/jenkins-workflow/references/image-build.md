# Image Build Evidence

镜像构建证据至少包含：

- Jenkins job name
- build number
- build result
- SCM revision
- image tag 或 digest
- console tail 中的关键 build/push 片段

如果缺少 image tag/digest，必须说明证据不足，不能推断镜像已经发布。
