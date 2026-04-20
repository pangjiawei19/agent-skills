/**
 * InfoQ AI&大模型频道资讯抓取脚本
 * 
 * 用法：在 browser snapshot 后解析页面内容
 */

// 配置
const CONFIG = {
  url: 'https://www.infoq.cn/topic/AI&LLM',
  defaultCount: 15,
  maxCount: 50
};

/**
 * 解析 browser snapshot 结果，提取资讯列表
 * @param {string} snapshot - browser snapshot 返回的文本
 * @param {number} count - 需要提取的条数
 * @returns {Array} 资讯列表 [{title, url, author?}]
 */
function parseSnapshot(snapshot, count = CONFIG.defaultCount) {
  const articles = [];
  
  // 匹配文章条目（基于 aria snapshot 结构）
  // 格式：heading "标题" [level=6] [ref=exx]: link "标题" [ref=exx]: /url: https://...
  const articleRegex = /heading "([^"]+)" \[level=6\][\s\S]*?link "[^"]+" \[ref=e\d+\]:[\s\S]*?\/url: (https:\/\/www\.infoq\.cn\/[^\s]+)/g;
  
  let match;
  while ((match = articleRegex.exec(snapshot)) !== null) {
    const [, title, url] = match;
    
    // 跳过导航菜单等非文章链接
    if (title === '首页' || title === 'AI 会议' || title === 'AI 课程' || 
        title === 'AI 应用' || title === '报告' || title === 'HarmonyOS' ||
        title === 'Snowflake' || title.includes('企业动态') || title.includes('行业深度')) {
      continue;
    }
    
    articles.push({
      title: title.trim(),
      url: url.trim()
    });
    
    if (articles.length >= count) {
      break;
    }
  }
  
  return articles;
}

/**
 * 格式化输出为简洁版
 * @param {Array} articles - 资讯列表
 * @returns {string} 格式化后的文本
 */
function formatSimple(articles) {
  let output = '**InfoQ AI&大模型 - 最新 ' + articles.length + ' 条资讯** 🦐\n\n';
  
  articles.forEach((article, index) => {
    output += `---\n\n`;
    output += `**${index + 1}. ${article.title}**\n`;
    output += `🔗 ${article.url}\n`;
  });
  
  output += `\n---`;
  return output;
}

/**
 * 格式化输出为详细版（含作者）
 * @param {Array} articles - 资讯列表
 * @param {string} snapshot - 原始 snapshot（用于提取作者）
 * @returns {string} 格式化后的文本
 */
function formatDetailed(articles, snapshot) {
  let output = '**InfoQ AI&大模型 - 最新 ' + articles.length + ' 条资讯** 🦐\n\n';
  
  articles.forEach((article, index) => {
    output += `---\n\n`;
    output += `**${index + 1}. ${article.title}**\n`;
    // TODO: 从 snapshot 中提取作者信息
    output += `🔗 ${article.url}\n`;
  });
  
  output += `\n---`;
  return output;
}

/**
 * 主函数
 * @param {Object} params - 参数
 * @param {string} params.snapshot - browser snapshot 返回的文本
 * @param {number} params.count - 条数
 * @param {string} params.format - 格式（simple/detailed）
 * @returns {string} 格式化后的输出
 */
function main(params) {
  const { snapshot, count = CONFIG.defaultCount, format = 'simple' } = params;
  
  const articles = parseSnapshot(snapshot, Math.min(count, CONFIG.maxCount));
  
  if (articles.length === 0) {
    return '❌ 未抓取到任何资讯，请检查页面结构是否变化';
  }
  
  if (format === 'detailed') {
    return formatDetailed(articles, snapshot);
  }
  
  return formatSimple(articles);
}

// 导出
module.exports = { parseSnapshot, formatSimple, formatDetailed, main, CONFIG };
