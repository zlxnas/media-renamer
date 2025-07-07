# Media Manager

一个功能强大的媒体文件管理工具，提供批量重命名、文件转移、分类管理等功能，帮助您高效组织媒体文件库。

## 功能特点

- **批量操作**：支持批量重命名和转移媒体文件
- **多种命名模式**：季集+中文、季集、仅集数、数字序号和自定义模式
- **文件分类**：可配置分类路径，实现媒体文件自动分类
- **文件链接**：支持创建硬链接和软链接，节省存储空间
- **响应式界面**：简洁大方的Web界面，适配各种设备
- **Docker支持**：提供Docker配置，便于快速部署

## 安装指南

### 前提条件
- Python 3.9+ 或 Docker & Docker Compose
- Git

### 手动安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/media-manager.git
cd media-manager

# 创建虚拟环境
python -m venv venv
# Windows激活虚拟环境
venv\Scripts\activate
# macOS/Linux激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
set FLASK_APP=app.py
set FLASK_ENV=production
set ADMIN_USER=admin
set ADMIN_PASSWORD=admin

# 启动应用
flask run --port 3005
```
### Docker安装
```bash
# 克隆仓库
git clone https://github.com/yourusername/
media-manager.git
cd media-manager

# 构建并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f
```
## 使用方法
1. 访问 http://localhost:3005
2. 使用管理员账户登录（默认：admin/admin）
3. 在设置页面配置媒体文件分类路径
4. 使用批量重命名或文件转移功能管理媒体文件
## 配置说明
配置文件位于 app/conf/config.json ，包含以下主要配置项：

- admin_user : 管理员用户名
- admin_password : 管理员密码（明文存储）
- categories : 媒体分类列表
- category_paths : 分类路径配置
## 项目结构
## 安全注意事项
- 默认管理员凭据为 admin/admin，请在首次登录后修改
- 目前系统采用密码明文存储方式，建议仅在个人环境中使用
- 生产环境中应考虑使用HTTPS和密码哈希存储
## 下一步功能改进计划
### 近期功能（1-2个月）
1. 媒体元数据支持
   
   - 添加视频文件元数据解析（分辨率、时长、编码格式）
   - 实现基于元数据的智能分类功能
   - 支持元数据搜索和筛选
2. 批量操作增强
   
   - 添加文件批量压缩/解压缩功能
   - 实现批量文件格式转换
   - 支持自定义正则表达式重命名规则
3. 用户体验优化
   
   - 添加文件拖拽操作支持
   - 实现批量操作进度保存与恢复
   - 优化移动端响应式布局
### 中期功能（3-4个月）
1. 媒体库管理功能
   
   - 实现媒体文件标签系统
   - 添加收藏和最近访问功能
   - 支持媒体文件评分和评论
2. 高级搜索功能
   
   - 实现全文搜索和高级筛选
   - 添加搜索历史记录
   - 支持保存搜索条件
3. 文件预览功能
   
   - 添加常见媒体文件预览（图片、视频、音频）
   - 实现文本文件在线查看
   - 支持缩略图生成与显示
### 长期功能（5个月以上）
1. 自动化工作流
   
   - 实现媒体文件自动分类规则
   - 添加定时任务功能
   - 支持文件变更监控与自动处理
2. 多用户支持
   
   - 添加用户角色与权限管理
   - 实现个人媒体库与共享媒体库
   - 支持用户间文件分享
3. 扩展生态
   
   - 开发插件系统支持第三方扩展
   - 添加API接口支持外部集成
   - 实现WebDAV服务器功能
## 许可证
MIT