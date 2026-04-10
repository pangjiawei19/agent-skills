---
name: wechat-article-reader
description: 读取微信公众号文章原文（mp.weixin.qq.com）。当用户发送微信公众号文章链接、要求阅读/总结/提取微信文章内容时使用。适用于所有 mp.weixin.qq.com/s/ 开头的 URL。
---

# 微信公众号文章读取

微信文章有反爬验证机制，直接 `web_fetch` 会返回验证码页面。本 skill 使用微信客户端 UA 绕过验证。

## 使用流程

收到微信文章链接后，按以下步骤执行：

### 1. 调用脚本抓取文章

```bash
./skills/wechat-article-reader/scripts/fetch_wechat_article.sh "<url>" [output_dir]
```

脚本返回 JSON，包含：
- `title`：文章标题
- `text`：正文纯文本，图片位置用 `[IMAGE_N]` 占位符标记
- `images`：图片列表（含本地路径和 workspace 路径）
- `image_count`：图片数量

### 2. 分析图片

如果 `image_count > 0`，逐张读取 `images` 中的图片文件（使用 `path` 字段），判断每张图片与文章内容的相关性：

- **相关图片**（图表、数据、流程图、示意图、与正文内容直接相关的配图等）：分析图片内容，用分析结果替换对应的 `[IMAGE_N]` 占位符
- **无关图片**（装饰性风景图、Logo、公众号二维码、纯排版用图等）：直接删除对应的 `[IMAGE_N]` 占位符

### 3. 整合返回

返回替换/清理占位符后的完整图文内容。

相关图片的替换格式：
```
[图片分析：简要描述图片内容]
```

## 输出格式

最终返回给用户的内容：

```
# {文章标题}

{正文内容，其中 [IMAGE_N] 已替换为图片分析结果}
```

## 脚本返回的 JSON 结构

```json
{
  "title": "文章标题",
  "text": "正文纯文本，含 [IMAGE_0]、[IMAGE_1] 等占位符",
  "images": [
    {
      "index": 0,
      "filename": "img_000.jpg",
      "path": "/tmp/wechat-images/img_000.jpg",
      "original_url": "https://...",
      "workspace_path": "/home/node/.openclaw/workspace/img_000.jpg"
    }
  ],
  "image_count": 9,
  "output_dir": "/tmp/wechat-images"
}
```

## 注意事项

- `web_fetch` 直接抓取会失败（桌面 UA 触发验证码），必须使用脚本
- 脚本自动过滤装饰性图片（图标、emoji、loading、placeholder、小于 1KB 的文件）
- 过滤后的图片全部下载和分析，无数量限制
- 图片下载失败时，对应条目的 `path` 为 null，跳过分析即可
