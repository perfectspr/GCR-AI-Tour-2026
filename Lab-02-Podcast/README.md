# 播客工作流

基于 Microsoft Azure AI 与 GitHub Actions 的自动化播客生成系统。该工作流通过智能 Agent 自动生成关于 AI 与技术话题的播客内容。

## 功能特性

- 🤖 **AI 驱动生成**：利用 Azure AI Projects 与 Agent 工作流，生成自然流畅的播客对话内容
- ⏰ **自动化调度**：GitHub Actions 每日自动触发，持续生成播客内容
- 📝 **话题管理**：基于纯文本的话题队列管理机制
- 🔄 **持续发布**：自动提交并推送生成的内容到仓库

## 前置条件

- Python 3.11+
- Azure AI Projects 订阅
- 已启用 Actions 的 GitHub 仓库
- Azure 凭据（租户 ID、客户端 ID、客户端密钥）

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/kinfey/podcast_workflow.git
cd podcast_workflow
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填写你的 Azure 凭据
```

## 配置说明

### Azure 配置

1. 在 [Azure AI Foundry](https://ai.azure.com) 中创建 Azure AI 项目
2. 创建 Microsoft Entra（Azure AD）服务主体：
   ```bash
   az ad sp create-for-rbac --name "podcast-workflow-sp" --role Contributor --scopes /subscriptions/{subscription-id}
   ```
3. 在 GitHub 仓库中添加 `AZURE_CREDENTIALS` Secret（Settings → Secrets and variables → Actions），格式如下：
   ```json
   {
     "clientId": "your-application-client-id",
     "clientSecret": "your-client-secret",
     "tenantId": "your-tenant-id",
     "subscriptionId": "your-subscription-id"
   }
   ```
   
   **注意**：`clientId` 必须是 Microsoft Entra 应用注册中的应用程序（客户端）ID。

### 话题管理

在 `topic/title.txt` 中添加话题，每行一个：
```
如何在工程中有效运用 GenAIOps
学习 CUDA 编程的技巧
全球文生视频模型横向对比
你对 Agentic 工作流的看法
Qwen 是最全面的开源模型吗？
```

GitHub Action 每天处理一个话题，处理完成后自动从队列中移除。

## 使用方式

### 手动执行

指定话题手动运行工作流：
```bash
python podcast_workflow.py -t "你的播客话题"
```

### 自动执行

GitHub Action 每 24 小时自动运行一次（UTC 00:00 / 北京时间 08:00）。

也可手动触发：
1. 进入 GitHub 仓库的「Actions」标签页
2. 选择「Daily Podcast Generator」
3. 点击「Run workflow」

## 工作流程

1. **话题选取**：读取 `topic/title.txt` 的第一行
2. **内容生成**：执行 AI Agent 工作流，生成播客内容
3. **输出存储**：将生成的播客保存至 `podcast/` 目录
4. **队列更新**：从 `topic/title.txt` 中移除已处理的话题
5. **Git 提交**：自动提交并推送变更到仓库

## 项目结构

```
podcast_workflow/
├── .github/
│   └── workflows/
│       └── daily-podcast.yml    # GitHub Actions 工作流配置
├── podcast/                      # 生成的播客内容
├── topic/
│   └── title.txt                # 话题队列
├── yaml/                         # 工作流配置文件
├── podcast_workflow.py          # 主工作流脚本
├── requirements.txt             # Python 依赖
└── README.md
```

## 生成内容说明

播客文件保存在 `podcast/` 目录下，以唯一标识符命名：
- 格式：`2p_podcast_<uuid>.txt`
- 内容：由 AI 生成的两位主持人围绕话题的对话内容

## GitHub Actions 工作流说明

每日工作流执行以下步骤：
1. 检出仓库代码
2. 配置 Python 环境
3. 安装依赖
4. 读取并处理一个话题
5. 运行播客生成脚本
6. 提交生成内容及更新后的话题列表
7. 推送变更到仓库

## 常见问题排查

### 大文件错误

如遇 GitHub 100 MB 文件大小限制报错，`.gitignore` 已配置排除大型媒体文件（`.mov`、`.mp4`、`.wav`、`.mp3` 等）。

### 认证问题

请确认 GitHub Secrets 中的 Azure 凭据配置正确，且具备访问 Azure AI Projects 的必要权限。

### 工作流失败

请在 GitHub 的 Actions 标签页查看详细日志。常见原因：
- Azure 凭据缺失或无效
- 话题队列为空
- API 速率限制

## 贡献

欢迎提交 Pull Request 参与贡献！

## 许可证

MIT License —— 欢迎将本项目用于你自己的播客生成需求。

## 致谢

本项目基于以下技术构建：
- [Azure AI Projects](https://learn.microsoft.com/azure/ai-studio/)
- [Microsoft Foundry Agent Framework](https://learn.microsoft.com/azure/ai-studio/concepts/agents)
- GitHub Actions