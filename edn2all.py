# 完成所有文本识别工作，暂未处理排序问题 2023-12-22
# 尚存在BUG：对字段「{:block/children ...}」报错，正则/文本替换均无法解决；通过清空「roam/excalidraw」页面内容解决了这个问题。最新版的Timeline各个最新edn已经可以完全识别了，PrismVision历史版本需要删除该字段才能正确使用。
# 通过去除文本「:entity/attrs #{}」实现了「{:block/children ...}」字段BUG的修复，至此，所有历史版本edn均实现读取。 2023-12-22 20:20
# 形式上实现了edn2md，暂时还有部分文本存在顺序问题。 2023-12-22 22:25
# 解决了排序问题 2023-12-23 00:41
# 优化了代码 2023-12-23 14:21
# V1.0 2023-12-23 16:56
# 屏蔽order_path字段以恢复对PrismVision的适配
# 增加了黑名单/白名单规则和页面目录 2023-12-23 21:39
# 增加了在指定路径自动寻找最新.edn文件的功能 2023-12-23 21:52
# 增加指定日期文件选取功能，并显示当前文件创建日期和体积信息 2023-12-23 22:35
# 优化页面生成时间：read_and_parse_edn_file占据了大文件处理的80%以上的时间，不太容易优化 2023-12-23 23:33
# 将markdown图片替换成可以控制尺寸的html图片，屏蔽codeblock 2023-12-24 00:53
# 补充对html导出的支持 2023-12-24 11:38
# 添加html中对字体和css等美化的支持 2023-12-24 16:51
# 优化代码显示，但会引起代码后有缩进行的显示异常；这似乎是markdown的显示逻辑，暂时不好解决 2023-12-24 19:11
# PrismVision中去除前一步的代码显示以方便整体展示 2023-12-24 19:49
# 修改html页面布局，目前除代码显示外，其他功能基本完备 2023-12-24 21:03
# 增加了word/pdf的导出支持，其中word支持较差 2023-12-23 21:58
# 修复匹配识别bug：edn_data = re.sub(r'(:entity/attrs).*?\}\]\}', r'\1', edn_data) 2023-12-25 12：16
# 添加转译谷歌图床到阿里云/本地的可选支持 2023-12-25 15:21
# 添加了对Github备份的支持 2023-12-25 16:40
# 尝试修复html行内代码显示异常，未果 2023-12-25 18:37
# 添加引用文本显示，并用下划线标记引文；优化代码 2023-12-25 21:07
# 重新启用code block，当前代码段仅支持顶格显示，前后一行必须顶格：这是markdown的代码显示规范 2023-12-25 23:38
# 优化图片链接![xx]()的识别和html的todo显示 2023-12-26 14:34
# 下一步计划：找出read_and_parse_edn_file(file_path)耗时的原因 -> edn_format.loads(edn_data)函数大量占用时间所致 2023-12-26 15:17
# 优化文件读取子函数 2023-12-26 16:18
# 修复html图片居中同步bug 2023-12-28 15:10
# 优化代码分布，删去效果不太好的PDF和docx导出 2024-06-17 22:22

import edn_format
import json
import re
from datetime import datetime, timezone, timedelta
import time  # 导入 time 模块
import os
import markdown


def get_file_info(filepath): # 获取文件信息
    # 获取文件的创建时间
    creation_time = os.path.getctime(filepath)
    formatted_creation_time = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")

    # 获取文件的体积（字节），并转换为 MB
    file_size_bytes = os.path.getsize(filepath)
    file_size_mb = file_size_bytes / (1024 * 1024)

    return formatted_creation_time, file_size_mb

def find_latest_edn_file(folder_path, specific_date=None): # 选取指定日期的.edn文件
    latest_time = None
    latest_file = None
    specific_date_time = None
    exact_match_found = False

    if specific_date:
        try:
            specific_date_time = datetime.strptime(specific_date, "%Y-%m-%d").timestamp()
        except ValueError:
            print("指定日期格式错误，格式应为 YYYY-MM-DD")
            return None, False

    for filename in os.listdir(folder_path):
        if filename.endswith(".edn"):
            filepath = os.path.join(folder_path, filename)
            file_time = os.path.getmtime(filepath)

            if specific_date_time:
                midnight_time = datetime.fromtimestamp(file_time).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
                if midnight_time > specific_date_time:
                    continue

                if midnight_time == specific_date_time:
                    exact_match_found = True

            if latest_time is None or file_time > latest_time:
                latest_time = file_time
                latest_file = filepath
    
    # 显示文件信息
    if latest_file: 
        if exact_match_found:
            print(f"选定的 .edn 文件:\n {edn_path}")
        else:
            print(f"未找到指定日期 ({specific_date}) 的文件，选择最接近日期的文件: \n{latest_file}")

        # 获取并打印文件的创建时间和体积
        creation_time, file_size = get_file_info(latest_file)
        print(f"文件创建时间: {creation_time} 文件体积: {file_size:.3f} MB")
    else:
        print("在指定日期之前没有找到任何 .edn 文件")

    return latest_file

def read_and_parse_edn_file(file_path): # 大文件处理很耗时！！！
    with open(file_path, 'r', encoding='utf-8') as file:
        edn_data = file.read()
        # 数据清洗
        # edn_data = re.sub(r':entity/attrs #{}', '', edn_data)
        ## edn_data = re.sub(r'(:entity/attrs).*?\}\]\}', r'\1', edn_data)
        ## edn_data = re.sub(r'(:entity/attrs) #{\[{.*?}\]}', r'\1', edn_data, flags=re.DOTALL)
        edn_data = re.sub(r'(:entity/attrs)\s*#{\[{(.*?)}\]}', r'\1', edn_data, flags=re.DOTALL) # 支持Github
        edn_data = re.sub(r'#datascript/DB', '', edn_data).replace('#', '**TaG**')

        return edn_format.loads(edn_data)

def convert_edn_to_json(data):
    if isinstance(data, edn_format.immutable_dict.ImmutableDict):
        new_dict = {}
        for k, v in data.items():
            if isinstance(k, list):
                key = tuple(convert_edn_to_json(item) for item in k)  # 将列表转换为元组
            else:
                key = convert_edn_to_json(k)
            new_dict[key] = convert_edn_to_json(v)
        return new_dict
    elif isinstance(data, edn_format.immutable_list.ImmutableList):
        return [convert_edn_to_json(v) for v in data]
    elif isinstance(data, edn_format.Keyword):
        return str(data)
    elif isinstance(data, list):
        return [convert_edn_to_json(v) for v in data]
    else:
        return data

def convert_timestamp_to_utc8(timestamp_ms): # 转换时间进制
    # 将毫秒转换为秒
    timestamp_sec = timestamp_ms / 1000.0
    # 将时间戳转换为UTC时间
    utc_time = datetime.utcfromtimestamp(timestamp_sec)
    # 转换为UTC+8时间
    utc8_time = utc_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
    return utc8_time.strftime('%Y-%m-%d %H:%M:%S')

def parse_datoms(datoms):
    block_data = {}
    for datom in datoms:
        if len(datom) != 4:
            continue

        block_id, attribute, value, _ = datom
        if block_id not in block_data:
            block_data[block_id] = {
                "id": block_id,
                "uid": None,
		"create_time": None,
                "page": None,
                "parents": [],
                "children": [],
                "order": None,
                "string": None,
                "heading": 0,  # 默认值为 0
            }

        if attribute == ":block/uid":
            block_data[block_id]["uid"] = value
        elif attribute == ":create/time":
            utc8_time = convert_timestamp_to_utc8(value)
            block_data[block_id]["create_time"] = utc8_time
        elif attribute == ":block/page":
            block_data[block_id]["page"] = value
        elif attribute == ":block/parents":
            block_data[block_id]["parents"].append(value)
        elif attribute == ":block/children":
            block_data[block_id]["children"].append(value)
        elif attribute == ":block/order":
            block_data[block_id]["order"] = value
        elif attribute == ":block/string":
            block_data[block_id]["string"] = value
        elif attribute == ":block/heading":
            block_data[block_id]["heading"] = value

    return [data for data in block_data.values() if data["string"] is not None]

def parse_datoms_for_pages(datoms):
    page_data = {}
    for datom in datoms:
        if len(datom) != 4:
            continue

        block_id, attribute, value, _ = datom

        # 确保block_id在page_data中
        if block_id not in page_data:
            page_data[block_id] = {
                "id": block_id,
                "uid": None,
                "title": None,
                "children": [],
            }

        # 提取相关属性
        if attribute == ":block/uid":
            page_data[block_id]["uid"] = value
        elif attribute == ":node/title":
            page_data[block_id]["title"] = value
        elif attribute == ":block/children":
            page_data[block_id]["children"].append(value)

    # 只返回有标题且有子项的页面
    return [data for data in page_data.values() if data["title"] is not None and data["children"]]

def build_blocks_dict(datoms):
    blocks = {}
    for datom in datoms:
        if len(datom) != 4:
            continue

        block_id, attribute, value, _ = datom
        if block_id not in blocks:
            blocks[block_id] = {
                "id": block_id,
                "uid": None,
                "string": None,
                "children": [],
                "parents": [],
                "order": None,
                # "order_path": [],  # 新增字段
                "heading": 0,  # 默认值为 0
                "text_align": None,
                "refs": [],
            }

        if attribute == ":block/uid":
            blocks[block_id]["uid"] = value
        elif attribute == ":block/string":
            blocks[block_id]["string"] = value
        elif attribute == ":block/children":
            blocks[block_id]["children"].append(value)
        elif attribute == ":block/parents":
            blocks[block_id]["parents"].append(value)
        elif attribute == ":block/order":
            blocks[block_id]["order"] = value
        elif attribute == ":block/heading":
            blocks[block_id]["heading"] = value
        elif attribute == ":block/text-align":
            blocks[block_id]["text_align"] = value
        elif attribute == ":block/refs":
            blocks[block_id]["refs"] = value

    return blocks

def process_blocks(blocks):
    uid_to_string_map = {block['uid']: block['string'] for block in blocks.values() if block['uid']}
    
    for block in blocks.values():
        if block['string']:
            # Find all occurrences of ((uid)) in the string
            uids_in_string = re.findall(r'\(\((.*?)\)\)', block['string'])
            for uid in uids_in_string:
                if uid in uid_to_string_map:
                    # Replace ((uid)) with the string of the referenced block
                    block['string'] = block['string'].replace(f"(({uid}))", '<u>' + uid_to_string_map[uid] + '</u>')

def build_page_content(block_id, blocks, level=0): # code block修改的位置
    block = blocks[block_id]
    indent = ' ' * (4 * level)
    heading_level = block.get('heading', 0)
    heading_prefix = '#' * (heading_level + 1) + ' ' if heading_level > 0 else ''

    content = block['string']
    
    # 代码段处理 
    content = re.sub(r'```(.*?)```', r'```\1\n```\n', content, flags=re.DOTALL)

    # 代码段删除
    # content = re.sub(r'```(.*?)```', r'```css\n deleted code```\n', content, flags=re.DOTALL)
    content = re.sub(r'202*\*\*.*?weathercard', 'year\*\*', content, flags=re.DOTALL)

    # 如果 :block/text-align 为 center，则在两边添加 <center>
    if block.get('text_align') == 'center': # and not content.startswith('!['):
        content = f"<center>{content}</center>"
        content = content.replace("^^", "<mark>").replace("__", "<i>").replace("**", "<b>")

    # 如果字符串以 '>' 开头，添加额外的换行符
    if content.startswith('>'):
        content += '\n'
    comma='- '
    
    # 缩进和内容：PrismVision中需要去除if语句！！！
    # if content.startswith('```'):
    #     content = f"{content}\n"
    # if not content.startswith('```'):
    content = f"{indent}{comma}{heading_prefix}{content}\n"

    for child_id in sorted(block["children"], key=lambda id: blocks[id]["order"]):
        content += build_page_content(child_id, blocks, level + 1)

    return content

def is_page_allowed(page, allowed_uids, allowed_titles, blocked_uids, blocked_titles):
    # 如果白名单不为空，且页面不在白名单中，则返回 False
    if allowed_uids or allowed_titles:
        if page["uid"] not in allowed_uids and page["title"] not in allowed_titles:
            return False

    # 如果页面在黑名单中，则返回 False
    if page["uid"] in blocked_uids or page["title"] in blocked_titles:
        return False

    # 在其他情况下，返回 True
    return True

########################## 读取 EDN 文件 ########################################
################################################################################

# 启动计时
start_time = time.time()

## 初始化参数
specific_date=None
blocked_uids = []
blocked_titles = []
allowed_uids = []
allowed_titles = []

## 参数设定
# specific_date = "2022-09-25"  # 例如 '2023-12-25'，如果不需要指定日期，则设为 None

# 指定文件夹路径自动寻找文件
folder_path = '/Users/lukesky/Library/Application Support/Roam Research/backups/InsightSphere/'
# folder_path = '/Users/lukesky/Library/Application Support/Roam Research/backups/PrismVision/'
# folder_path = '/Users/lukesky/Touch/Git/roam-snapshot/edn/' # folder_path = '/Users/lukesky/工作台'

# 黑名单与白名单
blocked_uids = ["uid1", "uid2", "uid3"]  # 需要屏蔽的页面UID列表
blocked_titles = ["W/S/roam/css", "title2", "title3"]  # 需要屏蔽的页面标题列表
# allowed_uids = ["Xj7YD_MxR", "", "mGBUMYZiW"]  # 需要显示的页面UID列表
# allowed_titles = ["W/S/roam/css","Inbo", "archai",  "审阅测试"]  # 需要显示的页面标题列表

## 导出文件夹
output_path = '/Users/lukesky/RR/output'  # 替换为实际的文件夹路径

################################################################################
################################################################################


# 查找最新的 .edn 文件
edn_path = find_latest_edn_file(folder_path, specific_date) 
# edn_path = '/Users/lukesky/Touch/Git/roam-snapshot/edn/PrismVision.edn'
# edn_path = '/Users/lukesky/Touch/Git/roam-snapshot/edn/InsightSphere.edn'

# 解析 EDN 数据 耗时22.5s/27s
parsed_data = read_and_parse_edn_file(edn_path)

# 转换为标准Python数据结构 耗时4s/27s
json_ready_data = convert_edn_to_json(parsed_data)

# 解析 datoms 部分 耗时0.1s/27s
datoms = json_ready_data.get(":datoms", [])


################## markdown

# 解析datoms以获取页面信息
parsed_pages = parse_datoms_for_pages(datoms)

# 构建块信息字典
blocks = build_blocks_dict(datoms)
process_blocks(blocks)

# 处理每个页面
pages_content = []
for page in parsed_pages:
    if not is_page_allowed(page, allowed_uids, allowed_titles, blocked_uids, blocked_titles):
        continue
    
    children = page["children"]
    # 检查是否只有一个 child 且该 child 的 string 仅包含空格
    if len(children) == 1 and not blocks[children[0]]['string'].strip():
        continue  # 如果满足条件，跳过这个页面
    
    page_content = f"# {page['title']}\n"
    # 确保第一级块按照 order 排序
    sorted_children = sorted(page["children"], key=lambda id: blocks[id]["order"])
    for child_id in sorted_children:
        page_content += build_page_content(child_id, blocks)
    
    # 还原每个页面的 Tag
    page_content = page_content.replace('**TaG**', '#')
    # Typora语法
    page_content = page_content.replace("^^", "==").replace("__", "_").replace("---", "——————————————— \n")
    page_content = page_content.replace("{{[[DONE]]}}", "- [x] ").replace("{{[[TODO]]}}", "- [ ] ")
    
    # 谷歌图床转移到阿里云/本地文件夹
    # # page_content = re.sub(r'https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2FPrismVision%2F(.*?)\?alt=media&token=.*?\)', r'https://ideapply.oss-cn-nanjing.aliyuncs.com/img/\1)', page_content, flags=re.DOTALL) #阿里云
    # page_content = re.sub(r'https://firebasestorage.googleapis.com/v0/b/firescript-577a2.appspot.com/o/imgs%2Fapp%2FPrismVision%2F(.*?)\?alt=media&token=.*?\)', r'/Users/lukesky/roam_image/PrismVision/images/PrismVision/\1)', page_content, flags=re.DOTALL) #本地

    # 将 Markdown 格式的图片链接转换为 HTML <img> 标签
    # page_content = re.sub(r'!\[.*?\]\((.*?)\)', r'<img src="\1" style="zoom:30%" />', page_content)
    page_content = re.sub(r'!\[.*?\]\((.*?)\)', r'<img src="\1" width="400px" />', page_content)


    pages_content.append(page_content)

# 构建目录信息
directory_content = "# 目录\n\n"
for page in parsed_pages:
    if is_page_allowed(page, allowed_uids, allowed_titles, blocked_uids, blocked_titles):
        directory_content += f"- {page['title']} (UID: {page['uid']}, ID: {page['id']})\n"
directory_content += "\n---\n\n"

page_content = directory_content + '\n'.join(pages_content)
page_content_toc = '[TOC]\n'+ directory_content +'\n'.join(pages_content)

# 指定文件夹路径和文件名
file_name = 'pages_text_output.md'
file_path = os.path.join(output_path, file_name)

# 创建文件夹（如果不存在）
os.makedirs(output_path, exist_ok=True)

# 将结果写入文件
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(page_content_toc)

################## html

def process_format_content(markdown_content): # 处理页面内容，转义 #Tag  处理待办事项
    # 处理页面内容，转义 #Tag
    markdown_content = re.sub(r'#(\w+)', r'🏷️\1', markdown_content)
    markdown_content = re.sub(r'#\.(\w+)', r'🏷️.\1', markdown_content)
    markdown_content = re.sub(r'#\[\[(\w+)', r'🏷️\[\[\1', markdown_content)
    markdown_content = re.sub(r'==(.*?)==', r'<mark>\1</mark>', markdown_content)
    markdown_content = re.sub(r'~~(.*?)~~', r'<del>\1</del>', markdown_content, flags=re.DOTALL)
    markdown_content = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>\n', markdown_content, flags=re.DOTALL)
    # markdown_content = re.sub(r'`\{\{.*?\}\}`', r'`\{\{\1\}\}`\n', markdown_content, flags=re.DOTALL) # 修复行内代码换行问题
    # markdown_content = re.sub(r'}}\s`\n', r'}}`\n\n' , markdown_content, flags=re.DOTALL)
    # markdown_content = re.sub(r'`\n', r'`\n\n' , markdown_content, flags=re.DOTALL) # 修复了行内代码换行问题

    # 替换未完成的待办事项
    markdown_content = re.sub(r'\- \[ \]', r'- <input type="checkbox" class="todo-checkbox" disabled>', markdown_content)
    # 替换已完成的待办事项
    markdown_content = re.sub(r'\- \[x\]', r'- <input type="checkbox" class="todo-checkbox" checked disabled>', markdown_content)
    return markdown_content

# 处理页面内容，转义 #Tag 处理待办事项
page_content = process_format_content(page_content)

# 转换 Markdown 为 HTML
html_content = markdown.markdown(page_content)
html_content = html_content.replace('🏷️', '#')

# 自定义CSS样式
custom_css = """
    @font-face {
        font-family: "CangErJinKai01-9128-W03-4";
        src: url('https://ideapply.oss-cn-nanjing.aliyuncs.com/fonts/CangErJinKai01-9128-W03-4.otf') format("opentype");
    }
    body {
        font-family: "CangErJinKai01-9128-W03-4", sans-serif;
        line-height: 1.6;
        font-size: 17px;
        padding: 1rem;
        margin-left: auto;  /* 左边距自动 */
        margin-right: auto; /* 右边距自动 */
        width: 70%;        /* 设定一个宽度 */
        max-width: 1024px;
    }
    h1, h2, h3, h4, h5, h6 {
        margin-top: 1.2em;
        margin-bottom: 0.6em;
    }
    p {
        margin-top: 0.5em;
        margin-bottom: 0.5em;
    }
    ul, ol {
        margin-top: 0.5em;
        margin-bottom: 0.5em;
        padding-left: 20px;
    }

    .todo-checkbox {
        margin-right: 0.25em;
    }

    /* 自动换行 */
    body {
        word-wrap: break-word; /* 旧的浏览器 */
        overflow-wrap: break-word; /* 新的标准 */
    }
    pre {
        white-space: pre-wrap; /* 允许在预格式化文本中自动换行 */
    }

    /* 自适应页边距 */
    #write {
        max-width: 860px;  /* 设置内容区的最大宽度 */
        margin: 0 auto;    /* 上下保持为0，左右自动调整，实现居中 */
        padding: 30px;     /* 内边距，可以根据需要调整 */
        padding-bottom: 100px; /* 底部内边距 */
    }

    /* 响应式设计，根据不同屏幕宽度调整最大宽度 */
    @media only screen and (min-width: 1400px) {
        #write {
            max-width: 1024px; /* 大屏幕时的最大宽度 */
        }
    }

    @media only screen and (min-width: 1800px) {
        #write {
            max-width: 1200px; /* 更大屏幕时的最大宽度 */
        }
    }

    """

html_with_custom_font = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{custom_css}</style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """

# 指定文件夹路径和文件名
file_name = 'pages_html_output.html'
file_path = os.path.join(output_path, file_name)

# 创建文件夹（如果不存在）
os.makedirs(output_path, exist_ok=True)

# 使用 UTF-8 编码将 HTML 写入文件
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(html_with_custom_font)


# 结束计时并打印运行时间
end_time = time.time()
print(f"Program finished in {end_time - start_time:.3f} seconds")
