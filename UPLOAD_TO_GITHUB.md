# 上传到 GitHub 步骤

## 方法一：使用命令行（推荐）

### 1. 初始化 Git 仓库

```bash
git init
```

### 2. 添加所有文件

```bash
git add .
```

### 3. 提交代码

```bash
git commit -m "Initial commit: GRVT vs Paradex 对冲交易机器人"
```

### 4. 在 GitHub 上创建新仓库

1. 访问 https://github.com/new
2. 输入仓库名称，例如：`grvt-paradex-trading-bot`
3. 选择 Public 或 Private
4. **不要**勾选 "Initialize this repository with a README"
5. 点击 "Create repository"

### 5. 关联远程仓库

```bash
git remote add origin https://github.com/你的用户名/grvt-paradex-trading-bot.git
```

### 6. 推送代码

```bash
git branch -M main
git push -u origin main
```

---

## 方法二：使用 GitHub Desktop

### 1. 下载并安装 GitHub Desktop

访问：https://desktop.github.com/

### 2. 打开 GitHub Desktop

1. 点击 "File" → "Add Local Repository"
2. 选择你的项目文件夹
3. 如果提示 "This directory does not appear to be a Git repository"，点击 "Create a repository"

### 3. 提交更改

1. 在左侧看到所有文件
2. 在底部输入提交信息：`Initial commit: GRVT vs Paradex 对冲交易机器人`
3. 点击 "Commit to main"

### 4. 发布到 GitHub

1. 点击顶部的 "Publish repository"
2. 输入仓库名称：`grvt-paradex-trading-bot`
3. 选择 Public 或 Private
4. 点击 "Publish Repository"

---

## 方法三：使用 VS Code

### 1. 打开项目文件夹

在 VS Code 中打开你的项目文件夹

### 2. 初始化 Git

1. 点击左侧的 "Source Control" 图标（或按 Ctrl+Shift+G）
2. 点击 "Initialize Repository"

### 3. 提交更改

1. 点击 "+" 号添加所有文件
2. 在上方输入提交信息：`Initial commit: GRVT vs Paradex 对冲交易机器人`
3. 点击 "✓" 提交

### 4. 发布到 GitHub

1. 点击 "Publish to GitHub"
2. 选择仓库名称和可见性
3. 点击 "Publish"

---

## 后续更新代码

### 命令行方式

```bash
# 查看修改的文件
git status

# 添加所有修改
git add .

# 提交修改
git commit -m "更新说明"

# 推送到 GitHub
git push
```

### GitHub Desktop 方式

1. 修改代码后，GitHub Desktop 会自动检测
2. 输入提交信息
3. 点击 "Commit to main"
4. 点击 "Push origin"

---

## 常用 Git 命令

```bash
# 查看状态
git status

# 查看提交历史
git log

# 查看远程仓库
git remote -v

# 拉取最新代码
git pull

# 创建新分支
git checkout -b feature-name

# 切换分支
git checkout main

# 合并分支
git merge feature-name
```

---

## 注意事项

1. **不要上传敏感信息**
   - 私钥、密码、API Key 等
   - 个人路径配置
   - 已经添加了 `.gitignore` 来排除常见的敏感文件

2. **检查 .gitignore**
   - 确保 `__pycache__/` 等临时文件不会被上传

3. **添加 LICENSE**
   - 如果是开源项目，建议添加 MIT 或其他开源协议

4. **完善 README**
   - 根据实际情况修改 README.md 中的配置路径
   - 添加更多使用示例

---

## 推荐的仓库设置

### 仓库名称建议
- `grvt-paradex-trading-bot`
- `crypto-arbitrage-bot`
- `defi-hedge-trading`

### 仓库描述建议
```
自动监控 GRVT 和 Paradex 价格差异并执行套利交易的机器人
```

### Topics 标签建议
- `trading-bot`
- `cryptocurrency`
- `arbitrage`
- `defi`
- `python`
- `playwright`
- `automated-trading`

---

## 完成后

上传成功后，你的仓库地址将是：
```
https://github.com/你的用户名/grvt-paradex-trading-bot
```

可以分享给其他人，或者在其他电脑上克隆：
```bash
git clone https://github.com/你的用户名/grvt-paradex-trading-bot.git
```
