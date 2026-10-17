#!/usr/bin/env bash
# 一键发布: 编译 + 提交 + 推送 (推送到 GitHub 后 Actions 自动部署)
# 用法: ./publish.sh "提交说明"
set -e
cd "$(dirname "$0")"
msg="${1:-更新文章}"

npx hexo generate

if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "没有变化, 跳过提交"
else
  git add -A
  git commit -m "$msg"
fi

git push
