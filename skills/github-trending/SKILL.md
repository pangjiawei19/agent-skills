# GitHub Trending 报告 Skill

自动生成 GitHub Trending 热门项目报告，包含项目信息、趋势分析和洞察。

## 触发条件

当用户提到以下关键词时触发：
- "GitHub Trending"
- "GitHub 热门"
- "GitHub 趋势"
- "今天热门项目"
- "拉取 GitHub Trending"
- "看看 GitHub 上有什么新项目"

## 功能说明

1. 使用浏览器访问 GitHub Trending 页面获取实时数据
2. 提取项目信息：名称、总 Star 数、今日新增 Star、语言、描述
3. 生成格式化的报告，包含：
   - 项目列表（带分隔线）
   - 趋势分析总结
   - 技术栈分布
   - 热点方向洞察

## 输出格式

```markdown
---

**1. 项目名称** ⭐ 总 Star 数 (+今日新增 今日)
- **链接：** [owner/repo](https://github.com/owner/repo)
- **语言：** 编程语言
- **描述：** 项目描述（中文）

---

**2. ...**

---

## 📊 今日趋势分析

### 🔥 热门关键词

### 技术栈分布

### 💡 观察

```

## 使用方法

```
用户：拉取一下今天的 GitHub Trending
助手：[执行此 Skill，返回完整报告]
```

## 依赖工具

- `browser` - 访问 GitHub Trending 页面
- `web_search` - 可选，用于补充项目背景信息

## 注意事项

1. GitHub Trending 页面需要登录才能看到 Star 按钮，但基本信息无需登录
2. 使用 browser.snapshot 获取页面内容，解析 aria-ref 元素
3. 项目数量默认取前 10 个，可根据用户需求调整
4. 趋势分析需要结合项目描述和当前技术热点进行解读

## 扩展建议

- 可添加按语言过滤功能（如"只看 Python 项目"）
- 可添加周榜/月榜支持
- 可添加项目对比功能
- 可定期自动推送（通过 cron）
