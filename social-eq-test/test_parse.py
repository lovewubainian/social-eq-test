#!/usr/bin/env python3
"""Test question extraction"""
import re

with open('/workspace/social-eq-test/js/data.js', 'r') as f:
    text = f.read()

def extract_js_objects(section, start_depth=0):
    depth = 0
    in_string = False
    string_char = None
    obj_start = -1
    objects = []
    i = 0
    while i < len(section):
        ch = section[i]
        if in_string:
            if ch == '\\':
                i += 1
            elif ch == string_char:
                in_string = False
            i += 1
            continue
        if ch == '"' or ch == "'":
            in_string = True
            string_char = ch
            i += 1
            continue
        if ch == '{':
            if depth == start_depth:
                obj_start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == start_depth and obj_start >= 0:
                objects.append(section[obj_start:i+1])
                obj_start = -1
        i += 1
    return objects

# Find QUESTIONS array bounds
start = text.find('var QUESTIONS = [')
end = text.find('var DIMENSION_DEFINITIONS', start)
section = text[start:end]

# Find the content inside the array brackets
array_start = section.find('[') + 1
depth = 0
in_string = False
string_char = None
array_end = -1
for i in range(array_start, len(section)):
    ch = section[i]
    if in_string:
        if ch == '\\':
            i += 1
        elif ch == string_char:
            in_string = False
        continue
    if ch == '"' or ch == "'":
        in_string = True
        string_char = ch
        continue
    if ch == '[':
        depth += 1
    elif ch == ']':
        if depth == 0:
            array_end = i
            break
        depth -= 1

array_content = section[array_start:array_end]
q_objs = extract_js_objects(array_content, 0)
print(f"Questions extracted: {len(q_objs)}")

if q_objs:
    first = q_objs[0]
    print(f"First question length: {len(first)} chars")
    print(first[:300])
    
    # Parse id and category
    id_m = re.search(r'id:\s*(\d+)', first)
    cat_m = re.search(r'category:\s*"([^"]+)"', first)
    if id_m:
        print(f"  id: {id_m.group(1)}")
    if cat_m:
        print(f"  category: {cat_m.group(1)}")
    
    # Parse options
    opts = re.findall(r'text:\s*"(.*?)"\s*,\s*score:\s*(\d)', first)
    print(f"  options: {len(opts)}")
    for t, s in opts:
        print(f"    score={s}: {t[:40]}...")
    
    # Parse dimensions
    dims_m = re.search(r'dimensions:\s*\[(.*?)\]', first, re.DOTALL)
    if dims_m:
        dims = re.findall(r'"([^"]+)"', dims_m.group(1))
        print(f"  dimensions: {dims}")

print()

# Also check questions 2 and 48
if len(q_objs) >= 2:
    q2 = q_objs[1]
    id_m = re.search(r'id:\s*(\d+)', q2)
    print(f"Q2 id: {id_m.group(1) if id_m else '?'}")

if len(q_objs) >= 48:
    q48 = q_objs[47]
    id_m = re.search(r'id:\s*(\d+)', q48)
    cat_m = re.search(r'category:\s*"([^"]+)"', q48)
    print(f"Q48 id: {id_m.group(1) if id_m else '?'}, category: {cat_m.group(1) if cat_m else '?'}")
