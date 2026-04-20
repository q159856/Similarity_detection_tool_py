#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名相似度检测工具
重构版本 - 模块化设计

功能：
1. 检测文件夹中文件名的相似度
2. 支持多种匹配算法
3. 重复文件管理功能
4. 完整的文件信息显示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import tkinter.font as tkfont

from ui.main_window import MainWindow


def setup_fonts():
    """设置中文字体支持"""
    try:
        default_font = tkfont.nametofont("TkDefaultFont")
        font_families = [f.lower() for f in tkfont.families()]
        
        if "microsoft yahei ui" in font_families:
            default_font.configure(family="Microsoft YaHei UI", size=9)
        elif "microsoft yahei" in font_families:
            default_font.configure(family="Microsoft YaHei", size=9)
    except:
        pass


def main():
    """主函数"""
    root = tk.Tk()
    
    setup_fonts()
    
    app = MainWindow(root)
    
    root.mainloop()


if __name__ == "__main__":
    main()
