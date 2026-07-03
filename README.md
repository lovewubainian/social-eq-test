# 中国人情世故情商测评

纯静态 HTML+CSS+JS 实现的中国式社交情商自测工具，覆盖 48 个本土人情场景，六大维度精准评估。

## 项目结构

```
social-eq-test/
├── index.html          # 主页面（首页 + 答题 + 报告三合一）
├── css/
│   └── style.css       # 完整样式（响应式，适配手机/电脑）
├── js/
│   ├── data.js         # 题库 + 维度定义 + 话术库 + 评级体系
│   └── app.js          # 主程序（分页答题 + 计分引擎 + 报告生成）
└── README.md           # 本文件
```

## 功能特性

- **48 道本土场景题**：酒局应酬、亲戚人情、职场交际、送礼办事、朋友相处、日常社交
- **六大维度分析**：人情分寸、察言观色、情绪自控、应酬处事、冲突化解、人际边界
- **四套评级体系**：人情通透高手、处事稳妥普通人、讨好型老好人、直性子不懂人情
- **社交话术锦囊**：根据低分维度自动匹配中式社交应对话术
- **纯前端无后端**：无需数据库、无需服务器、无需 npm 安装
- **响应式设计**：自适应手机、平板、电脑端

## 本地使用

直接用浏览器打开 `index.html` 即可。

## GitHub Pages 部署（零配置）

### 第一步：创建仓库

1. 打开 [GitHub](https://github.com)，点击右上角 `+` → `New repository`
2. Repository name 填写：`social-eq-test`（或任意名称）
3. 选择 **Public**
4. 点击 **Create repository**

### 第二步：上传文件

在终端中执行以下命令（将 `<你的用户名>` 替换为你的 GitHub 用户名）：

```bash
# 进入项目目录
cd social-eq-test

# 初始化 Git 仓库
git init
git add .
git commit -m "feat: 中国人情世故情商测评 - 初始版本"

# 关联远程仓库并推送
git remote add origin https://github.com/<你的用户名>/social-eq-test.git
git branch -M main
git push -u origin main
```

### 第三步：开启 GitHub Pages

1. 进入你的仓库页面，点击 **Settings**
2. 左侧菜单找到 **Pages**
3. Source 选择 **Deploy from a branch**
4. Branch 选择 `main`，文件夹选择 `/ (root)`
5. 点击 **Save**
6. 等待 1-2 分钟，页面会显示 `Your site is live at https://<你的用户名>.github.io/social-eq-test/`

### 第四步：访问网站

打开浏览器访问：`https://<你的用户名>.github.io/social-eq-test/`

## 技术说明

- 所有题目、分值、维度归属、反向计分规则均已预设完成，无需手动配置
- 计分模型基于多维加权评估，自动计算各维度百分比和综合总分
- 话术库根据低分维度自动匹配，覆盖敬酒、婉拒、催婚应对、职场沟通等高频场景
- 纯前端实现，所有数据存储在浏览器本地，不会上传任何个人信息
