# p2p_messenger_fixed.py - исправленная версия
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, filedialog, ttk
import json
import time
import os
import hashlib
from datetime import datetime
import random

class P2PMessengerFixed:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("P2P Мессенджер PRO - Исправленный")
        self.root.geometry("1000x750")
        
        # Переменные
        self.username = None
        self.udp_socket = None
        self.tcp_socket = None
        self.local_udp_port = None
        self.local_tcp_port = None
        self.connections = {}  # {peer_name: {'udp_addr': (ip, port), 'tcp_addr': (ip, port), 'last_seen': time}}
        self.current_chat = None
        self.running = False
        
        # Папка для сохранения файлов
        self.download_folder = os.path.join(os.path.expanduser("~"), "P2P_Downloads")
        os.makedirs(self.download_folder, exist_ok=True)
        
        # Активные передачи файлов
        self.active_transfers = {}  # {file_id: {'socket': socket, 'file': file, 'size': int, 'sent': int}}
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Инициализируем сокеты
        self.init_sockets()
        
    def create_widgets(self):
        """Создание интерфейса"""
        # Верхняя панель
        top_frame = tk.Frame(self.root, bg='lightgray', height=80)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)
        
        # Кнопки управления
        btn_frame = tk.Frame(top_frame, bg='lightgray')
        btn_frame.pack(pady=5)
        
        self.start_btn = tk.Button(btn_frame, text="🚀 Запустить P2P", 
                                  command=self.start_p2p, 
                                  bg='lightgreen', width=12, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=3)
        
        self.add_btn = tk.Button(btn_frame, text="👤 Добавить контакт", 
                                command=self.add_contact,
                                bg='lightblue', width=12, height=2,
                                state=tk.DISABLED)
        self.add_btn.pack(side=tk.LEFT, padx=3)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ Остановить", 
                                 command=self.stop_p2p,
                                 bg='lightcoral', width=12, height=2,
                                 state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=3)
        
        # Информация
        self.port_info = tk.Label(top_frame, text="⚙️ Порт: не запущен", 
                                 font=('Arial', 10), bg='lightgray')
        self.port_info.pack(pady=2)
        
        # Основная панель
        main_panel = tk.Frame(self.root)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Левая панель - контакты
        left_panel = tk.Frame(main_panel, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        tk.Label(left_panel, text="📱 МОИ КОНТАКТЫ", 
                font=('Arial', 12, 'bold')).pack(pady=5)
        
        self.contacts_list = tk.Listbox(left_panel, height=18, width=35, font=('Arial', 10))
        self.contacts_list.pack(fill=tk.BOTH, expand=True, pady=5)
        self.contacts_list.bind('<Double-Button-1>', self.open_chat)
        
        # Кнопки управления контактами
        contact_btn_frame = tk.Frame(left_panel)
        contact_btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(contact_btn_frame, text="➕ Добавить", 
                 command=self.add_contact, width=9).pack(side=tk.LEFT, padx=2)
        tk.Button(contact_btn_frame, text="❌ Удалить", 
                 command=self.delete_contact, width=9).pack(side=tk.LEFT, padx=2)
        tk.Button(contact_btn_frame, text="🔄 Статус", 
                 command=self.check_status, width=9).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - чат
        right_panel = tk.Frame(main_panel)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Заголовок чата
        self.chat_title = tk.Label(right_panel, text="💬 Выберите контакт", 
                                  font=('Arial', 12, 'bold'), fg='blue')
        self.chat_title.pack(pady=5)
        
        # Область чата
        self.chat_area = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, 
                                                   width=65, height=20,
                                                   font=('Arial', 10))
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=5)
        self.chat_area.config(state=tk.DISABLED)
        
        # Панель ввода
        input_frame = tk.Frame(right_panel)
        input_frame.pack(fill=tk.X, pady=5)
        
        # Кнопки для файлов
        file_btn_frame = tk.Frame(input_frame)
        file_btn_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        tk.Button(file_btn_frame, text="📎 Отправить файл", 
                 command=lambda: self.send_file('file'), 
                 bg='lightyellow', width=12).pack(side=tk.LEFT, padx=2)
        
        tk.Button(file_btn_frame, text="🖼️ Отправить фото", 
                 command=lambda: self.send_file('image'), 
                 bg='lightyellow', width=12).pack(side=tk.LEFT, padx=2)
        
        tk.Button(file_btn_frame, text="🎬 Отправить видео", 
                 command=lambda: self.send_file('video'), 
                 bg='lightyellow', width=12).pack(side=tk.LEFT, padx=2)
        
        tk.Button(file_btn_frame, text="📂 Показать папку", 
                 command=self.open_download_folder, 
                 bg='lightgray', width=12).pack(side=tk.RIGHT, padx=2)
        
        # Поле ввода текста
        text_frame = tk.Frame(input_frame)
        text_frame.pack(fill=tk.X, pady=5)
        
        self.message_entry = tk.Entry(text_frame, font=('Arial', 11))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        
        self.send_btn = tk.Button(text_frame, text="📤 Отправить", 
                                 command=self.send_message, width=10,
                                 state=tk.DISABLED, bg='lightgreen')
        self.send_btn.pack(side=tk.RIGHT)
        
        # Прогресс бар
        self.progress_frame = tk.Frame(right_panel)
        self.progress_frame.pack(fill=tk.X, pady=2)
        
        self.progress_label = tk.Label(self.progress_frame, text="", font=('Arial', 9))
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=400, mode='determinate')
        self.progress_bar.pack()
        
        # Статус бар
        self.status_bar = tk.Label(self.root, text="✅ Статус: Не запущен", 
                                   bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.show_my_ips()
        
    def init_sockets(self):
        """Инициализация сокетов"""
        try:
            # UDP для сообщений
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind(('0.0.0.0', 0))
            self.local_udp_port = self.udp_socket.getsockname()[1]
            
            # TCP для файлов
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind(('0.0.0.0', 0))
            self.local_tcp_port = self.tcp_socket.getsockname()[1]
            self.tcp_socket.listen(5)
            self.tcp_socket.settimeout(1.0)  # Таймаут для accept
            
            print(f"✅ UDP порт: {self.local_udp_port}, TCP порт: {self.local_tcp_port}")
            
        except Exception as e:
            print(f"❌ Ошибка создания сокетов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось создать сокеты: {e}")
            
    def show_my_ips(self):
        """Показывает IP адреса"""
        ips = []
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            ips.append(ip)
            ips.append('127.0.0.1')
        except:
            ips = ['не определен']
            
        self.status_bar.config(text=f"🌐 Ваши IP: {', '.join(ips)}")
        
    def start_p2p(self):
        """Запуск P2P сети"""
        self.username = simpledialog.askstring("Имя", "Введите ваше имя:", parent=self.root)
        if not self.username:
            return
            
        self.running = True
        
        # Запускаем потоки
        threading.Thread(target=self.listen_udp, daemon=True).start()
        threading.Thread(target=self.listen_tcp, daemon=True).start()
        
        # Обновляем интерфейс
        self.start_btn.config(state=tk.DISABLED)
        self.add_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.port_info.config(text=f"📡 UDP: {self.local_udp_port} | TCP: {self.local_tcp_port}", fg="green")
        
        self.log_message(f"✅ P2P сеть запущена! Ваше имя: {self.username}", system=True)
        self.show_connection_info()
        
    def listen_udp(self):
        """Прослушивание UDP сообщений"""
        while self.running:
            try:
                self.udp_socket.settimeout(0.5)
                data, addr = self.udp_socket.recvfrom(65535)
                message = json.loads(data.decode('utf-8'))
                
                if message['type'] == 'chat':
                    self.handle_chat_message(message)
                elif message['type'] == 'file_request':
                    self.handle_file_request(message, addr)
                elif message['type'] == 'file_accept':
                    self.handle_file_accept(message)
                elif message['type'] == 'ping':
                    self.udp_socket.sendto(json.dumps({'type': 'pong'}).encode(), addr)
                elif message['type'] == 'pong':
                    self.handle_pong(addr)
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"UDP ошибка: {e}")
                    
    def listen_tcp(self):
        """Прослушивание TCP соединений для файлов"""
        while self.running:
            try:
                client_socket, addr = self.tcp_socket.accept()
                threading.Thread(target=self.handle_file_transfer, 
                               args=(client_socket, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"TCP ошибка: {e}")
                    
    def handle_chat_message(self, message):
        """Обработка текстового сообщения"""
        sender = message['sender']
        content = message['content']
        
        if self.current_chat == sender:
            self.log_message(f"{sender}: {content}")
        else:
            self.log_message(f"📨 Новое сообщение от {sender}: {content}", system=True)
            self.highlight_contact(sender)
            
    def handle_file_request(self, message, addr):
        """Обработка запроса на отправку файла"""
        file_id = message['file_id']
        filename = message['filename']
        file_size = message['file_size']
        sender = message['sender']
        
        # Предлагаем принять файл
        result = messagebox.askyesno("Входящий файл", 
                                    f"📥 {sender} отправляет файл:\n"
                                    f"Имя: {filename}\n"
                                    f"Размер: {self.format_size(file_size)}\n\n"
                                    f"Принять?")
        
        if result:
            # Отправляем подтверждение
            accept_msg = json.dumps({
                'type': 'file_accept',
                'file_id': file_id,
                'accept': True
            })
            self.udp_socket.sendto(accept_msg.encode(), addr)
            
            # Запускаем прием файла
            threading.Thread(target=self.receive_file, 
                           args=(addr, file_id, filename, file_size), daemon=True).start()
        else:
            # Отклоняем
            accept_msg = json.dumps({
                'type': 'file_accept',
                'file_id': file_id,
                'accept': False
            })
            self.udp_socket.sendto(accept_msg.encode(), addr)
            
    def handle_file_accept(self, message):
        """Обработка подтверждения приема файла"""
        file_id = message['file_id']
        accept = message.get('accept', False)
        
        if accept and file_id in self.active_transfers:
            # Начинаем отправку файла
            transfer = self.active_transfers[file_id]
            threading.Thread(target=self.send_file_data, 
                           args=(file_id, transfer['file_path'], transfer['filename'], 
                                 transfer['file_size'], transfer['peer_addr']), daemon=True).start()
        elif not accept:
            self.log_message(f"❌ Отправка файла отклонена", system=True)
            if file_id in self.active_transfers:
                del self.active_transfers[file_id]
                
    def handle_pong(self, addr):
        """Обработка pong ответа"""
        for name, info in self.connections.items():
            if info['udp_addr'] == addr:
                info['last_seen'] = time.time()
                self.update_contact_status(name, True)
                
    def handle_file_transfer(self, client_socket, addr):
        """Обработка передачи файла (серверная сторона)"""
        try:
            # Получаем информацию о файле
            file_info = client_socket.recv(1024).decode()
            data = json.loads(file_info)
            
            file_id = data['file_id']
            filename = data['filename']
            file_size = data['file_size']
            
            # Сохраняем файл
            save_path = os.path.join(self.download_folder, filename)
            received = 0
            
            with open(save_path, 'wb') as f:
                while received < file_size:
                    chunk = client_socket.recv(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    
                    # Обновляем прогресс
                    if file_size > 0:
                        progress = (received / file_size) * 100
                        self.update_progress(f"Загрузка {filename}", progress)
                        
            self.update_progress("", 0)
            self.log_message(f"✅ Файл сохранен: {filename} ({self.format_size(file_size)})", system=True)
            
        except Exception as e:
            self.log_message(f"❌ Ошибка получения файла: {e}", system=True)
        finally:
            client_socket.close()
            
    def send_file(self, file_type):
        """Инициализация отправки файла"""
        if not self.current_chat:
            messagebox.showwarning("Внимание", "Выберите контакт для отправки")
            return
            
        if self.current_chat not in self.connections:
            messagebox.showerror("Ошибка", "Контакт не найден")
            return
            
        # Выбираем файл
        if file_type == 'image':
            filetypes = [("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp")]
        elif file_type == 'video':
            filetypes = [("Видео", "*.mp4 *.avi *.mkv *.mov")]
        else:
            filetypes = [("Все файлы", "*.*")]
            
        file_path = filedialog.askopenfilename(title="Выберите файл", filetypes=filetypes)
        if not file_path:
            return
            
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Проверяем размер
        if file_size > 100 * 1024 * 1024:  # 100 MB
            if not messagebox.askyesno("Большой файл", 
                                      f"Файл размером {self.format_size(file_size)}.\n"
                                      f"Отправить?"):
                return
                
        # Генерируем ID файла
        file_id = hashlib.md5(f"{self.username}{filename}{time.time()}".encode()).hexdigest()
        
        # Сохраняем информацию о передаче
        peer = self.connections[self.current_chat]
        self.active_transfers[file_id] = {
            'file_path': file_path,
            'filename': filename,
            'file_size': file_size,
            'peer_addr': peer['udp_addr'],
            'peer_name': self.current_chat
        }
        
        # Отправляем запрос на отправку файла
        file_request = {
            'type': 'file_request',
            'file_id': file_id,
            'filename': filename,
            'file_size': file_size,
            'sender': self.username
        }
        
        self.udp_socket.sendto(json.dumps(file_request).encode(), peer['udp_addr'])
        self.log_message(f"📤 Запрос на отправку файла {filename} отправлен...", system=True)
        
    def send_file_data(self, file_id, file_path, filename, file_size, peer_addr):
        """Отправка данных файла"""
        try:
            # Создаем новое TCP соединение
            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_client.connect(peer_addr)
            
            # Отправляем информацию о файле
            file_info = {
                'file_id': file_id,
                'filename': filename,
                'file_size': file_size
            }
            tcp_client.send(json.dumps(file_info).encode())
            time.sleep(0.1)  # Небольшая пауза
            
            # Отправляем файл
            sent = 0
            with open(file_path, 'rb') as f:
                while sent < file_size:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    tcp_client.send(chunk)
                    sent += len(chunk)
                    
                    # Обновляем прогресс
                    progress = (sent / file_size) * 100
                    self.update_progress(f"Отправка {filename}", progress)
                    
            self.update_progress("", 0)
            self.log_message(f"✅ Файл {filename} отправлен ({self.format_size(file_size)})", system=True)
            tcp_client.close()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка отправки файла: {e}", system=True)
        finally:
            if file_id in self.active_transfers:
                del self.active_transfers[file_id]
                
    def receive_file(self, peer_addr, file_id, filename, file_size):
        """Прием файла (клиентская сторона)"""
        try:
            # Создаем новое TCP соединение к отправителю
            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_client.connect(peer_addr)
            
            # Запрашиваем файл
            request = json.dumps({
                'type': 'file_request_data',
                'file_id': file_id
            })
            tcp_client.send(request.encode())
            time.sleep(0.1)
            
            # Получаем файл
            save_path = os.path.join(self.download_folder, filename)
            received = 0
            
            with open(save_path, 'wb') as f:
                while received < file_size:
                    chunk = tcp_client.recv(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    
                    # Обновляем прогресс
                    progress = (received / file_size) * 100
                    self.update_progress(f"Загрузка {filename}", progress)
                    
            self.update_progress("", 0)
            self.log_message(f"✅ Файл сохранен: {filename} ({self.format_size(file_size)})", system=True)
            tcp_client.close()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка получения файла: {e}", system=True)
            
    def add_contact(self):
        """Добавление контакта"""
        add_win = tk.Toplevel(self.root)
        add_win.title("Добавить контакт")
        add_win.geometry("450x450")
        
        tk.Label(add_win, text="➕ ДОБАВЛЕНИЕ КОНТАКТА", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        tk.Label(add_win, text="Имя контакта:").pack(pady=5)
        name_entry = tk.Entry(add_win, width=30)
        name_entry.pack()
        
        tk.Label(add_win, text="IP адрес:").pack(pady=5)
        ip_entry = tk.Entry(add_win, width=30)
        ip_entry.pack()
        
        tk.Label(add_win, text="UDP порт (чат):").pack(pady=5)
        udp_port_entry = tk.Entry(add_win, width=30)
        udp_port_entry.pack()
        
        tk.Label(add_win, text="TCP порт (файлы):").pack(pady=5)
        tcp_port_entry = tk.Entry(add_win, width=30)
        tcp_port_entry.pack()
        
        def save():
            name = name_entry.get().strip()
            ip = ip_entry.get().strip()
            udp_port = udp_port_entry.get().strip()
            tcp_port = tcp_port_entry.get().strip()
            
            if not all([name, ip, udp_port, tcp_port]):
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
                
            try:
                udp_port = int(udp_port)
                tcp_port = int(tcp_port)
                
                # Сохраняем контакт
                self.connections[name] = {
                    'udp_addr': (ip, udp_port),
                    'tcp_addr': (ip, tcp_port),
                    'last_seen': time.time()
                }
                
                self.contacts_list.insert(tk.END, f"{name} 🟢")
                self.log_message(f"✅ Контакт {name} добавлен", system=True)
                add_win.destroy()
                
            except ValueError:
                messagebox.showerror("Ошибка", "Порты должны быть числами")
                
        tk.Button(add_win, text="Сохранить", command=save, 
                 bg="lightgreen", width=15).pack(pady=15)
        tk.Button(add_win, text="Отмена", command=add_win.destroy, 
                 width=15).pack()
                 
    def delete_contact(self):
        """Удаление контакта"""
        selection = self.contacts_list.curselection()
        if not selection:
            return
            
        name = self.contacts_list.get(selection[0]).split(' ')[0]
        if messagebox.askyesno("Подтверждение", f"Удалить контакт {name}?"):
            if name in self.connections:
                del self.connections[name]
            self.contacts_list.delete(selection)
            
            if self.current_chat == name:
                self.current_chat = None
                self.chat_title.config(text="💬 Выберите контакт")
                self.send_btn.config(state=tk.DISABLED)
                
    def check_status(self):
        """Проверка статуса контакта"""
        selection = self.contacts_list.curselection()
        if not selection:
            return
            
        name = self.contacts_list.get(selection[0]).split(' ')[0]
        if name in self.connections:
            info = self.connections[name]
            status = "онлайн 🟢" if time.time() - info.get('last_seen', 0) < 60 else "оффлайн 🔴"
            self.log_message(f"Статус {name}: {status}", system=True)
        else:
            self.log_message(f"Контакт {name} не найден", system=True)
            
    def update_contact_status(self, name, online):
        """Обновление статуса"""
        for i in range(self.contacts_list.size()):
            item = self.contacts_list.get(i)
            if item.startswith(name):
                status = "🟢" if online else "🔴"
                self.contacts_list.delete(i)
                self.contacts_list.insert(i, f"{name} {status}")
                break
                
    def highlight_contact(self, name):
        """Подсветка контакта"""
        for i in range(self.contacts_list.size()):
            item = self.contacts_list.get(i)
            if item.startswith(name):
                self.contacts_list.selection_clear(0, tk.END)
                self.contacts_list.selection_set(i)
                self.contacts_list.see(i)
                break
                
    def open_chat(self, event):
        """Открытие чата"""
        selection = self.contacts_list.curselection()
        if not selection:
            return
            
        name = self.contacts_list.get(selection[0]).split(' ')[0]
        if name not in self.connections:
            messagebox.showerror("Ошибка", "Контакт не найден")
            return
            
        self.current_chat = name
        self.chat_title.config(text=f"💬 Чат с {name}")
        self.send_btn.config(state=tk.NORMAL)
        
        # Очищаем чат
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
        self.log_message(f"🔗 Чат с {name} открыт", system=True)
        
    def send_message(self):
        """Отправка текстового сообщения"""
        if not self.current_chat:
            messagebox.showwarning("Внимание", "Выберите контакт для чата")
            return
            
        message = self.message_entry.get().strip()
        if not message:
            return
            
        if self.current_chat not in self.connections:
            messagebox.showerror("Ошибка", "Контакт не найден")
            return
            
        try:
            peer = self.connections[self.current_chat]
            msg_data = json.dumps({
                'type': 'chat',
                'sender': self.username,
                'content': message
            })
            
            self.udp_socket.sendto(msg_data.encode(), peer['udp_addr'])
            self.log_message(f"Вы: {message}")
            self.message_entry.delete(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить: {e}")
            
    def log_message(self, msg, system=False):
        """Добавление сообщения в чат"""
        self.chat_area.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if system:
            self.chat_area.insert(tk.END, f"[{timestamp}] 🔵 {msg}\n", "system")
            self.chat_area.tag_config("system", foreground="gray")
        else:
            self.chat_area.insert(tk.END, f"[{timestamp}] {msg}\n")
            
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
    def update_progress(self, text, value):
        """Обновление прогресс бара"""
        self.progress_label.config(text=text)
        self.progress_bar['value'] = value
        self.root.update_idletasks()
        
    def open_download_folder(self):
        """Открывает папку с загрузками"""
        if os.name == 'nt':  # Windows
            os.startfile(self.download_folder)
        else:  # macOS, Linux
            os.system(f'open "{self.download_folder}"' if os.name == 'posix' else f'xdg-open "{self.download_folder}"')
        
    def format_size(self, size):
        """Форматирует размер файла"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ТБ"
        
    def show_connection_info(self):
        """Показывает информацию для подключения"""
        info_win = tk.Toplevel(self.root)
        info_win.title("Ваши данные для подключения")
        info_win.geometry("500x550")
        
        tk.Label(info_win, text="📡 ВАШИ ДАННЫЕ ДЛЯ ПОДКЛЮЧЕНИЯ", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        tk.Label(info_win, text="Имя:", font=('Arial', 10)).pack()
        tk.Label(info_win, text=self.username, font=('Courier', 14, 'bold'), 
                fg="blue").pack()
        
        tk.Label(info_win, text="\nIP адреса:", font=('Arial', 10)).pack()
        
        ips = []
        try:
            hostname = socket.gethostname()
            ips.append(socket.gethostbyname(hostname))
            ips.append('127.0.0.1')
        except:
            ips = ['не определен']
            
        for ip in ips:
            tk.Label(info_win, text=ip, font=('Courier', 11)).pack()
            
        tk.Label(info_win, text=f"\nUDP порт (чат):", font=('Arial', 10)).pack()
        tk.Label(info_win, text=str(self.local_udp_port), font=('Courier', 12, 'bold'), 
                fg="green").pack()
                
        tk.Label(info_win, text=f"TCP порт (файлы):", font=('Arial', 10)).pack()
        tk.Label(info_win, text=str(self.local_tcp_port), font=('Courier', 12, 'bold'), 
                fg="green").pack()
        
        tk.Label(info_win, text="\n📝 КАК ПОДКЛЮЧИТЬСЯ:", 
                font=('Arial', 10, 'bold')).pack(pady=10)
        tk.Label(info_win, text="1. Скопируйте один из IP адресов\n"
                               "2. Передайте контакту: имя, IP, UDP порт и TCP порт\n"
                               "3. Контакт нажмет 'Добавить контакт'\n"
                               "4. Введет ваши данные\n"
                               "5. Дважды кликнет по вашему имени в списке\n\n"
                               "📁 Файлы сохраняются в:\n"
                               f"{self.download_folder}", 
                justify=tk.LEFT).pack()
        
        tk.Button(info_win, text="Закрыть", command=info_win.destroy, 
                 width=15).pack(pady=10)
        
    def stop_p2p(self):
        """Остановка P2P сети"""
        self.running = False
        
        self.start_btn.config(state=tk.NORMAL)
        self.add_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.port_info.config(text="⚙️ Порт: не запущен", fg="red")
        
        self.connections.clear()
        self.contacts_list.delete(0, tk.END)
        self.current_chat = None
        self.username = None
        self.chat_title.config(text="💬 Выберите контакт")
        
        self.log_message("❌ P2P сеть остановлена", system=True)
        
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = P2PMessengerFixed()
        app.run()
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
