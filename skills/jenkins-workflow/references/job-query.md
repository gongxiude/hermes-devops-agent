# Jenkins Job Query

只读查询优先使用 Jenkins MCP read-only tools：

- `whoAmI`
- `getStatus`
- `getJobs`
- `findJobsWithScmUrl`
- `getJob`
- `getJobScm`
- `getBuild`
- `getBuildScm`
- `getBuildChangeSets`
- `getBuildLog`
- `searchBuildLog`
- `getQueueItem`
- `getTestResults`
- `getFlakyFailures`

禁止使用 `triggerBuild` 和 `updateBuild`。
