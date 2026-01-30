#!/usr/bin/env python3
"""
Web-сервер для отображения системного монитора в реальном времени
"""

from flask import Flask, jsonify
from system_monitor import SystemMonitor
import threading
import time

app = Flask(__name__)
monitor = SystemMonitor()

def update_loop():
    """Фоновая задача для обновления данных"""
    while True:
        monitor.update_all()
        time.sleep(2)

@app.route('/')
def index():
    """Главная страница с HTML-отчётом"""
    return monitor.get_html_report()

@app.route('/data')
def get_data():
    """API для получения данных в формате JSON"""
    return jsonify({
        'cpu_usage': monitor.system_info.cpu_usage,
        'cpu_freq': monitor.system_info.cpu_freq,
        'ram_used': monitor.system_info.ram_used,
        'ram_total': monitor.system_info.ram_total,
        'ram_percent': monitor.system_info.ram_percent,
        'gpu_intel_usage': monitor.system_info.gpu_intel_usage,
        'gpu_nvidia_usage': monitor.system_info.gpu_nvidia_usage,
        'gpu_nvidia_mem_used': monitor.system_info.gpu_nvidia_mem_used,
        'gpu_nvidia_mem_total': monitor.system_info.gpu_nvidia_mem_total,
        'gpu_nvidia_temp': monitor.system_info.gpu_nvidia_temp
    })

if __name__ == "__main__":
    # Запускаем фоновый поток для обновления данных
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()
    
    # Запускаем Flask сервер
    print("🚀 Запуск системного монитора...")
    print("📊 Терминальный монитор: python system_monitor.py")
    print("🌐 Веб-интерфейс: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)