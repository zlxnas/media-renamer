import json
import os

# 更新配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'conf', 'config.json')

def load_config():
    if not os.path.exists(CONFIG_PATH):
        # 创建默认配置
        default_config = {
            "admin_username": "admin",
            "admin_password": "admin",
            "categories": [  # 从固定字典改为数组结构
                {"name": "电影", "path": "电影"},
                {"name": "电视剧", "path": "电视剧"},
                {"name": "动漫", "path": "动漫"},
                {"name": "短视频", "path": "短视频"}
            ]
        }
        save_config(default_config)
        return default_config
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    # 确保conf目录存在
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)