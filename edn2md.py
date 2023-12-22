# 完成所有文本识别工作，暂未处理排序问题 2023-12-22
# 尚存在BUG：对字段「{:block/children ...}」报错，正则/文本替换均无法解决；通过清空「roam/excalidraw」页面内容解决了这个问题。最新版的Timeline各个最新edn已经可以完全识别了，PrismVision历史版本需要删除该字段才能正确使用。
# 通过去除文本「:entity/attrs #{}」实现了「{:block/children ...}」字段BUG的修复，至此，所有历史版本edn均实现读取。 2023-12-22 20:20
# 形式上实现了edn2md，暂时还有部分文本存在顺序问题。 2023-12-22 22:25

import edn_format
import json
import re
from datetime import datetime, timezone, timedelta

def convert_timestamp_to_utc8(timestamp_ms):
    # 将毫秒转换为秒
    timestamp_sec = timestamp_ms / 1000.0
    # 将时间戳转换为UTC时间
    utc_time = datetime.utcfromtimestamp(timestamp_sec)
    # 转换为UTC+8时间
    utc8_time = utc_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
    return utc8_time.strftime('%Y-%m-%d %H:%M:%S')

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

    return [data for data in block_data.values() if data["string"] is not None]

### 读取 EDN 文件
edn_path = '/Users/lukesky/Library/Application Support/Roam Research/backups/InsightSphere/backup-InsightSphere-2023-12-20-15-02-50.edn'

print(edn_path)

with open(edn_path, 'r', encoding='utf-8') as file:
    edn_data = file.read()

# 使用正则表达式移除复杂的 :entity/attrs 字段
edn_data = re.sub(r':entity/attrs #{}', '', edn_data)
pattern = r'(:entity/attrs).*?\}\]\}'
edn_data = re.sub(pattern, r'\1', edn_data)

# 利用正则表达式/文本替换，移除特定代码段（目前无效）
# to_remove="\{\:block\/children \.\.\.\}"
# edn_data=edn_data.replace(to_remove,'')

# pattern3 = r'{:block/children ...}'
# edn_data = re.sub(pattern3, '', edn_data, re.DOTALL, flags=re.DOTALL)

# 删除所有代码段
# pattern2 = r'(```).*?```'
# edn_data = re.sub(pattern2, '```css\n deleted code```', edn_data, re.DOTALL, flags=re.DOTALL)

# 移除特定的标签和可能的解析干扰字符
edn_data = re.sub(r'#datascript/DB', '', edn_data)
edn_data = edn_data.replace('#', '') 



# 解析 EDN 数据
parsed_data = edn_format.loads(edn_data)

# 转换为标准Python数据结构
json_ready_data = convert_edn_to_json(parsed_data)

# 解析 datoms 部分
datoms = json_ready_data.get(":datoms", [])
parsed_datoms = parse_datoms(datoms)

# 手动构造每个数据项的JSON字符串
json_items = [json.dumps(item, ensure_ascii=False) for item in parsed_datoms]

# 将所有项连接在一起，每个项之间用逗号和换行符分隔
json_data = ',\n'.join(json_items)

# 保存为 JSON 文件
with open('output_file.json', 'w', encoding='utf-8') as json_file:
    json_file.write(json_data)

################## page

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
                "children": []
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

# 解析datoms以获取页面信息
parsed_pages = parse_datoms_for_pages(datoms)

# 转换为JSON
json_pages = [json.dumps(page, ensure_ascii=False) for page in parsed_pages]

# 将所有页面信息合并为一个字符串
json_pages_data = ',\n'.join(json_pages)

# 保存页面信息为JSON文件
with open('pages_output_file.json', 'w', encoding='utf-8') as pages_json_file:
    pages_json_file.write(json_pages_data)


######### content
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
                "order": None
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

    return blocks

def build_page_content(block_id, blocks, page_id):
    block = blocks[block_id]
    content = {"string": block["string"], "children": []}

    # 递归处理子块
    for child_id in sorted(block["children"], key=lambda id: blocks[id]["order"]):
        child_block = blocks[child_id]

        # 检查是否为当前页面或父块的直接子块
        if page_id in child_block["parents"] or block_id in child_block["parents"]:
            content["children"].append(build_page_content(child_id, blocks, page_id))

    return content

# 构建块信息字典
blocks = build_blocks_dict(datoms)

# 处理每个页面
pages_content = []
for page in parsed_pages:
    page_content = {
        "id": page["id"],
        "uid": page["uid"],
        "title": page["title"],
        "content": []
    }
    for child_id in page["children"]:
        page_content["content"].append(build_page_content(child_id, blocks, page["id"]))
    pages_content.append(page_content)

# 转换为JSON
json_pages_content = [json.dumps(page, ensure_ascii=False) for page in pages_content]

# 保存到文件
with open('pages_hierarchy_output_file.json', 'w', encoding='utf-8') as file:
    file.write(',\n'.join(json_pages_content))


###### txt

def build_page_content(block_id, blocks, level=0):
    block = blocks[block_id]
    indent = ' ' * (4 * level)  # 每层级增加4个空格缩进
    content = f"{indent}{block['string']}\n"

    # 递归处理子块
    for child_id in sorted(block["children"], key=lambda id: blocks[id]["order"]):
        content += build_page_content(child_id, blocks, level + 1)

    return content

# 构建块信息字典
blocks = build_blocks_dict(datoms)

# 处理每个页面
pages_content = []
for page in parsed_pages:
    page_content = f"Page: {page['title']}\n"
    for child_id in page["children"]:
        page_content += build_page_content(child_id, blocks)
    pages_content.append(page_content)

# 保存到文件
with open('pages_text_output.md', 'w', encoding='utf-8') as file:
    file.write('\n'.join(pages_content))
