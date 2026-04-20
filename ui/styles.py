#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
样式管理模块
负责界面样式的统一管理
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from typing import Dict, Any


class StyleManager:
    """样式管理器"""
    
    def __init__(self):
        self._fonts: Dict[str, Any] = {}
        self._colors = {
            'primary': '#2980b9',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'info': '#3498db',
            'light': '#ecf0f1',
            'dark': '#2c3e50',
            'muted': '#95a5a6',
            'text_primary': '#333333',
            'text_secondary': '#666666',
            'background': '#ffffff',
        }
    
    def setup_styles(self, root: tk.Tk):
        """
        设置全局样式
        
        Args:
            root: Tk根窗口
        """
        self._setup_fonts(root)
        self._setup_ttk_styles()
    
    def _setup_fonts(self, root: tk.Tk):
        """设置字体"""
        try:
            default_font = tkfont.nametofont("TkDefaultFont")
            font_families = [f.lower() for f in tkfont.families()]
            
            if "microsoft yahei ui" in font_families:
                default_font.configure(family="Microsoft YaHei UI", size=9)
            elif "microsoft yahei" in font_families:
                default_font.configure(family="Microsoft YaHei", size=9)
        except:
            pass
        
        try:
            default_font = tkfont.nametofont("TkDefaultFont")
            
            self._fonts['title'] = tkfont.Font(font=default_font)
            self._fonts['title'].configure(size=14, weight="bold")
            
            self._fonts['heading'] = tkfont.Font(font=default_font)
            self._fonts['heading'].configure(size=11, weight="bold")
            
            self._fonts['normal'] = tkfont.Font(font=default_font)
            self._fonts['normal'].configure(size=10)
            
            self._fonts['small'] = tkfont.Font(font=default_font)
            self._fonts['small'].configure(size=9)
            
            self._fonts['bold'] = tkfont.Font(font=default_font)
            self._fonts['bold'].configure(weight="bold")
            
            self._fonts['summary'] = tkfont.Font(font=default_font)
            self._fonts['summary'].configure(size=10, weight="bold")
            
        except:
            self._fonts = {
                'title': ("TkDefaultFont", 14, "bold"),
                'heading': ("TkDefaultFont", 11, "bold"),
                'normal': ("TkDefaultFont", 10),
                'small': ("TkDefaultFont", 9),
                'bold': ("TkDefaultFont", 10, "bold"),
                'summary': ("TkDefaultFont", 10, "bold"),
            }
    
    def _setup_ttk_styles(self):
        """设置ttk样式"""
        style = ttk.Style()
        
        try:
            style.configure("Title.TLabel", font=self._fonts.get('title', ("TkDefaultFont", 14, "bold")))
            style.configure("Heading.TLabel", font=self._fonts.get('heading', ("TkDefaultFont", 11, "bold")))
            style.configure("Normal.TLabel", font=self._fonts.get('normal', ("TkDefaultFont", 10)))
            style.configure("Small.TLabel", font=self._fonts.get('small', ("TkDefaultFont", 9)))
            style.configure("Result.TLabel", font=self._fonts.get('small', ("TkDefaultFont", 9)), foreground=self._colors['text_primary'])
        except:
            pass
    
    def get_font(self, name: str) -> Any:
        """
        获取字体
        
        Args:
            name: 字体名称
            
        Returns:
            字体对象或元组
        """
        return self._fonts.get(name, self._fonts.get('normal'))
    
    def get_color(self, name: str) -> str:
        """
        获取颜色
        
        Args:
            name: 颜色名称
            
        Returns:
            颜色值
        """
        return self._colors.get(name, '#333333')
    
    def configure_text_widget(self, text_widget: tk.Text):
        """
        配置文本控件的标签样式
        
        Args:
            text_widget: Tk文本控件
        """
        title_font = self.get_font('title')
        bold_font = self.get_font('bold')
        normal_font = self.get_font('small')
        summary_font = self.get_font('summary')
        
        text_widget.tag_configure(
            "group_title", 
            font=title_font, 
            foreground=self._colors['dark'], 
            background=self._colors['light']
        )
        text_widget.tag_configure(
            "similarity_high", 
            foreground=self._colors['danger'], 
            font=bold_font
        )
        text_widget.tag_configure(
            "similarity_medium", 
            foreground=self._colors['warning'], 
            font=normal_font
        )
        text_widget.tag_configure(
            "filename", 
            foreground=self._colors['primary'], 
            font=normal_font
        )
        text_widget.tag_configure(
            "separator", 
            foreground=self._colors['muted']
        )
        text_widget.tag_configure(
            "summary", 
            font=summary_font, 
            foreground=self._colors['success']
        )
        text_widget.tag_configure(
            "file_info", 
            foreground=self._colors['text_secondary'],
            font=normal_font
        )
