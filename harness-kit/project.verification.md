# Project Verification

本文件描述当前项目的验证命令。迁移到新项目后，应通过 `harness-kit/init/project-profiler.prompt.md` 重新生成。

## Harness 验证

```bash
bash harness-kit/scripts/harness-check.sh
```

## 应用验证

| 命令 | 用途 |
| --- | --- |
| `cd backend && python -m pytest -v` | 后端测试（pytest） |
| `cd frontend && npm run build` | 前端构建 |
| `uvicorn app.main:app --reload` | 启动后端（开发模式） |
| `cd frontend && npm run dev` | 启动前端（开发模式） |

## 静态检查

| 命令 | 用途 |
| --- | --- |
| `cd backend && python -c "import app"` | Python 模块导入检查 |
| `cd frontend && npm run lint` | 前端 lint（若有） |
| `python -m py_compile backend/app/*.py` | Python 语法检查 |

## 待确认项

- 是否需要代码格式化工具（black/isort for Python，prettier/eslint for JS）
- 是否需要 type hint 检查（mypy）
