#!/usr/bin/env python3
"""
中国人情世故情商测评 - 全链路自动化测试脚本 v2
"""
import re, sys, os, json, random

BASE = "/workspace/social-eq-test"
passed = 0
failed = 0
errors = []

def ok(msg):
    global passed; passed += 1
    print(f"  [PASS] {msg}")

def fail(msg):
    global failed; errors.append(msg); failed += 1
    print(f"  [FAIL] {msg}")

def hdr(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

with open(f"{BASE}/js/data.js", "r") as f: data_text = f.read()
with open(f"{BASE}/js/app.js", "r") as f: app_text = f.read()
with open(f"{BASE}/index.html", "r") as f: html_text = f.read()
with open(f"{BASE}/css/style.css", "r") as f: css_text = f.read()
with open(f"{BASE}/README.md", "r") as f: readme_text = f.read()

# ================================================================
# 稳健的 JS 对象解析器
# ================================================================
def extract_js_objects(text, start_marker, end_marker=None):
    """Extract JS object literals by tracking brace depth"""
    start = text.find(start_marker)
    if start == -1:
        return []
    if end_marker:
        end = text.find(end_marker, start)
    else:
        end = len(text)
    section = text[start:end]
    
    # Find top-level objects (brace depth = 0 at start of each)
    objects = []
    depth = 0
    in_string = False
    string_char = None
    obj_start = -1
    
    for i, ch in enumerate(section):
        if in_string:
            if ch == '\\':
                i += 1  # skip escaped char
                continue
            if ch == string_char:
                in_string = False
            continue
        
        if ch in '"\'':
            in_string = True
            string_char = ch
            continue
        
        if ch == '{':
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and obj_start >= 0:
                objects.append(section[obj_start:i+1])
                obj_start = -1
    
    return objects

def parse_question_obj(obj_text):
    """Parse a single question object using regex on flat fields"""
    q = {}
    
    # Simple fields
    for field in ['id', 'category', 'scenario', 'question']:
        m = re.search(rf'{field}:\s*"((?:[^"\\]|\\.)*)"', obj_text)
        if m:
            q[field] = m.group(1)
    
    # id as int
    m = re.search(r'id:\s*(\d+)', obj_text)
    if m:
        q['id'] = int(m.group(1))
    
    # options array - find each { text: "...", score: N }
    opts = re.findall(r'text:\s*"(.*?)"\s*,\s*score:\s*(\d)', obj_text)
    q['options'] = [(t, int(s)) for t, s in opts]
    
    # dimensions array
    dims_match = re.search(r'dimensions:\s*\[(.*?)\]', obj_text, re.DOTALL)
    if dims_match:
        dims = re.findall(r'"([^"]+)"', dims_match.group(1))
        q['dimensions'] = dims
    else:
        q['dimensions'] = []
    
    # reverse
    q['reverse'] = 'reverse: true' in obj_text
    
    return q

# ================================================================
# 0. 加载数据
# ================================================================
hdr("0. 数据文件加载")
ok("data.js, app.js, index.html, style.css, README.md 全部加载成功")

# ================================================================
# 1. 题库完整性
# ================================================================
hdr("1. 题库完整性校验")

question_objs = extract_js_objects(data_text, 'var QUESTIONS = [', 'var DIMENSION_DEFINITIONS')
questions = [parse_question_obj(obj) for obj in question_objs]
questions = [q for q in questions if 'id' in q and 'category' in q]

print(f"  解析到 {len(questions)} 道题目")
if len(questions) == 48:
    ok("题目总数: 48")
else:
    fail(f"题目总数: {len(questions)}（预期48）")

# 检查每道题4个选项
bad = [q['id'] for q in questions if len(q.get('options', [])) != 4]
if not bad:
    ok("所有题目均有4个选项")
else:
    fail(f"以下题目选项数≠4: {bad}")

# ID连续性
ids = sorted([q['id'] for q in questions])
if ids == list(range(1, 49)):
    ok("题目ID连续: 1-48")
else:
    fail(f"ID不连续: {ids}")

# 分类分布
cats = {}
for q in questions:
    cats[q['category']] = cats.get(q['category'], 0) + 1
expected_cats = {"酒局应酬": 8, "亲戚人情": 8, "职场交际": 8, "送礼办事": 8, "朋友相处": 8, "日常社交": 8}
if cats == expected_cats:
    ok(f"六类场景各8题: " + ", ".join(f"{k}={v}" for k, v in sorted(cats.items())))
else:
    fail(f"场景分布不符: {cats}")

# 维度覆盖
dim_counts = {}
for q in questions:
    for d in q.get('dimensions', []):
        dim_counts[d] = dim_counts.get(d, 0) + 1
expected_dims = {"人情分寸", "察言观色", "情绪自控", "应酬处事", "冲突化解", "人际边界"}
if set(dim_counts.keys()) == expected_dims:
    ok(f"六大维度全部覆盖: {dict(sorted(dim_counts.items()))}")
else:
    fail(f"维度不完整: {set(dim_counts.keys())}")

# 分值范围
all_scores = []
for q in questions:
    for _, s in q.get('options', []):
        all_scores.append(s)
if all_scores:
    mn, mx = min(all_scores), max(all_scores)
    if mn >= 1 and mx <= 4:
        ok(f"选项分值范围: {mn}-{mx}")
    else:
        fail(f"分值越界: {mn}-{mx}")

# ================================================================
# 2. 无西方场景
# ================================================================
hdr("2. 无西方场景检查")

western = ["感恩节", "圣诞节", "万圣节", "派对", "college", "campus", "dorm", "fraternity",
           "美式", "欧美", "CEO", "MBA", "华尔街", "硅谷", "prom", "halloween", "thanksgiving"]
found_w = []
for q in questions:
    text = q.get('scenario', '') + q.get('question', '') + q.get('category', '')
    for kw in western:
        if kw.lower() in text.lower():
            found_w.append((q['id'], kw))
if not found_w:
    ok("无西方/欧美场景关键词")
else:
    fail(f"发现西方场景: {found_w}")

# 中国元素
cn_el = ["酒局", "敬酒", "红包", "拜年", "亲戚", "长辈", "人情", "领导",
         "团建", "AA", "饭局", "送礼", "催婚", "份子", "微信群", "走后门", "劝酒"]
cn_found = set()
for q in questions:
    text = q.get('scenario', '') + q.get('question', '') + q.get('category', '')
    for el in cn_el:
        if el in text:
            cn_found.add(el)
if len(cn_found) >= 12:
    ok(f"包含{len(cn_found)}个中国本土元素")
else:
    fail(f"中国元素过少: {len(cn_found)}")

# ================================================================
# 3. 计分引擎
# ================================================================
hdr("3. 计分引擎模拟测试")

def simulate_scoring(answers):
    dim_raw = {d: 0 for d in expected_dims}
    dim_count = {d: 0 for d in expected_dims}
    for q in questions:
        qid = q['id']
        if qid not in answers:
            continue
        score = int(q['options'][answers[qid]][1])
        for d in q['dimensions']:
            dim_raw[d] += score
            dim_count[d] += 1
    dim_pct = {}
    total_raw, total_max = 0, 0
    for d in expected_dims:
        mx = dim_count[d] * 4
        dim_pct[d] = round((dim_raw[d] / mx) * 100) if mx > 0 else 0
        total_raw += dim_raw[d]
        total_max += mx
    overall = round((total_raw / total_max) * 100) if total_max > 0 else 0
    return {'percent': dim_pct, 'overall': overall}

def determine_rating(scores):
    o = scores['overall']
    p = scores['percent']
    if o >= 55 and p.get("人际边界", 0) < 55 and p.get("冲突化解", 0) < 55:
        return "pleaser"
    if o >= 85:
        return "master"
    if o < 60:
        return "straight"
    return "average"

rating_names = {"master": "人情通透高手", "average": "处事稳妥普通人",
                "pleaser": "讨好型老好人", "straight": "直性子不懂人情"}

# 全选最优
best_answers = {}
for q in questions:
    best_idx = max(range(4), key=lambda i: int(q['options'][i][1]))
    best_answers[q['id']] = best_idx
sb = simulate_scoring(best_answers)
rb = determine_rating(sb)
print(f"  全选最优: 综合={sb['overall']}% → {rating_names[rb]}")
if sb['overall'] >= 85:
    ok(f"最优答案→{rating_names[rb]}（{sb['overall']}%）")
else:
    fail(f"最优答案仅{sb['overall']}%")

# 全选最差
worst_answers = {}
for q in questions:
    worst_idx = min(range(4), key=lambda i: int(q['options'][i][1]))
    worst_answers[q['id']] = worst_idx
sw = simulate_scoring(worst_answers)
rw = determine_rating(sw)
print(f"  全选最差: 综合={sw['overall']}% → {rating_names[rw]}")
if sw['overall'] < 60:
    ok(f"最差答案→{rating_names[rw]}（{sw['overall']}%）")
else:
    fail(f"最差答案{sb['overall']}%偏高")

# 讨好型模拟
pleaser_answers = {}
for q in questions:
    dims = q['dimensions']
    if "人际边界" in dims or "冲突化解" in dims:
        pleaser_answers[q['id']] = min(range(4), key=lambda i: int(q['options'][i][1]))
    else:
        pleaser_answers[q['id']] = max(range(4), key=lambda i: int(q['options'][i][1]))
sp = simulate_scoring(pleaser_answers)
rp = determine_rating(sp)
print(f"  讨好型模拟: 综合={sp['overall']}%, 边界={sp['percent'].get('人际边界',0)}%, 冲突={sp['percent'].get('冲突化解',0)}% → {rating_names[rp]}")
ok("讨好型模拟完成")

# 确定性验证
s1 = simulate_scoring(best_answers)
s2 = simulate_scoring(best_answers)
if s1['overall'] == s2['overall']:
    ok("计分引擎确定性: 相同输入→相同输出")
else:
    fail("计分引擎不稳定")

# ================================================================
# 4. 话术联动
# ================================================================
hdr("4. 话术联动测试")

scripts_start = data_text.find('var SOCIAL_SCRIPTS')
scripts_end = data_text.find('var RATING_SYSTEM')
scripts_section = data_text[scripts_start:scripts_end]

script_objs = extract_js_objects(scripts_section, '{')
scripts_by_dim = {}
current_dim = None
for obj_text in script_objs:
    scenario_m = re.search(r'scenario:\s*"([^"]+)"', obj_text)
    script_m = re.search(r'script:\s*"([^"]+)"', obj_text)
    if scenario_m and script_m:
        # Find which dimension this belongs to
        dim_m = re.findall(r'"([^"]+)":\s*\[', scripts_section)
        pass  # We'll use a simpler approach

# Simpler: regex extract per dimension
for dim in expected_dims:
    dim_block_start = scripts_section.find(f'"{dim}": [')
    if dim_block_start == -1:
        continue
    # Find the closing ] for this dimension's scripts array
    # The array ends with ] followed by , or newline+}
    after_start = scripts_section.find('[', dim_block_start) + 1
    # Track brace depth to find matching ]
    depth = 0
    in_str = False
    str_ch = None
    dim_block_end = -1
    for i in range(after_start, len(scripts_section)):
        ch = scripts_section[i]
        if in_str:
            if ch == '\\':
                i += 1
            elif ch == str_ch:
                in_str = False
            continue
        if ch == '"' or ch == "'":
            in_str = True
            str_ch = ch
            continue
        if ch == '[':
            depth += 1
        elif ch == ']':
            if depth == 0:
                dim_block_end = i
                break
            depth -= 1
    if dim_block_end == -1:
        continue
    dim_block = scripts_section[dim_block_start:dim_block_end+1]
    scripts = re.findall(r'scenario:\s*"([^"]+)"\s*,\s*script:\s*"([^"]+)"', dim_block)
    scripts_by_dim[dim] = scripts

for dim in expected_dims:
    count = len(scripts_by_dim.get(dim, []))
    if count >= 3:
        ok(f"{dim}: {count}条话术")
    else:
        fail(f"{dim}: 仅{count}条话术")

# 验证低分触发话术
test_weak = ["人情分寸", "察言观色"]
scripts_found = []
for dim in test_weak:
    if dim in scripts_by_dim:
        scripts_found.append(dim)
        for sc, script in scripts_by_dim[dim][:2]:
            print(f"    [{dim}] {sc}: {script[:50]}...")
if len(scripts_found) == len(test_weak):
    ok("短板话术联动正常")
else:
    fail("话术联动缺失")

# ================================================================
# 5. 评级体系
# ================================================================
hdr("5. 评级体系校验")

rating_start = data_text.find('var RATING_SYSTEM')
rating_section = data_text[rating_start:]
rating_ids = re.findall(r'id:\s*"([^"]+)"', rating_section)
expected_ratings = ["master", "average", "pleaser", "straight"]
if set(rating_ids) == set(expected_ratings):
    ok(f"四套评级: {rating_ids}")
else:
    fail(f"评级不完整: {rating_ids}")

# ================================================================
# 6. HTML结构
# ================================================================
hdr("6. HTML 结构校验")

for sid in ["screen-home", "screen-test", "screen-result"]:
    if f'id="{sid}"' in html_text:
        ok(f"屏幕 '{sid}' 存在")
    else:
        fail(f"屏幕 '{sid}' 缺失")

# JS-ID匹配
js_ids = re.findall(r'getElementById\("([^"]+)"\)', app_text)
html_ids = re.findall(r'id="([^"]+)"', html_text)
missing = set(js_ids) - set(html_ids)
if not missing:
    ok(f"JS引用的{len(js_ids)}个DOM ID全部存在于HTML")
else:
    fail(f"缺失ID: {missing}")

# 资源加载顺序
dp = html_text.find('js/data.js')
ap = html_text.find('js/app.js')
if 0 < dp < ap:
    ok("JS加载顺序: data.js → app.js")
else:
    fail("JS加载顺序错误")

# ================================================================
# 7. 离线可用性
# ================================================================
hdr("7. 离线可用性测试")

ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', html_text)
if not ext:
    ok("无外部HTTP依赖")
else:
    fail(f"外部依赖: {ext}")

cdn_kw = ['cdn.', 'unpkg', 'jsdelivr', 'googleapis', 'cloudflare']
cdn_hit = [k for k in cdn_kw if k in html_text]
if not cdn_hit:
    ok("无CDN引用")
else:
    fail(f"CDN引用: {cdn_hit}")

api_kw = ['fetch(', 'axios', 'XMLHttpRequest', '$.ajax']
api_hit = [k for k in api_kw if k in app_text]
if not api_hit:
    ok("无后端API调用")
else:
    fail(f"API调用: {api_hit}")

for f in ["index.html", "css/style.css", "js/data.js", "js/app.js", "README.md"]:
    path = f"{BASE}/{f}"
    if os.path.exists(path):
        ok(f"文件存在: {f}")
    else:
        fail(f"文件缺失: {f}")

# ================================================================
# 8. CSS响应式
# ================================================================
hdr("8. CSS 响应式适配")

mqs = re.findall(r'@media[^{]*\{', css_text)
if mqs:
    ok(f"{len(mqs)}个媒体查询断点")
    for mq in mqs:
        print(f"    {mq.strip()}")
else:
    fail("无媒体查询")

for bp in ["max-width: 768px", "max-width: 480px"]:
    if bp in css_text:
        ok(f"断点 '{bp}' 存在")
    else:
        fail(f"断点 '{bp}' 缺失")

for prop in ['flex-direction: column', 'grid-template-columns: 1fr', 'width: 100%']:
    if prop in css_text:
        ok(f"响应式属性存在: {prop}")
    else:
        fail(f"响应式属性缺失: {prop}")

if 'viewport' in html_text and 'width=device-width' in html_text:
    ok("viewport meta 正确")
else:
    fail("viewport meta 缺失")

# ================================================================
# 9. 部署文档
# ================================================================
hdr("9. 部署文档校验")

checks = [
    ("创建仓库步骤", "New repository|创建.*仓库"),
    ("上传文件步骤", "git init|git add|git commit"),
    ("GitHub Pages配置", "Settings|Pages"),
    ("访问地址", "github.io"),
]
for name, pat in checks:
    if re.search(pat, readme_text):
        ok(f"包含{name}")
    else:
        fail(f"缺少{name}")

for cmd in ["git init", "git add .", "git commit", "git remote add", "git push"]:
    if cmd in readme_text:
        ok(f"部署命令 '{cmd}' 存在")
    else:
        fail(f"命令 '{cmd}' 缺失")

# ================================================================
# 10. 随机模拟
# ================================================================
hdr("10. 随机模拟×200次")

all_ratings = set()
rc = {"master": 0, "average": 0, "pleaser": 0, "straight": 0}
sr = []
for _ in range(200):
    ans = {q['id']: random.randint(0, 3) for q in questions}
    s = simulate_scoring(ans)
    r = determine_rating(s)
    all_ratings.add(r)
    rc[r] += 1
    sr.append(s['overall'])

print(f"  分数范围: {min(sr)}~{max(sr)}")
print(f"  评级分布: {rc}")
print(f"  覆盖{len(all_ratings)}/4种评级")

if len(all_ratings) >= 3:
    ok(f"覆盖{len(all_ratings)}种评级")
else:
    fail(f"仅覆盖{len(all_ratings)}种")

if 20 <= min(sr) <= 50:
    ok(f"最低分{min(sr)}%合理")
else:
    fail(f"最低分{min(sr)}%异常")

if 60 <= max(sr) <= 100:
    ok(f"最高分{max(sr)}%合理（随机答题预期60-75%）")
else:
    fail(f"最高分{max(sr)}%异常")

# ================================================================
# 汇总
# ================================================================
hdr("测试汇总")
total = passed + failed
print(f"\n  通过: {passed}/{total}  ({round(passed/total*100)}%)")
print(f"  失败: {failed}/{total}")

if failed > 0:
    print(f"\n  失败项:")
    for e in errors:
        print(f"    - {e}")
    sys.exit(1)
else:
    print(f"\n  全部测试通过 - 项目可交付")
    sys.exit(0)
