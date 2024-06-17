# EDN 文件转换工具

## 描述
此 Python 脚本用于处理 Roam Research 的 EDN 文件，提取数据，进行数据清洗和转换，并将数据导出为 Markdown 和 HTML 格式。它支持复杂的数据结构处理，并处理自定义格式化，包括内联引用和 Markdown 语法的处理。

## 功能
- 在目录中获取并处理最新或指定日期的 EDN 文件。
- 将 EDN 数据转换为类 JSON 结构，并处理层次化数据块。
- 使用自定义格式在 Markdown 或 HTML 中导出数据。
- 根据可自定义的白名单和黑名单过滤数据。
- 可自定义 HTML 导出的 CSS 布局
- Markdown 格式自定义部分基于 Typora 中语法

## 安装
克隆此仓库到您的本地机器：
```bash
git clone https://github.com/ideapply/edn-file-processor.git
