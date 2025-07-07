import os
import shutil
from pathlib import Path

MEDIA_ROOT = '/media'

# 获取目录内容
def get_directory_contents(path):
    import datetime  # 添加datetime模块导入
    full_path = os.path.join(MEDIA_ROOT, path.lstrip('/'))
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return []
        
    items = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        # 获取修改时间戳
        mtime = os.path.getmtime(item_path)
        # 转换为可读日期时间格式
        modified_time = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        items.append({
            'name': item,
            'path': os.path.join(path, item),
            'is_dir': os.path.isdir(item_path),
            'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
            'modified_timestamp': mtime,  # 用于排序的时间戳
            'modified_time': modified_time  # 用于显示的格式化时间
        })
    return items

# 批量重命名文件
def batch_rename_files(directory, prefix, season, start_episode, naming_pattern='season_episode', custom_pattern=None, digits=2):
    import re  # 添加正则表达式导入
    full_path = os.path.join(MEDIA_ROOT, directory.lstrip('/'))
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return False, "目录不存在"

    # 获取所有媒体文件并按名称排序
    # 扩展媒体文件扩展名支持范围
    media_extensions = (
        '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.mpeg', '.mpg',
        '.m4v', '.webm', '.ogg', '.ogv', '.m2ts', '.ts', '.mts', '.vob',
        '.iso', '.mxf', '.rm', '.rmvb', '.3gp', '.3g2', '.divx', '.xvid',
        '.wmvhd', '.asf', '.amv', '.f4v', '.m2v', '.mpeg1', '.mpeg2'
    )
    files = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        if os.path.isfile(item_path) and item.lower().endswith(media_extensions):
            files.append(item)

    # 按自然顺序排序文件
    files.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', x)])

    episode = start_episode  # 初始化集数计数器
    renamed_count = 0
    for item in files:
        item_path = os.path.join(full_path, item)
        ext = os.path.splitext(item)[1]
        season_str = str(season).zfill(2)
        episode_str = str(episode).zfill(digits)
        number_str = str(episode).zfill(digits)

        # 根据选择的命名模式生成新文件名
        if naming_pattern == 'season_episode_cn':
            new_name = f"{prefix} - S{season_str}E{episode_str} - 第{episode}集{ext}"
        elif naming_pattern == 'season_episode':
            new_name = f"{prefix} - S{season_str}E{episode_str}{ext}"
        elif naming_pattern == 'episode_only':
            new_name = f"{prefix} - 第{episode}集{ext}"
        elif naming_pattern == 'number_sequence':
            new_name = f"{prefix} - {number_str}{ext}"
        elif naming_pattern == 'custom' and custom_pattern:
            new_name = (custom_pattern
                .replace('{prefix}', prefix)
                .replace('{season}', str(season))
                .replace('{episode}', str(episode))
                .replace('{season2}', season_str)
                .replace('{episode2}', episode_str)
                .replace('{number}', number_str)) + ext
        else:
            new_name = f"{prefix} - S{season_str}E{episode_str}{ext}"

        # 避免重复文件名
        counter = 1
        base_new_name = new_name
        while os.path.exists(os.path.join(full_path, new_name)):
            name, ext = os.path.splitext(base_new_name)
            new_name = f"{name} ({counter}){ext}"
            counter += 1

        # 执行重命名
        new_path = os.path.join(full_path, new_name)
        os.rename(item_path, new_path)
        renamed_count += 1
        episode += 1  # 集数递增

    return True, f"成功重命名 {renamed_count} 个文件"

# 转移文件
def transfer_files(source_dir, dest_dir, transfer_method, season, min_size_mb, progress_callback, prefix, start_episode, filename=None, naming_pattern='season_episode_cn', custom_pattern=None, digits=2, create_season_folder=False):
    source_path = os.path.join(MEDIA_ROOT, source_dir.lstrip('/'))
    min_size = min_size_mb * 1024 * 1024
    
    # 处理单个文件
    if filename:
        file_path = os.path.join(source_path, filename)
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return False, "文件不存在"
        if os.path.getsize(file_path) < min_size:
            return False, "文件大小小于最小限制"
        # 将单个文件也转换为(rel_path, filename)元组格式
        files_to_transfer = [('', filename)]
    # 处理目录下所有文件
    else:
        if not os.path.exists(source_path) or not os.path.isdir(source_path):
            return False, "源目录不存在"
        
        files_to_transfer = []
        # 添加媒体文件扩展名过滤
        media_extensions = (
            '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.mpeg', '.mpg',
            '.m4v', '.webm', '.ogg', '.ogv', '.m2ts', '.ts', '.mts', '.vob',
            '.iso', '.mxf', '.rm', '.rmvb', '.3gp', '.3g2', '.divx', '.xvid',
            '.wmvhd', '.asf', '.amv', '.f4v', '.m2v', '.mpeg1', '.mpeg2'
        )
        
        # 递归遍历所有子目录
        for root, dirs, files in os.walk(source_path):
            for item in files:
                item_path = os.path.join(root, item)
                # 检查文件大小和扩展名
                if (os.path.getsize(item_path) >= min_size and 
                    item.lower().endswith(media_extensions)):
                    # 存储相对路径以便保持目录结构
                    rel_path = os.path.relpath(root, source_path)
                    files_to_transfer.append((rel_path, item))
        
        # 添加自然排序，确保文件按名称中的数字顺序处理
        import re
        files_to_transfer.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', x[1])])
        
        total_files = len(files_to_transfer)
        if total_files == 0:
            return True, "没有符合条件的文件需要转移"
        
        # 创建目标目录
        dest_path = os.path.join(MEDIA_ROOT, dest_dir.lstrip('/'))
        
        # 如果需要创建季文件夹
        if create_season_folder:
            dest_path = os.path.join(dest_path, f"Season {season}")
            
        os.makedirs(dest_path, exist_ok=True)
        
        transferred = 0
        # 初始化集数计数器
        episode = start_episode
        # 修改循环以解包元组
        for rel_path, filename in files_to_transfer:
            item_path = os.path.join(source_path, rel_path, filename)
            
            # 应用重命名规则
            ext = os.path.splitext(filename)[1]
            season_str = str(season).zfill(2)
            episode_str = str(episode).zfill(digits)
            number_str = str(episode).zfill(digits)
            
            # 根据选择的命名模式生成新文件名
            if naming_pattern == 'season_episode_cn':
                new_name = f"{prefix} - S{season_str}E{episode_str} - 第{episode}集{ext}"
            elif naming_pattern == 'season_episode':
                new_name = f"{prefix} - S{season_str}E{episode_str}{ext}"
            elif naming_pattern == 'episode_only':
                new_name = f"{prefix} - 第{episode}集{ext}"
            elif naming_pattern == 'number_sequence':
                new_name = f"{prefix} - {number_str}{ext}"
            elif naming_pattern == 'custom' and custom_pattern:
                new_name = (custom_pattern
                    .replace('{prefix}', prefix)
                    .replace('{season}', str(season))
                    .replace('{episode}', str(episode))
                    .replace('{season2}', season_str)
                    .replace('{episode2}', episode_str)
                    .replace('{number}', number_str)) + ext
            else:
                new_name = f"{prefix} - S{season_str}E{episode_str}{ext}"
            
            # 避免重复文件名
            counter = 1
            base_new_name = new_name
            while os.path.exists(os.path.join(dest_path, rel_path, new_name)):
                name, ext = os.path.splitext(base_new_name)
                new_name = f"{name} ({counter}){ext}"
                counter += 1
            
            # 构建目标路径并创建目录
            dest_item_path = os.path.join(dest_path, rel_path, new_name)
            os.makedirs(os.path.dirname(dest_item_path), exist_ok=True)
            episode += 1  # 集数递增
            
            try:
                if transfer_method == 'move':
                    shutil.move(item_path, dest_item_path)
                elif transfer_method == 'copy':
                    shutil.copy2(item_path, dest_item_path)
                elif transfer_method == 'hardlink':
                    os.link(item_path, dest_item_path)
                elif transfer_method == 'symlink':
                    os.symlink(item_path, dest_item_path)
                else:
                    return False, f"不支持的转移方式: {transfer_method}"
                
                transferred += 1
                # 计算并更新进度
                progress = int((transferred / total_files) * 100)
                progress_callback(progress, filename)
            except Exception as e:
                return False, f"处理文件 {filename} 时出错: {str(e)}"
        
        return True, f"成功{transfer_method} {transferred} 个文件到 {dest_path}"

# 单个文件重命名
def rename_single_file(directory, filename, prefix, season, episode):
    full_path = os.path.join(MEDIA_ROOT, directory.lstrip('/'))
    file_path = os.path.join(full_path, filename)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return False, "文件不存在"
    
    if not filename.lower().endswith(('.mp4', '.mkv', '.avi')):
        return False, "不支持的文件类型"
    
    ext = os.path.splitext(filename)[1]
    # 移除硬编码的季节和集数格式，仅使用用户提供的前缀
    new_name = f"{prefix}{ext}"
    new_path = os.path.join(full_path, new_name)
    
    os.rename(file_path, new_path)
    return True, f"文件已重命名为: {new_name}"


def find_hardlinks(file_path):
    """查找文件的所有硬链接"""
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return 0, []
    
    # 获取文件的inode
    try:
        stat_info = os.stat(file_path)
        inode = stat_info.st_ino
        device = stat_info.st_dev
        link_count = stat_info.st_nlink
        
        # 如果硬链接数为1，则没有其他硬链接
        if link_count <= 1:
            return link_count, [file_path]
        
        # 搜索媒体根目录查找相同inode和设备的文件
        hardlinks = []
        for root, dirs, files in os.walk(MEDIA_ROOT):
            for file in files:
                try:
                    current_path = os.path.join(root, file)
                    current_stat = os.stat(current_path)
                    if current_stat.st_ino == inode and current_stat.st_dev == device:
                        hardlinks.append(current_path)
                except:
                    continue
        
        return link_count, hardlinks
    except Exception as e:
        print(f"查找硬链接失败: {e}")
        return 0, []

def delete_item(path, is_dir=False):
    """删除文件或文件夹"""
    full_path = os.path.join(MEDIA_ROOT, path.lstrip('/'))
    
    if not os.path.exists(full_path):
        return False, "项目不存在"
    
    try:
        if is_dir:
            # 删除文件夹
            shutil.rmtree(full_path)
            return True, f"文件夹 '{os.path.basename(full_path)}' 已删除"
        else:
            # 删除文件
            os.remove(full_path)
            return True, f"文件 '{os.path.basename(full_path)}' 已删除"
    except Exception as e:
        return False, f"删除失败: {str(e)}"