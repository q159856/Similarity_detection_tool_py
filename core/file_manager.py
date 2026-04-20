#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理模块
负责文件的读取、信息获取等操作
"""

import os
from datetime import datetime
from typing import List, Dict, Any


class FileManager:
    """文件管理器"""
    
    @staticmethod
    def get_files_in_folder(folder_path: str) -> List[str]:
        """
        获取文件夹中的所有文件（不包含子目录）
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            文件名列表
        """
        files = []
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    files.append(item)
        except Exception as e:
            raise ValueError(f"读取文件夹时出错：{str(e)}")
        return files
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        获取文件的详细信息
        
        Args:
            file_path: 文件完整路径
            
        Returns:
            包含文件信息的字典
        """
        info = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'extension': '',
            'size': 0,
            'size_str': '0 B',
            'created_time': None,
            'created_time_str': '',
            'modified_time': None,
            'modified_time_str': '',
            'exists': False
        }
        
        if not os.path.exists(file_path):
            return info
        
        info['exists'] = True
        
        try:
            stat = os.stat(file_path)
            info['size'] = stat.st_size
            info['size_str'] = FileManager.format_file_size(stat.st_size)
            info['extension'] = os.path.splitext(file_path)[1].lower()
            
            try:
                info['created_time'] = stat.st_ctime
                info['created_time_str'] = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            
            try:
                info['modified_time'] = stat.st_mtime
                info['modified_time_str'] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        except:
            pass
        
        return info
    
    @staticmethod
    def format_file_size(size: int) -> str:
        """
        格式化文件大小
        
        Args:
            size: 文件大小（字节）
            
        Returns:
            格式化后的字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    @staticmethod
    def clean_filename(filename: str, include_extension: bool = False) -> str:
        """
        预处理文件名，去除扩展名（可选）和特殊字符
        
        Args:
            filename: 原始文件名
            include_extension: 是否包含扩展名
            
        Returns:
            清理后的文件名（小写）
        """
        import re
        
        if not include_extension:
            filename = os.path.splitext(filename)[0]
        
        filename = re.sub(r'[^\w\u4e00-\u9fa5]', '', filename)
        return filename.lower()
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功删除
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except:
            pass
        return False
    
    @staticmethod
    def open_folder(folder_path: str) -> bool:
        """
        打开文件夹（在资源管理器中）
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            是否成功打开
        """
        try:
            import subprocess
            if os.path.exists(folder_path):
                os.startfile(folder_path)
                return True
        except:
            try:
                subprocess.run(['explorer', folder_path])
                return True
            except:
                pass
        return False
