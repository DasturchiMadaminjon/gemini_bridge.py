#!/usr/bin/env python3
"""
Gemini Enterprise Local Bridge v1.0
Ishga tushirish: python gemini_bridge.py
"""

import os
import json
import shutil
import base64
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

PORT = 57843
HOME = str(Path.home())

HTML_APP = r"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemini Enterprise Analyzer</title>
    <style>
        :root {
            --bg-base: #0a0e17;
            --glass-bg: rgba(16, 22, 35, 0.65);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-border-hover: rgba(255, 255, 255, 0.15);
            --primary-gradient: linear-gradient(135deg, #1b4965 0%, #62b6cb 100%);
            --accent: #5fa8d3;
            --accent-hover: #cae9ff;
            --text-main: #e2e8f0;
            --text-muted: #94a3b8;
            --danger: #ef4444;
            --success: #10b981;
            --shadow-multi: 0 4px 6px -1px rgba(0,0,0,0.1), 0 10px 15px -3px rgba(0,0,0,0.3), 0 25px 50px -12px rgba(0,0,0,0.5);
            --bezier-smooth: cubic-bezier(0.25, 0.8, 0.25, 1);
            --font-main: 'Segoe UI', system-ui, -apple-system, sans-serif;
            --font-mono: 'Fira Code', 'Cascadia Code', Consolas, monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-base);
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(27, 73, 101, 0.15), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(98, 182, 203, 0.15), transparent 25%);
            color: var(--text-main);
            font-family: var(--font-main);
            font-size: 14px;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .glass-panel {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            box-shadow: var(--shadow-multi);
        }

        /* Top Bar */
        #topbar {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 20px;
            border-bottom: 1px solid var(--glass-border);
            z-index: 10;
        }

        .logo {
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
            letter-spacing: 0.5px;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--text-muted);
            margin-left: 10px;
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--danger);
            transition: all 0.4s var(--bezier-smooth);
        }

        .dot.active {
            background: var(--success);
            box-shadow: 0 0 10px var(--success);
        }

        .input-glass {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            padding: 8px 12px;
            color: var(--text-main);
            font-family: var(--font-mono);
            font-size: 13px;
            outline: none;
            transition: all 0.3s var(--bezier-smooth);
        }

        .input-glass:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba(95, 168, 211, 0.2);
        }

        #path-input { width: 300px; }
        #api-key-input { width: 250px; font-family: var(--font-main); }

        .btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            padding: 8px 16px;
            color: var(--text-main);
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s var(--bezier-smooth);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .btn:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--glass-border-hover);
            transform: translateY(-1px);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-primary {
            background: var(--primary-gradient);
            border: none;
            color: #fff;
            box-shadow: 0 4px 15px rgba(27, 73, 101, 0.4);
        }

        .btn-primary:hover:not(:disabled) {
            box-shadow: 0 6px 20px rgba(98, 182, 203, 0.6);
            transform: translateY(-2px);
        }

        /* Layout */
        #workspace {
            display: flex;
            flex: 1;
            overflow: hidden;
            padding: 16px;
            gap: 16px;
        }

        /* Sidebar Explorer */
        #explorer {
            width: 320px;
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            flex-shrink: 0;
        }

        #breadcrumb {
            padding: 12px 16px;
            font-size: 12px;
            color: var(--accent);
            border-bottom: 1px solid var(--glass-border);
            font-family: var(--font-mono);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            background: rgba(0, 0, 0, 0.1);
        }

        #file-tree {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }

        #file-tree::-webkit-scrollbar { width: 6px; }
        #file-tree::-webkit-scrollbar-track { background: transparent; }
        #file-tree::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }

        .file-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s var(--bezier-smooth);
            border: 1px solid transparent;
            margin-bottom: 4px;
        }

        .file-item:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--glass-border);
            transform: translateX(4px);
        }

        .file-item.selected {
            background: rgba(95, 168, 211, 0.15);
            border-color: rgba(95, 168, 211, 0.3);
        }

        .f-icon { font-size: 16px; width: 20px; text-align: center; }
        .f-name { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .f-size { font-size: 11px; color: var(--text-muted); }

        .checkbox {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1px solid var(--glass-border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            transition: all 0.2s ease;
        }

        .file-item.selected .checkbox {
            background: var(--accent);
            border-color: var(--accent);
            color: #000;
        }

        #explorer-footer {
            padding: 12px 16px;
            border-top: 1px solid var(--glass-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0, 0, 0, 0.1);
        }

        /* Chat Panel */
        #chat-panel {
            flex: 1;
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        #messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        #messages-container::-webkit-scrollbar { width: 6px; }
        #messages-container::-webkit-scrollbar-track { background: transparent; }
        #messages-container::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }

        .message {
            display: flex;
            gap: 16px;
            max-width: 90%;
            animation: fadeIn 0.4s var(--bezier-smooth);
        }

        .message.user {
            flex-direction: row-reverse;
            align-self: flex-end;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .avatar {
            width: 36px;
            height: 36px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 16px;
            flex-shrink: 0;
            box-shadow: var(--shadow-multi);
        }

        .message.ai .avatar {
            background: var(--primary-gradient);
            color: #fff;
        }

        .message.user .avatar {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-main);
            border: 1px solid var(--glass-border);
        }

        .msg-content {
            display: flex;
            flex-direction: column;
            gap: 6px;
            min-width: 0;
        }

        .msg-author {
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 600;
        }

        .message.user .msg-author {
            text-align: right;
        }

        .msg-bubble {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 16px 20px;
            font-size: 14px;
            line-height: 1.6;
            color: var(--text-main);
            overflow-wrap: break-word;
        }

        .message.user .msg-bubble {
            background: rgba(95, 168, 211, 0.1);
            border-color: rgba(95, 168, 211, 0.2);
            border-top-right-radius: 4px;
        }

        .message.ai .msg-bubble {
            border-top-left-radius: 4px;
        }

        .msg-bubble pre {
            background: rgba(0, 0, 0, 0.4);
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            border: 1px solid var(--glass-border);
        }

        .msg-bubble code {
            font-family: var(--font-mono);
            font-size: 13px;
            color: var(--accent-hover);
        }

        .msg-bubble p { margin-bottom: 10px; }
        .msg-bubble p:last-child { margin-bottom: 0; }

        .typing-indicator {
            display: flex;
            gap: 6px;
            padding: 8px 4px;
        }

        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: var(--accent);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }

        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        /* Input Area */
        #input-container {
            padding: 16px 24px;
            border-top: 1px solid var(--glass-border);
            background: rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        #selected-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .chip {
            background: rgba(95, 168, 211, 0.15);
            border: 1px solid rgba(95, 168, 211, 0.3);
            border-radius: 12px;
            padding: 4px 10px;
            font-size: 11px;
            color: var(--accent-hover);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .chip button {
            background: none;
            border: none;
            color: var(--danger);
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
        }

        .input-wrapper {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        #chat-input {
            flex: 1;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 12px 16px;
            color: var(--text-main);
            font-family: var(--font-main);
            font-size: 14px;
            resize: none;
            outline: none;
            min-height: 44px;
            max-height: 150px;
            transition: all 0.3s var(--bezier-smooth);
        }

        #chat-input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba(95, 168, 211, 0.1);
        }

        #send-btn {
            height: 44px;
            width: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }

        /* Toast Notifications */
        #toast-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            z-index: 1000;
        }

        .toast {
            min-width: 250px;
            padding: 14px 20px;
            border-radius: 12px;
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            color: var(--text-main);
            box-shadow: var(--shadow-multi);
            display: flex;
            align-items: center;
            gap: 12px;
            transform: translateX(120%);
            opacity: 0;
            transition: all 0.4s var(--bezier-smooth);
        }

        .toast.show {
            transform: translateX(0);
            opacity: 1;
        }
        
        .toast.error { border-left: 4px solid var(--danger); }
        .toast.success { border-left: 4px solid var(--success); }

    </style>
</head>
<body>

    <header id="topbar" class="glass-panel">
        <div class="logo">✨ Gemini Bridge</div>
        <div class="status-indicator">
            <div id="server-status" class="dot"></div>
            <span id="server-text">Ulanilmoqda...</span>
        </div>
        <div style="flex: 1;"></div>
        <input type="password" id="api-key-input" class="input-glass" placeholder="Gemini API Key..." title="Google AI Studio dan olingan API kalit">
        <input type="text" id="path-input" class="input-glass" placeholder="Papka yo'li (masalan: C:\Loyihalar)">
        <button class="btn" onclick="app.loadDirectory()">Ochish</button>
        <button class="btn btn-primary" onclick="app.triggerAnalysis()" id="btn-analyze" disabled>Kodni Tahlil Qil</button>
    </header>

    <main id="workspace">
        <aside id="explorer" class="glass-panel">
            <div id="breadcrumb">/</div>
            <div id="file-tree">
                </div>
            <div id="explorer-footer">
                <span id="selection-count" style="font-size: 12px; color: var(--text-muted);">0 ta tanlangan</span>
                <div style="display: flex; gap: 8px;">
                    <button class="btn" style="padding: 4px 8px; font-size: 11px;" onclick="app.selectAll()">Barchasi</button>
                    <button class="btn" style="padding: 4px 8px; font-size: 11px;" onclick="app.clearSelection()">Tozala</button>
                </div>
            </div>
        </aside>

        <section id="chat-panel" class="glass-panel">
            <div id="messages-container">
                <div style="text-align: center; color: var(--text-muted); margin-top: 40px;">
                    <h2 style="color: var(--text-main); margin-bottom: 10px; font-weight: 500;">Gemini Enterprise tizimiga xush kelibsiz</h2>
                    <p style="max-width: 400px; margin: 0 auto; line-height: 1.5;">Lokal fayllaringizni tanlang, API kalitingizni kiriting va kod bo'yicha murakkab tahlillarni amalga oshiring.</p>
                </div>
            </div>
            
            <div id="input-container">
                <div id="selected-chips"></div>
                <div class="input-wrapper">
                    <textarea id="chat-input" placeholder="Savolingizni yoki buyruqni yozing... (Enter - jo'natish)" rows="1"></textarea>
                    <button id="send-btn" class="btn btn-primary" onclick="app.sendMessage()">↑</button>
                </div>
            </div>
        </section>
    </main>

    <div id="toast-container"></div>

    <script>
        /**
         * Enterprise-Grade Frontend Logic utilizing ES6+ concepts
         * Architecture: State Machine + Event Driven
         */
        const app = {
            config: {
                apiUrl: 'http://127.0.0.1:57843',
                skipDirs: ['.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'],
                allowedExts: ['.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.txt', '.env', '.sql', '.tsx', '.jsx']
            },
            state: {
                currentPath: '',
                parentPath: null,
                selectedFiles: new Set(),
                chatHistory: [],
                isProcessing: false
            },
            elements: {
                serverDot: document.getElementById('server-status'),
                serverText: document.getElementById('server-text'),
                pathInput: document.getElementById('path-input'),
                apiKeyInput: document.getElementById('api-key-input'),
                fileTree: document.getElementById('file-tree'),
                breadcrumb: document.getElementById('breadcrumb'),
                selCount: document.getElementById('selection-count'),
                chipsContainer: document.getElementById('selected-chips'),
                chatInput: document.getElementById('chat-input'),
                sendBtn: document.getElementById('send-btn'),
                messages: document.getElementById('messages-container'),
                analyzeBtn: document.getElementById('btn-analyze')
            },

            // --- Initialization ---
            async init() {
                this.setupEventListeners();
                this.loadSavedKey();
                await this.checkServerConnection();
            },

            setupEventListeners() {
                this.elements.apiKeyInput.addEventListener('change', (e) => {
                    localStorage.setItem('gemini_api_key', e.target.value.trim());
                    this.showToast('API Kalit saqlandi', 'success');
                });

                this.elements.chatInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.sendMessage();
                    }
                });

                this.elements.chatInput.addEventListener('input', function() {
                    this.style.height = 'auto';
                    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
                });

                this.elements.pathInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') this.loadDirectory();
                });
            },

            loadSavedKey() {
                const key = localStorage.getItem('gemini_api_key');
                if (key) this.elements.apiKeyInput.value = key;
            },

            // --- UI Utilities ---
            showToast(msg, type = 'success') {
                const toast = document.createElement('div');
                toast.className = `toast ${type}`;
                toast.innerHTML = `<span>${type === 'success' ? '✅' : '❌'}</span> <span>${this.escapeHTML(msg)}</span>`;
                document.getElementById('toast-container').appendChild(toast);
                
                requestAnimationFrame(() => toast.classList.add('show'));
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 400);
                }, 4000);
            },

            escapeHTML(str) {
                return String(str).replace(/[&<>'"]/g, tag => 
                    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag])
                );
            },

            formatSize(bytes) {
                if (!bytes) return '';
                if (bytes < 1024) return `${bytes} B`;
                if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
                return `${(bytes / 1048576).toFixed(2)} MB`;
            },

            getIcon(item) {
                if (item.type === 'folder') return '📁';
                const ext = (item.ext || '').toLowerCase();
                if (ext === '.py') return '🐍';
                if (['.js', '.ts', '.jsx', '.tsx'].includes(ext)) return '📜';
                if (['.html', '.css'].includes(ext)) return '🎨';
                if (['.json', '.md', '.txt'].includes(ext)) return '📄';
                return '📎';
            },

            isReadable(item) {
                if (item.type === 'folder') return false;
                const ext = (item.ext || '').toLowerCase();
                return this.config.allowedExts.includes(ext) && (!item.size || item.size < 500 * 1024);
            },

            // --- File System Operations ---
            async checkServerConnection() {
                try {
                    const res = await fetch(`${this.config.apiUrl}/home`, { signal: AbortSignal.timeout(2000) });
                    if (!res.ok) throw new Error('Bad response');
                    const data = await res.json();
                    
                    this.elements.serverDot.classList.add('active');
                    this.elements.serverText.textContent = 'Ulangan';
                    this.elements.pathInput.value = data.home;
                    await this.loadDirectory(data.home);
                } catch (error) {
                    this.elements.serverDot.classList.remove('active');
                    this.elements.serverText.textContent = 'Ulanilmagan (Serverni yoqing)';
                    setTimeout(() => this.checkServerConnection(), 3000);
                }
            },

            async loadDirectory(pathStr = null) {
                const targetPath = pathStr || this.elements.pathInput.value.trim();
                if (!targetPath) return;

                this.elements.fileTree.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-muted);">Yuklanmoqda...</div>';

                try {
                    const res = await fetch(`${this.config.apiUrl}/list?path=${encodeURIComponent(targetPath)}`);
                    const data = await res.json();

                    if (data.error) throw new Error(data.error);

                    this.state.currentPath = data.path;
                    this.state.parentPath = data.parent;
                    this.elements.pathInput.value = data.path;
                    this.elements.breadcrumb.textContent = data.path;
                    
                    this.renderFiles(data.items);
                } catch (error) {
                    this.elements.fileTree.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--danger);">${this.escapeHTML(error.message)}</div>`;
                    this.showToast(error.message, 'error');
                }
            },

            renderFiles(items) {
                let html = '';
                
                if (this.state.parentPath) {
                    html += `
                        <div class="file-item" onclick="app.loadDirectory('${this.escapeHTML(this.state.parentPath).replace(/\\/g, '\\\\')}')">
                            <span class="f-icon">↩</span>
                            <span class="f-name" style="color: var(--text-muted)">... orqaga</span>
                        </div>
                    `;
                }

                for (const item of items) {
                    if (this.config.skipDirs.includes(item.name)) continue;
                    
                    const isSelected = this.state.selectedFiles.has(item.path);
                    const isReadOk = this.isReadable(item);
                    const escPath = this.escapeHTML(item.path).replace(/\\/g, '\\\\');
                    const escName = this.escapeHTML(item.name);
                    
                    const onClickAttr = item.type === 'folder' 
                        ? `onclick="app.loadDirectory('${escPath}')"` 
                        : `onclick="app.toggleFileSelection('${escPath}', '${escName}', ${isReadOk})"`;

                    html += `
                        <div class="file-item ${isSelected ? 'selected' : ''}" ${onClickAttr}>
                            <span class="f-icon">${this.getIcon(item)}</span>
                            <span class="f-name">${escName}</span>
                            <span class="f-size">${this.formatSize(item.size)}</span>
                            ${item.type === 'file' ? `<div class="checkbox">${isSelected ? '✓' : ''}</div>` : ''}
                        </div>
                    `;
                }

                this.elements.fileTree.innerHTML = html || '<div style="text-align: center; padding: 20px; color: var(--text-muted);">Bo\'sh papka</div>';
                this.updateSelectionUI();
            },

            toggleFileSelection(path, name, isReadable) {
                if (!isReadable) {
                    this.showToast(`O'qish mumkin bo'lmagan format yoki hajm: ${name}`, 'error');
                    return;
                }

                if (this.state.selectedFiles.has(path)) {
                    this.state.selectedFiles.delete(path);
                } else {
                    this.state.selectedFiles.add(path);
                }
                
                this.loadDirectory(this.state.currentPath); // Re-render tree
            },

            clearSelection() {
                this.state.selectedFiles.clear();
                this.loadDirectory(this.state.currentPath);
            },

            async selectAll() {
                try {
                    const res = await fetch(`${this.config.apiUrl}/list?path=${encodeURIComponent(this.state.currentPath)}`);
                    const data = await res.json();
                    if (!data.error) {
                        data.items.forEach(item => {
                            if (this.isReadable(item)) this.state.selectedFiles.add(item.path);
                        });
                        this.loadDirectory(this.state.currentPath);
                    }
                } catch(e) { console.error(e); }
            },

            updateSelectionUI() {
                const count = this.state.selectedFiles.size;
                this.elements.selCount.textContent = `${count} ta fayl tanlandi`;
                this.elements.analyzeBtn.disabled = count === 0;

                let chipsHtml = '';
                for (const path of this.state.selectedFiles) {
                    const filename = path.split('\\').pop().split('/').pop();
                    const escPath = this.escapeHTML(path).replace(/\\/g, '\\\\');
                    chipsHtml += `
                        <div class="chip">
                            ${this.escapeHTML(filename)}
                            <button onclick="app.toggleFileSelection('${escPath}', '${this.escapeHTML(filename)}', true)">✕</button>
                        </div>
                    `;
                }
                this.elements.chipsContainer.innerHTML = chipsHtml;
            },

            async readSelectedFiles() {
                const combinedContent = [];
                for (const path of this.state.selectedFiles) {
                    try {
                        const res = await fetch(`${this.config.apiUrl}/read?path=${encodeURIComponent(path)}`);
                        const data = await res.json();
                        if (data.type === 'text' && data.content) {
                            const shortPath = path.replace(/\\/g, '/').split('/').slice(-3).join('/');
                            combinedContent.push(`\n// --- File: ${shortPath} ---\n${data.content.slice(0, 8000)}`); // Limit to 8K chars per file
                        }
                    } catch (e) { console.warn('Failed to read', path, e); }
                }
                return combinedContent.join('\n');
            },

            // --- Chat & AI Integration ---
            appendMessage(role, text, isHtml = false) {
                const msgDiv = document.createElement('div');
                msgDiv.className = `message ${role}`;
                
                let contentHtml = '';
                if (text === 'TYPING') {
                    contentHtml = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;
                } else {
                    // Simple markdown formatting implementation
                    let formatted = this.escapeHTML(text)
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/`(.*?)`/g, '<code>$1</code>')
                        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
                        .replace(/\n/g, '<br>');
                    contentHtml = isHtml ? text : formatted;
                }

                msgDiv.innerHTML = `
                    <div class="avatar">${role === 'ai' ? '✨' : '👤'}</div>
                    <div class="msg-content">
                        <div class="msg-author">${role === 'ai' ? 'Gemini Pro' : 'Siz'}</div>
                        <div class="msg-bubble">${contentHtml}</div>
                    </div>
                `;
                
                this.elements.messages.appendChild(msgDiv);
                this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
                return msgDiv;
            },

            updateMessage(element, newText) {
                const bubble = element.querySelector('.msg-bubble');
                const formatted = this.escapeHTML(newText)
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/`(.*?)`/g, '<code>$1</code>')
                        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
                        .replace(/\n/g, '<br>');
                bubble.innerHTML = formatted;
                this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
            },

            async triggerAnalysis() {
                if (this.state.selectedFiles.size === 0) return;
                this.elements.chatInput.value = "Tanlangan fayllarni to'liq arxitektura, xavfsizlik va clean-code jihatdan tahlil qiling.";
                await this.sendMessage();
            },

            async sendMessage() {
                const text = this.elements.chatInput.value.trim();
                const apiKey = this.elements.apiKeyInput.value.trim();

                if (!text || this.state.isProcessing) return;
                if (!apiKey) {
                    this.showToast('Iltimos, yuqoridagi maydonga Gemini API kalitini kiriting!', 'error');
                    this.elements.apiKeyInput.focus();
                    return;
                }

                this.state.isProcessing = true;
                this.elements.chatInput.value = '';
                this.elements.chatInput.style.height = 'auto';
                this.elements.sendBtn.disabled = true;

                this.appendMessage('user', text);
                
                let fileContext = '';
                if (this.state.selectedFiles.size > 0) {
                    const notifyElement = this.appendMessage('ai', `Fayllar o'qilmoqda...`);
                    fileContext = await this.readSelectedFiles();
                    notifyElement.remove();
                }

                const loadingMsg = this.appendMessage('ai', 'TYPING');

                try {
                    // Prepare payload for Gemini API
                    const contents = this.state.chatHistory.map(msg => ({
                        role: msg.role === 'ai' ? 'model' : 'user',
                        parts: [{ text: msg.content }]
                    }));

                    // Add current user prompt with injected file context (if any)
                    const fullPrompt = fileContext 
                        ? `[Fayllar Konteksti]\n${fileContext}\n\n[Foydalanuvchi Savoli]\n${text}` 
                        : text;
                    
                    contents.push({ role: 'user', parts: [{ text: fullPrompt }] });

                    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=${apiKey}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            systemInstruction: {
                                parts: [{ text: "Sen ekspert darajadagi Senior Full Stack Developer san. O'zbek tilida aniq, qisqa, professional va xavfsiz (production-ready) kod hamda tahlillarni taqdim etasan." }]
                            },
                            contents: contents,
                            generationConfig: { temperature: 0.7 }
                        })
                    });

                    if (!response.ok) {
                        const errData = await response.json();
                        throw new Error(errData.error?.message || 'API Xatolik');
                    }

                    const result = await response.json();
                    const replyText = result.candidates[0].content.parts[0].text;
                    
                    this.updateMessage(loadingMsg, replyText);
                    
                    // Save to history (save the clean text, not the huge file context)
                    this.state.chatHistory.push({ role: 'user', content: text });
                    this.state.chatHistory.push({ role: 'ai', content: replyText });

                } catch (error) {
                    this.updateMessage(loadingMsg, `❌ Xatolik yuz berdi: ${error.message}`);
                    this.showToast(error.message, 'error');
                } finally {
                    this.state.isProcessing = false;
                    this.elements.sendBtn.disabled = false;
                }
            }
        };

        // Boot
        document.addEventListener('DOMContentLoaded', () => app.init());
    </script>
</body>
</html>
"""

def apply_cors(handler):
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")

class GeminiBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Oynada ortiqcha loglarni yashirish

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        apply_cors(self)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        apply_cors(self)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        path = unquote(qs.get("path", [HOME])[0])

        if parsed.path in ("/", "/index.html"):
            body = HTML_APP.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/home":
            self.send_json({"home": HOME})

        elif parsed.path == "/list":
            try:
                p = Path(path)
                if not p.exists() or p.is_file():
                    return self.send_json({"error": "Noto'g'ri papka yo'li"}, 400)

                items = []
                for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                    try:
                        stat = item.stat()
                        items.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "file" if item.is_file() else "folder",
                            "size": stat.st_size if item.is_file() else None,
                            "ext": item.suffix.lower() if item.is_file() else None,
                        })
                    except PermissionError:
                        pass

                self.send_json({
                    "path": str(p),
                    "parent": str(p.parent) if str(p) != str(p.parent) else None,
                    "items": items
                })
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif parsed.path == "/read":
            try:
                p = Path(path)
                if not p.is_file():
                    return self.send_json({"error": "Fayl topilmadi"}, 404)

                size = p.stat().st_size
                if size > 5 * 1024 * 1024:
                    return self.send_json({"error": "Fayl hajmi ruxsat etilganidan katta (5MB)"}, 400)

                content = p.read_text(encoding="utf-8")
                self.send_json({"type": "text", "content": content})
            except UnicodeDecodeError:
                self.send_json({"error": "Binar faylni o'qib bo'lmaydi"}, 400)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        else:
            self.send_json({"error": "Endpoint topilmadi"}, 404)

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🚀 Gemini Enterprise Local Bridge ishga tushdi")
    print(f"🌐 Brauzeringizda oching: http://127.0.0.1:{PORT}")
    print("🛑 To'xtatish uchun: Ctrl+C ni bosing")
    print("=" * 50 + "\n")

    try:
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{PORT}")
    except:
        pass

    server = HTTPServer(("127.0.0.1", PORT), GeminiBridgeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer muvaffaqiyatli to'xtatildi.")