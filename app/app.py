from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from auth import auth, login_manager
from file_ops import get_directory_contents, batch_rename_files, transfer_files, rename_single_file, find_hardlinks, delete_item, MEDIA_ROOT
from config import load_config, save_config
import os
import threading
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

app.register_blueprint(auth)

@app.route('/')
@login_required
def index():
    path = request.args.get('path', '')
    config = load_config()  # 加载配置
    contents = get_directory_contents(path)
    return render_template('index.html', contents=contents, current_path=path, config=config)  # 传递config到模板

@app.route('/rename', methods=['GET', 'POST'])
@login_required
def rename_files():
    if request.method == 'POST':
        directory = request.form.get('directory')
        filename = request.form.get('filename')  # 获取单个文件名
        prefix = request.form.get('prefix')
        season = int(request.form.get('season', 1))
        start_episode = int(request.form.get('start_episode', 1))
        naming_pattern = request.form.get('naming_pattern', 'season_episode_cn')  # 设为默认模式
        custom_pattern = request.form.get('custom_pattern')
        digits = int(request.form.get('digits', 2))
        
        # 如果指定了单个文件，则只重命名该文件
        if filename:
            success, message = rename_single_file(directory, filename, prefix, season, start_episode)
        else:
            success, message = batch_rename_files(
                directory, prefix, season, start_episode,
                naming_pattern=naming_pattern,
                custom_pattern=custom_pattern,
                digits=digits
            )
        return jsonify({'success': success, 'message': message})
    
    path = request.args.get('path', '')
    filename = request.args.get('filename', '')  # 接收文件名参数
    return render_template('rename.html', current_path=path, filename=filename)  # 传递文件名到模板

# 添加转移任务跟踪字典和锁
transfer_tasks = {}
transfer_lock = threading.Lock()

# 添加任务进度更新函数
def update_transfer_progress(task_id, progress, filename, success=None, message=None):
    with transfer_lock:
        if task_id not in transfer_tasks:
            transfer_tasks[task_id] = {
                'start_time': datetime.now(),
                'progress': 0,
                'status': 'in_progress',
                'message': ''
            }
        
        transfer_tasks[task_id]['progress'] = progress
        if filename:
            transfer_tasks[task_id]['message'] = f'正在处理: {filename}'
        if success is not None:
            transfer_tasks[task_id]['status'] = 'completed' if success else 'error'
            transfer_tasks[task_id]['success'] = success
            transfer_tasks[task_id]['message'] = message
            transfer_tasks[task_id]['end_time'] = datetime.now()

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer_files_route():
    if request.method == 'POST':
        source_dir = request.form.get('source_dir')
        filename = request.form.get('filename')
        dest_dir = request.form.get('dest_dir')
        transfer_method = request.form.get('transfer_method', 'move')
        season = int(request.form.get('season', 1))
        min_size = float(request.form.get('min_size', 0))
        prefix = request.form.get('prefix', '')
        start_episode = int(request.form.get('start_episode', 1))
        digits = int(request.form.get('digits', 2))
        create_season_folder = request.form.get('create_season_folder') == 'on'  # 添加此行
        naming_pattern = request.form.get('naming_pattern', 'season_episode_cn')
        custom_pattern = request.form.get('custom_pattern', '')
        
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 启动后台任务
        def background_task():
            try:
                # 调用转移文件函数
                success, message = transfer_files(
                    source_dir, dest_dir, transfer_method, season, min_size,
                    lambda p, f: update_transfer_progress(task_id, p, f),
                    prefix, start_episode, filename, naming_pattern, custom_pattern,
                    digits=digits,
                    create_season_folder=create_season_folder
                )
                update_transfer_progress(task_id, 100, None, success, message)
            except Exception as e:
                # 确保异常情况下任务状态也被记录
                update_transfer_progress(task_id, 0, None, False, f'任务失败: {str(e)}')
        
        threading.Thread(target=background_task).start()
        
        return jsonify({'task_id': task_id})
    else:
        path = request.args.get('path', '')
        filename = request.args.get('filename', '')
        return render_template('transfer.html', current_path=path, filename=filename, os=os)

# 添加进度查询API
@app.route('/transfer-progress/<task_id>')
@login_required
def get_transfer_progress(task_id):
    with transfer_lock:
        task = transfer_tasks.get(task_id, None)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        # 清理过期任务(超过30分钟)
        if task['status'] in ['completed', 'error'] and datetime.now() - task['start_time'] > timedelta(minutes=30):
            del transfer_tasks[task_id]
            return jsonify({'error': '任务已过期'}), 404
        
        return jsonify({
            'progress': task['progress'],
            'message': task['message'],
            'status': task['status'],
            'success': task.get('success')
        })

# 新增设置页面路由
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    config = load_config()
    
    if request.method == 'POST':
        # 处理用户名修改
        if 'new_username' in request.form and request.form['new_username']:
            config['admin_username'] = request.form['new_username']
        
        # 处理密码修改
        if 'new_password' in request.form and request.form['new_password']:
            config['admin_password'] = request.form['new_password']
        
        # 处理分类设置
        config['categories'] = []
        i = 0
        while f'category_name_{i}' in request.form:
            category_name = request.form[f'category_name_{i}']
            category_path = request.form[f'category_path_{i}']
            if category_name and category_path:
                config['categories'].append({
                    'name': category_name,
                    'path': category_path
                })
            i += 1
        
        try:
            save_config(config)
            flash('设置已保存')
        except Exception as e:
            flash(f'保存失败: {str(e)}')
            app.logger.error(f'配置保存错误: {str(e)}')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', config=config)

# 添加文件夹浏览API
@app.route('/browse-folders')
@login_required
def browse_folders():
    path = request.args.get('path', '')
    full_path = os.path.join(MEDIA_ROOT, path.lstrip('/'))
    
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return jsonify({'error': '路径不存在或不是目录'}), 400
    
    folders = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        if os.path.isdir(item_path):
            folders.append({
                'name': item,
                'path': os.path.join(path, item) if path else item
            })
    
    return jsonify({
        'currentPath': path,
        'folders': folders
    })

@app.route('/rename-single', methods=['POST'])
@login_required
def rename_single_item():
    path = request.form.get('path')
    new_name = request.form.get('new_name')
    is_dir = request.form.get('is_dir') == 'true'
    
    # 提取目录和文件名
    directory = os.path.dirname(path)
    old_name = os.path.basename(path)
    
    try:
        # 对于文件夹，直接重命名
        if is_dir:
            old_path = os.path.join(MEDIA_ROOT, path.lstrip('/'))
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            os.rename(old_path, new_path)
            return jsonify({'success': True, 'message': f'文件夹已重命名为: {new_name}'})
        # 对于文件，使用现有函数
        else:
            # 提取文件扩展名
            ext = os.path.splitext(old_name)[1]
            # 简单重命名（不使用媒体文件命名规则）
            success, message = rename_single_file(directory, old_name, new_name.rsplit('.', 1)[0] if '.' in new_name else new_name, 1, 1)
            
            # 如果使用现有函数失败，尝试直接重命名
            if not success:
                old_path = os.path.join(MEDIA_ROOT, path.lstrip('/'))
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                os.rename(old_path, new_path)
                return jsonify({'success': True, 'message': f'文件已重命名为: {new_name}'})
                
            return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'重命名失败: {str(e)}'})

@app.route('/hardlink-query')
@login_required
def hardlink_query():
    path = request.args.get('path')
    full_path = os.path.join(MEDIA_ROOT, path.lstrip('/'))
    
    try:
        link_count, links = find_hardlinks(full_path)
        return jsonify({
            'success': True,
            'linkCount': link_count,
            'links': links
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'})

@app.route('/delete-item', methods=['POST'])
@login_required
def delete_item_route():
    data = request.get_json()
    path = data.get('path')
    is_dir = data.get('is_dir', False)
    
    try:
        success, message = delete_item(path, is_dir)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

@app.context_processor
def inject_os():
    import os
    return dict(os=os)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3005)