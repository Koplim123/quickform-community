# QuickForm-Communiy

## 项目简介

QuickForm 是由温州科技高级中学 AI 科创中心联合温州大学开发的开源智能表单管理系统。教师借助 AI 大模型生成交互网页，通过 QuickForm 提供的 API 接口回收数据，并对学习数据进行智能分析，实现基于数据的精准教学。

社区版由社区维护，支持本地私有化部署。
社区版本允许自由的代码提交，欢迎向项目提交Pull Request!

## 快速开始

### 环境要求

- Python ≥ 3.11
- 任何支持 Python 的操作系统（Windows / macOS / Linux）

### 安装部署

```bash
# 1. 克隆仓库
git clone https://gitee.com/Koplim123/quickform-Community
cd quickform

# 2. 安装依赖
pip install -r src/requirements.txt

# 3. 启动服务
python src/run.py
```

启动后访问 `http://localhost:{port}` 即可使用。

**注:直接运行run.py为debug环境，生产环境请使用gunicorn等工具运行部署**
**生产环境请修改.env文件中的SECRET_KEY!**

## 配置项

config.json为项目


### 默认管理员账号

| 用户名 | 密码 |
|--------|------|
| `wst` | `quickform` |

> 首次使用请立即修改默认密码。

## 开源协议

本项目遵循教师版,采用 [MIT 许可证](LICENSE) 开源。
