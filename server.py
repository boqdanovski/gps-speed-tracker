from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

# Создаем директорию для данных (в Vercel это временная файловая система)
DATA_DIR = '/tmp/speed_data'
ALL_DEVICES_FILE = os.path.join(DATA_DIR, 'all_devices.txt')

# Создаем директорию если не существует
os.makedirs(DATA_DIR, exist_ok=True)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Получаем IP клиента из заголовков
        client_ip = self.headers.get('X-Forwarded-For', 'unknown').split(',')[0].strip()
        if client_ip == 'unknown':
            client_ip = self.headers.get('X-Real-IP', 'unknown')
        
        # Получаем название устройства из заголовка или используем IP
        device_name = self.headers.get('X-Device-Name', client_ip)
        
        # Заменяем точки на подчеркивания для имени файла
        safe_name = device_name.replace('.', '_').replace(':', '_').replace(' ', '_')
        device_file = os.path.join(DATA_DIR, f'device_{safe_name}.txt')
        device_log_file = os.path.join(DATA_DIR, f'device_{safe_name}_log.txt')

        # Читаем данные
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        speed_data = post_data.decode('utf-8').strip()

        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

        print(f'📥 Получена скорость от {device_name} ({client_ip}): {speed_data} км/ч в {timestamp}')

        # Перезаписываем файл с текущей скоростью (каждую секунду)
        with open(device_file, 'w') as f:
            f.write(speed_data)  # Только скорость, без переноса строки

        # Добавляем в лог
        with open(device_log_file, 'a') as f:
            f.write(f'{timestamp} - {speed_data} км/ч\n')

        # Добавляем в общий лог
        with open(ALL_DEVICES_FILE, 'a') as f:
            f.write(f'{timestamp} - {device_name} ({client_ip}) - {speed_data} км/ч\n')

        # Отправляем ответ
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        self.wfile.write(f'Speed updated for {device_name}: {speed_data} km/h'.encode())

        print(f'💾 Данные от {device_name} сохранены.')

    def handle_file_download(self):
        """Обработка скачивания файлов"""
        try:
            # Извлекаем имя файла из пути
            filename = self.path.replace('/download/', '')
            
            # Проверяем, что файл существует в нашей директории
            if not filename.startswith('device_') and filename != 'all_devices.txt':
                self.send_error(404, "File not found")
                return
                
            filepath = os.path.join(DATA_DIR, filename)
            
            if not os.path.exists(filepath):
                self.send_error(404, "File not found")
                return
                
            # Читаем файл
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Определяем тип контента
            if filename.endswith('.txt'):
                content_type = 'text/plain; charset=utf-8'
            else:
                content_type = 'application/octet-stream'
            
            # Отправляем файл
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
            print(f'📥 Файл {filename} отправлен для скачивания')
            
        except Exception as e:
            print(f'❌ Ошибка при скачивании файла: {e}')
            self.send_error(500, "Internal server error")

    def do_GET(self):
        # Проверяем, запрашивается ли конкретный файл
        if self.path.startswith('/download/'):
            self.handle_file_download()
            return
            
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>⛵ 69F СКОРОСТЬ - Все устройства</title>
    <meta http-equiv="refresh" content="1">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .content {{
            padding: 30px;
        }}
        .device-card {{ 
            background: #f8f9fa; 
            border: 1px solid #e9ecef; 
            border-radius: 8px; 
            padding: 20px; 
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }}
        .device-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .device-card h2 {{ 
            margin: 0 0 10px 0; 
            color: #495057; 
            font-size: 1.3em;
        }}
        .speed {{ 
            font-size: 2em; 
            font-weight: bold; 
            color: #28a745; 
            margin: 10px 0;
        }}
        .timestamp {{ 
            font-size: 0.9em; 
            color: #6c757d; 
            margin: 5px 0;
        }}
        .no-data {{
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 40px;
        }}
        .log-section {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-top: 30px;
        }}
        .log-section h2 {{
            color: #495057;
            margin-top: 0;
        }}
        .log-content {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }}
        .status {{
            text-align: center;
            color: #6c757d;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⛵ 69F СКОРОСТЬ</h1>
            <p>Отслеживание скорости всех устройств</p>
        </div>
        <div class="content">
            <div class="status">
                Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
'''

        # Читаем данные из файлов устройств
        device_files = []
        if os.path.exists(DATA_DIR):
            device_files = [f for f in os.listdir(DATA_DIR) if f.startswith('device_') and f.endswith('.txt') and not f.endswith('_log.txt')]
        
        if not device_files:
            html_content += '<div class="no-data">Нет данных от устройств. Подключите Android приложения.</div>'
        else:
            for filename in sorted(device_files):
                filepath = os.path.join(DATA_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        speed = f.read().strip()
                    device_name = filename.replace('device_', '').replace('.txt', '').replace('_', ' ')
                    last_update = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    safe_name = device_name.replace(' ', '_')
                    
                    # Проверяем, как давно было последнее обновление
                    current_time = datetime.now()
                    last_update_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    time_diff = (current_time - last_update_time).total_seconds()
                    
                    # Если прошло больше 10 секунд - показываем "Device not Tracking"
                    if time_diff > 10:
                        status_text = "🔴 Device not Tracking"
                        status_color = "#dc3545"
                        speed_display = "—"
                    else:
                        status_text = "🟢 Device Tracking"
                        status_color = "#28a745"
                        speed_display = f"{speed} км/ч"
                    
                    html_content += f'''
                    <div class="device-card">
                        <h2>📱 Устройство: {device_name}</h2>
                        <div style="color: {status_color}; font-weight: bold; margin-bottom: 10px;">{status_text}</div>
                        <div class="speed">{speed_display}</div>
                        <div class="timestamp">Последнее обновление: {last_update}</div>
                        <div style="margin-top: 10px;">
                            <a href="/download/device_{safe_name}.txt" style="color: #007bff; text-decoration: none; margin-right: 15px;">📄 Текущая скорость (обновляется каждую секунду)</a>
                            <a href="/download/device_{safe_name}_log.txt" style="color: #28a745; text-decoration: none;">📊 История</a>
                        </div>
                        <div style="margin-top: 5px; font-size: 0.9em; color: #6c757d;">
                            Прямая ссылка: <code>https://gps-speed-tracker.vercel.app/download/device_{safe_name}.txt</code>
                        </div>
                    </div>
                    '''
                except Exception as e:
                    html_content += f'<div class="device-card"><h2>❌ Ошибка чтения {filename}: {e}</h2></div>'

        # Добавляем общий лог
        html_content += '''
            <div class="log-section">
                <h2>📋 Общий лог всех устройств</h2>
                <div style="margin-bottom: 15px;">
                    <a href="/download/all_devices.txt" style="color: #dc3545; text-decoration: none; font-weight: bold;">📥 Скачать полный лог</a>
                </div>
                <div class="log-content">
'''
        if os.path.exists(ALL_DEVICES_FILE):
            try:
                with open(ALL_DEVICES_FILE, 'r') as f:
                    log_content = f.read()
                    if log_content.strip():
                        html_content += log_content
                    else:
                        html_content += 'Лог пока пуст.'
            except Exception as e:
                html_content += f'Ошибка чтения лога: {e}'
        else:
            html_content += 'Лог пока пуст.'
        
        html_content += '''
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''
        self.wfile.write(html_content.encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Device-Name')
        self.end_headers()
