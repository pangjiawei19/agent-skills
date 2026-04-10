#!/usr/bin/env node

/**
 * GitHub Trending 报告生成脚本
 * 
 * 使用方法：
 * 1. 使用 browser 工具打开 https://github.com/trending
 * 2. 使用 browser.snapshot 获取页面内容
 * 3. 解析项目信息
 * 4. 生成格式化报告
 */

// 示例：从 browser snapshot 结果中提取项目信息的解析逻辑
// 实际使用时，需要在 Skill 中调用 browser 工具

const GITHUB_TRENDING_URL = 'https://github.com/trending';

// 项目信息结构
interface ProjectInfo {
  rank: number;
  owner: string;
  name: string;
  totalStars: number;
  starsToday: number;
  language: string;
  description: string;
  url: string;
}

// 解析 browser snapshot 结果中的项目信息
function parseTrendingProjects(snapshotContent: string): ProjectInfo[] {
  // 从 snapshot 的 aria-ref 元素中提取项目信息
  // 实际解析逻辑需要根据 snapshot 返回的具体结构调整
  
  const projects: ProjectInfo[] = [];
  
  // 示例解析逻辑（伪代码）
  // 1. 查找所有 article 元素（每个项目一个 article）
  // 2. 提取 heading 中的 owner/name
  // 3. 提取 star 链接中的总 Star 数
  // 4. 提取 "stars today" 文本
  // 5. 提取 language 和 description
  
  return projects;
}

// 生成趋势分析
function generateAnalysis(projects: ProjectInfo[]): string {
  const languages = new Map<string, number>();
  const keywords = new Map<string, number>();
  
  // 统计语言分布
  projects.forEach(p => {
    languages.set(p.language, (languages.get(p.language) || 0) + 1);
  });
  
  // 从描述中提取关键词（AI、Agent、browser、code 等）
  const keywordPatterns = ['AI', 'Agent', 'browser', 'code', 'CLI', 'framework', 'engine', 'database'];
  projects.forEach(p => {
    const desc = p.description.toLowerCase();
    keywordPatterns.forEach(kw => {
      if (desc.includes(kw.toLowerCase())) {
        keywords.set(kw, (keywords.get(kw) || 0) + 1);
      }
    });
  });
  
  // 生成分析报告
  let analysis = '## 📊 今日趋势分析\n\n';
  
  // 热门关键词
  const topKeywords = Array.from(keywords.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);
  
  if (topKeywords.length > 0) {
    analysis += `### 🔥 热门关键词\n\n`;
    analysis += topKeywords.map(([kw, count]) => `- **${kw}** (${count} 个项目提及)`).join('\n');
    analysis += '\n\n';
  }
  
  // 技术栈分布
  analysis += `### 技术栈分布\n\n`;
  const sortedLanguages = Array.from(languages.entries()).sort((a, b) => b[1] - a[1]);
  sortedLanguages.forEach(([lang, count]) => {
    const percentage = Math.round((count / projects.length) * 100);
    analysis += `- **${lang}**: ${count} 个项目 (${percentage}%)\n`;
  });
  analysis += '\n';
  
  // 观察与洞察
  analysis += `### 💡 观察\n\n`;
  analysis += `- 今日最热项目：**${projects[0]?.name}**，单日增长 ${projects[0]?.starsToday.toLocaleString()} 星\n`;
  analysis += `- 平均每个项目今日增长：${Math.round(projects.reduce((sum, p) => sum + p.starsToday, 0) / projects.length).toLocaleString()} 星\n`;
  
  return analysis;
}

// 生成完整报告
function generateReport(projects: ProjectInfo[]): string {
  let report = '';
  
  projects.forEach((p, index) => {
    report += `---\n\n`;
    report += `**${index + 1}. ${p.name}** ⭐ ${p.totalStars.toLocaleString()} (+${p.starsToday.toLocaleString()} 今日)\n`;
    report += `- **链接：** [${p.owner}/${p.name}](https://github.com/${p.owner}/${p.name})\n`;
    report += `- **语言：** ${p.language}\n`;
    report += `- **描述：** ${p.description}\n`;
  });
  
  report += `\n---\n\n`;
  report += generateAnalysis(projects);
  
  return report;
}

module.exports = {
  GITHUB_TRENDING_URL,
  parseTrendingProjects,
  generateAnalysis,
  generateReport
};
