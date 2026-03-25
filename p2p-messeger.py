# test_local.py - для тестирования на одном ПК
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, filedialog, ttk
import json
import time
import os
import hashlib

class TestP2PMessenger:
    def __init__(self, instance_name, udp_port=None, tcp_port=None):
        self.instance_name = instance_name
        self.root = tk.Tk()
        self.root.title(f"P2P Тест - {instance_name}")
        self.root.geometry("900x650")
        
        # Переменные
        self.username = instance_name
        self.udp_socket = None
        self.tcp_socket = None
        self.connections = {}
        self.current_chat = None
        self.running = False
        self.local_udp_port = udp_port
        self.local_tcp_port = tcp_port
        
        # Папка для загрузок
        self.download_folder = os.path.join(os.path.expanduser("~"), f"P2P_Downloads_{instance_name}")
        os.makedirs(self.download_folder, exist_ok=True)
        
        # Активные передачи
        self.active_transfers = {}
        
        self.create_widgets()
        self.init_sockets()
        
    def create_widgets(self):
        """Создание интерфейса"""
        # Основной фрейм
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Информационная панель
        info_frame = tk.Frame(main_frame, bg='lightgray', height=80)
        info_frame.pack(fill=tk.X, pady=5)
        info_frame.pack_propagate(False)
        
        tk.Label(info_frame, text=f"👤 {self.instance_name}", 
                font=('Arial', 14, 'bold')).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.status_label = tk.Label(info_frame, text="⏳ Статус: Запуск...", 
                                    font=('Arial', 10))
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Контакты
        contacts_frame = tk.Frame(main_frame)
        contacts_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        tk.Label(contacts_frame, text="📱 КОНТАКТЫ", font=('Arial', 12, 'bold')).pack()
        
        self.contacts_list = tk.Listbox(contacts_frame, height=20, width=25)
        self.contacts_list.pack(pady=5)
        self.contacts_list.bind('<Double-Button-1>', self.open_chat)
        
        # Кнопки
        btn_frame = tk.Frame(contacts_frame)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="➕ Добавить контакт", 
                 command=self.add_contact, width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="❌ Удалить", 
                 command=self.delete_contact, width=8).pack(side=tk.LEFT, padx=2)
        
        # Чат
        chat_frame = tk.Frame(main_frame)
        chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.chat_title = tk.Label(chat_frame, text="💬 Чат", 
                                  font=('Arial', 12, 'bold'))
        self.chat_title.pack()
        
        self.chat_area = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, 
                                                   width=60, height=20)
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=5)
        self.chat_area.config(state=tk.DISABLED)
        
        # Панель ввода
        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        # Кнопки файлов
        file_frame = tk.Frame(input_frame)
        file_frame.pack(fill=tk.X, pady=2)
        
        tk.Button(file_frame, text="📎 Файл", 
                 command=lambda: self.send_file('file'), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="🖼️ Фото", 
                 command=lambda: self.send_file('image'), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="🎬 Видео", 
                 command=lambda: self.send_file('video'), width=8).pack(side=tk.LEFT, padx=2)
        
        # Текст
        text_frame = tk.Frame(input_frame)
        text_frame.pack(fill=tk.X, pady=5)
        
        self.message_entry = tk.Entry(text_frame, font=('Arial', 11))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        
        self.send_btn = tk.Button(text_frame, text="Отправить", 
                                 command=self.send_message, width=10,
                                 state=tk.DISABLED)
        self.send_btn.pack(side=tk.RIGHT)
        
        # Прогресс
        self.progress_bar = ttk.Progressbar(chat_frame, length=400, mode='determinate')
        self.progress_bar.pack(pady=2)
        
        self.progress_label = tk.Label(chat_frame, text="", font=('Arial', 9))
        self.progress_label.pack()
        
        # Статус
        self.bottom_status = tk.Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.bottom_status.pack(side=tk.BOTTOM, fill=tk.X)
        
    def init_sockets(self):
        """Инициализация сокетов"""
        try:
            # UDP
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if self.local_udp_port:
                self.udp_socket.bind(('127.0.0.1', self.local_udp_port))
            else:
                self.udp_socket.bind(('127.0.0.1', 0))
            self.local_udp_port = self.udp_socket.getsockname()[1]
            
            # TCP
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if self.local_tcp_port:
                self.tcp_socket.bind(('127.0.0.1', self.local_tcp_port))
            else:
                self.tcp_socket.bind(('127.0.0.1', 0))
            self.local_tcp_port = self.tcp_socket.getsockname()[1]
            self.tcp_socket.listen(5)
            self.tcp_socket.settimeout(1.0)
            
            self.running = True
            
            # Запускаем потоки
            threading.Thread(target=self.listen_udp, daemon=True).start()
            threading.Thread(target=self.listen_tcp, daemon=True).start()
            
            self.status_label.config(text=f"✅ Запущен | UDP:{self.local_udp_port} TCP:{self.local_tcp_port}")
            self.bottom_status.config(text=f"📡 UDP: {self.local_udp_port} | TCP: {self.local_tcp_port}")
            
            self.log_message(f"✅ {self.instance_name} запущен!", system=True)
            self.log_message(f"📁 Файлы: {self.download_folder}", system=True)
            
        except Exception as e:
            print(f"Ошибка: {e}")
            
    def listen_udp(self):
        """Прослушивание UDP"""
        while self.running:
            try:
                self.udp_socket.settimeout(0.5)
                data, addr = self.udp_socket.recvfrom(65535)
                message = json.loads(data.decode('utf-8'))
                
                if message['type'] == 'chat':
                    sender = message['sender']
                    content = message['content']
                    if self.current_chat == sender:
                        self.log_message(f"{sender}: {content}")
                    else:
                        self.log_message(f"📨 {sender}: {content}", system=True)
                        self.highlight_contact(sender)
                        
                elif message['type'] == 'file_request':
                    self.handle_file_request(message, addr)
                    
                elif message['type'] == 'file_accept':
                    self.handle_file_accept(message)
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"UDP ошибка: {e}")
                    
    def listen_tcp(self):
        """Прослушивание TCP"""
        while self.running:
            try:
                client_socket, addr = self.tcp_socket.accept()
                threading.Thread(target=self.handle_file_transfer, 
                               args=(client_socket,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"TCP ошибка: {e}")
                    
    def handle_file_request(self, message, addr):
        """Обработка запроса файла"""
        file_id = message['file_id']
        filename = message['filename']
        file_size = message['file_size']
        sender = message['sender']
        
        result = messagebox.askyesno("Входящий файл", 
                                    f"{sender} отправляет:\n{filename}\n{self.format_size(file_size)}\n\nПринять?")
        
        accept_msg = json.dumps({
            'type': 'file_accept',
            'file_id': file_id,
            'accept': result
        })
        self.udp_socket.sendto(accept_msg.encode(), addr)
        
        if result:
            threading.Thread(target=self.receive_file, 
                           args=(addr, file_id, filename, file_size), daemon=True).start()
            
    def handle_file_accept(self, message):
        """Обработка подтверждения"""
        file_id = message['file_id']
        accept = message.get('accept', False)
        
        if accept and file_id in self.active_transfers:
            transfer = self.active_transfers[file_id]
            threading.Thread(target=self.send_file_data, 
                           args=(file_id, transfer['file_path'], transfer['filename'], 
                                 transfer['file_size'], transfer['peer_addr']), daemon=True).start()
        elif not accept:
            self.log_message(f"❌ Отправка отклонена", system=True)
            if file_id in self.active_transfers:
                del self.active_transfers[file_id]
                
    def handle_file_transfer(self, client_socket):
        """Прием файла"""
        try:
            file_info = client_socket.recv(1024).decode()
            data = json.loads(file_info)
            
            filename = data['filename']
            file_size = data['file_size']
            
            save_path = os.path.join(self.download_folder, filename)
            received = 0
            
            with open(save_path, 'wb') as f:
                while received < file_size:
                    chunk = client_socket.recv(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    progress = (received / file_size) * 100
                    self.update_progress(f"Загрузка {filename}", progress)
                    
            self.update_progress("", 0)
            self.log_message(f"✅ Файл сохранен: {filename}", system=True)
            
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}", system=True)
        finally:
            client_socket.close()
            
    def send_file(self, file_type):
        """Отправка файла"""
        if not self.current_chat:
            messagebox.showwarning("Внимание", "Выберите контакт")
            return
            
        if self.current_chat not in self.connections:
            messagebox.showerror("Ошибка", "Контакт не найден")
            return
            
        if file_type == 'image':
            filetypes = [("Изображения", "*.jpg *.jpeg *.png *.gif")]
        elif file_type == 'video':
            filetypes = [("Видео", "*.mp4 *.avi *.mkv")]
        else:
            filetypes = [("Все файлы", "*.*")]
            
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if not file_path:
            return
            
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_id = hashlib.md5(f"{self.username}{filename}{time.time()}".encode()).hexdigest()
        
        peer = self.connections[self.current_chat]
        self.active_transfers[file_id] = {
            'file_path': file_path,
            'filename': filename,
            'file_size': file_size,
            'peer_addr': peer['udp_addr'],
            'peer_name': self.current_chat
        }
        
        file_request = {
            'type': 'file_request',
            'file_id': file_id,
            'filename': filename,
            'file_size': file_size,
            'sender': self.username
        }
        
        self.udp_socket.sendto(json.dumps(file_request).encode(), peer['udp_addr'])
        self.log_message(f"📤 Запрос на отправку {filename}", system=True)
        
    def send_file_data(self, file_id, file_path, filename, file_size, peer_addr):
        """Отправка данных файла"""
        try:
            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_client.connect(peer_addr)
            
            file_info = {
                'file_id': file_id,
                'filename': filename,
                'file_size': file_size
            }
            tcp_client.send(json.dumps(file_info).encode())
            time.sleep(0.1)
            
            sent = 0
            with open(file_path, 'rb') as f:
                while sent < file_size:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    tcp_client.send(chunk)
                    sent += len(chunk)
                    progress = (sent / file_size) * 100
                    self.update_progress(f"Отправка {filename}", progress)
                    
            self.update_progress("", 0)
            self.log_message(f"✅ {filename} отправлен", system=True)
            tcp_client.close()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}", system=True)
        finally:
            if file_id in self.active_transfers:
                del self.active_transfers[file_id]
                
    def receive_file(self, peer_addr, file_id, filename, file_size):
        """Прием файла"""
        try:
            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_client.connect(peer_addr)
            
            request = json.dumps({'type': 'file_request_data', 'file_id': file_id})
            tcp_client.send(request.encode())
            time.sleep(0.1)
            
            save_path = os.path.join(self.download_folder, filename)
            received = 0
            
            with open(save_path, 'wb') as f:
                while received < file_size:
                    chunk = tcp_client.recv(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    progress = (received / file_size) * 100
                    self.update_progress(f"Загрузка {filename}", progress)
                    
            self.update_progress("", 0)
            self.log_message(f"✅ {filename} сохранен", system=True)
            tcp_client.close()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}", system=True)
            
    def add_contact(self):
        """Добавление контакта"""
        add_win = tk.Toplevel(self.root)
        add_win.title("Добавить контакт")
        add_win.geometry("400x350")
        
        tk.Label(add_win, text="ДОБАВЛЕНИЕ КОНТАКТА", font=('Arial', 12, 'bold')).pack(pady=10)
        
        tk.Label(add_win, text="Имя:").pack()
        name_entry = tk.Entry(add_win, width=30)
        name_entry.pack(pady=5)
        
        tk.Label(add_win, text="UDP порт:").pack()
        udp_entry = tk.Entry(add_win, width=30)
        udp_entry.pack(pady=5)
        
        tk.Label(add_win, text="TCP порт:").pack()
        tcp_entry = tk.Entry(add_win, width=30)
        tcp_entry.pack(pady=5)
        
        def save():
            name = name_entry.get().strip()
            udp = udp_entry.get().strip()
            tcp = tcp_entry.get().strip()
            
            if not all([name, udp, tcp]):
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
                
            try:
                self.connections[name] = {
                    'udp_addr': ('127.0.0.1', int(udp)),
                    'tcp_addr': ('127.0.0.1', int(tcp))
                }
                self.contacts_list.insert(tk.END, f"{name} 🟢")
                self.log_message(f"✅ Контакт {name} добавлен", system=True)
                add_win.destroy()
            except:
                messagebox.showerror("Ошибка", "Порт должен быть числом")
                
        tk.Button(add_win, text="Сохранить", command=save, bg="lightgreen").pack(pady=10)
        tk.Button(add_win, text="Отмена", command=add_win.destroy).pack()
        
    def delete_contact(self):
        """Удаление контакта"""
        selection = self.contacts_list.curselection()
        if selection:
            name = self.contacts_list.get(selection[0]).split(' ')[0]
            if name in self.connections:
                del self.connections[name]
            self.contacts_list.delete(selection)
            
    def open_chat(self, event):
        """Открытие чата"""
        selection = self.contacts_list.curselection()
        if selection:
            name = self.contacts_list.get(selection[0]).split(' ')[0]
            self.current_chat = name
            self.chat_title.config(text=f"💬 Чат с {name}")
            self.send_btn.config(state=tk.NORMAL)
            self.log_message(f"🔗 Чат с {name} открыт", system=True)
            
    def send_message(self):
        """Отправка сообщения"""
        if not self.current_chat:
            return
            
        message = self.message_entry.get().strip()
        if not message:
            return
            
        if self.current_chat in self.connections:
            peer = self.connections[self.current_chat]
            msg_data = json.dumps({
                'type': 'chat',
                'sender': self.username,
                'content': message
            })
            self.udp_socket.sendto(msg_data.encode(), peer['udp_addr'])
            self.log_message(f"Вы: {message}")
            self.message_entry.delete(0, tk.END)
            
    def log_message(self, msg, system=False):
        """Добавление сообщения"""
        self.chat_area.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        prefix = "🔵 " if system else ""
        self.chat_area.insert(tk.END, f"[{timestamp}] {prefix}{msg}\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
    def highlight_contact(self, name):
        """Подсветка контакта"""
        for i in range(self.contacts_list.size()):
            if self.contacts_list.get(i).startswith(name):
                self.contacts_list.selection_clear(0, tk.END)
                self.contacts_list.selection_set(i)
                break
                
    def update_progress(self, text, value):
        """Обновление прогресса"""
        self.progress_label.config(text=text)
        self.progress_bar['value'] = value
        self.root.update_idletasks()
        
    def format_size(self, size):
        """Форматирование размера"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"
        
    def run(self):
        """Запуск"""
        self.root.mainloop()

# Запуск двух экземпляров
if __name__ == "__main__":
    import subprocess
    import sys
    
    # Спрашиваем, как тестировать
    answer = messagebox.askyesno("Тестирование", 
                                 "Запустить два экземпляра для тестирования?\n\n"
                                 "ДА - запустит Алису и Боба автоматически\n"
                                 "НЕТ - запустит только один экземпляр")
    
    if answer:
        # Запускаем два экземпляра с разными портами
        print("Запуск тестовых экземпляров...")
        
        # Экземпляр 1 (Алиса) - порты 9001, 9002
        threading.Thread(target=lambda: TestP2PMessenger("Алиса", 9001, 9002).run(), daemon=True).start()
        time.sleep(1)
        
        # Экземпляр 2 (Боб) - порты 9003, 9004
        threading.Thread(target=lambda: TestP2PMessenger("Боб", 9003, 9004).run(), daemon=True).start()
        
        # Добавляем контакты автоматически
        time.sleep(2)
        print("\n" + "="*50)
        print("✅ Два экземпляра запущены!")
        print("📝 Для тестирования:")
        print("1. В окне Алисы нажми 'Добавить контакт'")
        print("2. Введи: Имя=Боб, UDP=9003, TCP=9004")
        print("3. В окне Боба нажми 'Добавить контакт'")
        print("4. Введи: Имя=Алиса, UDP=9001, TCP=9002")
        print("5. Дважды кликни по контакту и общайся!")
        print("="*50)
        
        # Запускаем главный цикл
        tk.Tk().mainloop()
    else:
        # Запускаем один экземпляр
        app = TestP2PMessenger("Пользователь")
        app.run()
