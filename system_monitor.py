#!/usr/bin/env python3
"""
Системный монитор для Linux Mint
Мониторит CPU (Intel), RAM, GPU (Intel/Nvidia) с автообновлением 2 секунд
"""

import psutil
import time
import os
import subprocess
from dataclasses import dataclass
from typing import Optional, Dict, Any
import json

# Попробуем импортировать библиотеку для NVIDIA GPU
try:
    import pynvml
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False

# Попробуем импортировать библиотеку для Intel GPU
try:
    import intel_gpu_top
    INTEL_GPU_AVAILABLE = True
except ImportError:
    INTEL_GPU_AVAILABLE = False

@dataclass
class SystemInfo:
    """Класс для хранения информации о системе"""
    cpu_name: str = ""
    cpu_cores: int = 0
    cpu_threads: int = 0
    cpu_usage: float = 0.0
    cpu_freq: float = 0.0
    
    ram_total: float = 0.0
    ram_used: float = 0.0
    ram_percent: float = 0.0
    
    gpu_intel_name: str = ""
    gpu_intel_usage: float = 0.0
    gpu_intel_mem_used: float = 0.0
    
    gpu_nvidia_name: str = ""
    gpu_nvidia_usage: float = 0.0
    gpu_nvidia_mem_used: float = 0.0
    gpu_nvidia_mem_total: float = 0.0
    gpu_nvidia_temp: float = 0.0

class SystemMonitor:
    def __init__(self):
        self.system_info = SystemInfo()
        self._init_cpu_info()
        self._init_gpu_info()
        
    def _init_cpu_info(self):
        """Получение информации о процессоре"""
        try:
            # Получаем имя процессора из /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        self.system_info.cpu_name = line.split(':')[1].strip()
                        break
            
            self.system_info.cpu_cores = psutil.cpu_count(logical=False)
            self.system_info.cpu_threads = psutil.cpu_count(logical=True)
        except Exception as e:
            print(f"Ошибка при получении информации о CPU: {e}")
    
    def _init_gpu_info(self):
        """Получение информации о GPU"""
        # Информация об Intel GPU
        try:
            result = subprocess.run(['lspci', '-v'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'Intel' in line and ('Graphics' in line or 'UHD' in line or 'HD Graphics' in line):
                    self.system_info.gpu_intel_name = line.split(':')[2].strip()
                    break
        except Exception as e:
            print(f"Ошибка при получении информации об Intel GPU: {e}")
        
        # Информация о NVIDIA GPU
        if NVIDIA_AVAILABLE:
            try:
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                self.system_info.gpu_nvidia_name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                pynvml.nvmlShutdown()
            except Exception as e:
                print(f"Ошибка при получении информации о NVIDIA GPU: {e}")
    
    def update_cpu_info(self):
        """Обновление информации о CPU"""
        self.system_info.cpu_usage = psutil.cpu_percent(interval=0.1)
        
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                self.system_info.cpu_freq = cpu_freq.current
        except:
            self.system_info.cpu_freq = 0.0
    
    def update_ram_info(self):
        """Обновление информации о RAM"""
        mem = psutil.virtual_memory()
        self.system_info.ram_total = mem.total / (1024**3)  # Конвертируем в GB
        self.system_info.ram_used = mem.used / (1024**3)    # Конвертируем в GB
        self.system_info.ram_percent = mem.percent
    
    def update_intel_gpu_info(self):
        """Обновление информации об Intel GPU"""
        # Используем intel_gpu_top если доступно
        if INTEL_GPU_AVAILABLE:
            try:
                # Здесь можно добавить вызов intel_gpu_top API
                # Временная заглушка - получение данных через системные файлы
                self.system_info.gpu_intel_usage = 0.0
                self.system_info.gpu_intel_mem_used = 0.0
            except Exception as e:
                print(f"Ошибка при обновлении информации об Intel GPU: {e}")
        else:
            # Альтернативный метод через sysfs (если доступно)
            try:
                with open('/sys/class/drm/card0/gt_cur_freq_mhz', 'r') as f:
                    freq = int(f.read().strip())
                    self.system_info.gpu_intel_usage = min(freq / 1000.0, 100.0)
            except:
                self.system_info.gpu_intel_usage = 0.0
    
    def update_nvidia_gpu_info(self):
        """Обновление информации о NVIDIA GPU"""
        if not NVIDIA_AVAILABLE:
            return
        
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            # Использование GPU
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            self.system_info.gpu_nvidia_usage = utilization.gpu
            
            # Память
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            self.system_info.gpu_nvidia_mem_used = memory.used / (1024**3)  # GB
            self.system_info.gpu_nvidia_mem_total = memory.total / (1024**3)  # GB
            
            # Температура
            try:
                self.system_info.gpu_nvidia_temp = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU
                )
            except:
                self.system_info.gpu_nvidia_temp = 0.0
            
            pynvml.nvmlShutdown()
        except Exception as e:
            print(f"Ошибка при обновлении информации о NVIDIA GPU: {e}")
    
    def update_all(self):
        """Обновление всей информации"""
        self.update_cpu_info()
        self.update_ram_info()
        self.update_intel_gpu_info()
        self.update_nvidia_gpu_info()
    
    def get_html_report(self) -> str:
        """Генерация HTML-отчёта"""
        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Системный монитор</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    color: white;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                }}
                .card {{
                    background: white;
                    border-radius: 15px;
                    padding: 25px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    transition: transform 0.3s ease;
                }}
                .card:hover {{
                    transform: translateY(-5px);
                }}
                .card h3 {{
                    color: #667eea;
                    margin-top: 0;
                    border-bottom: 2px solid #f0f0f0;
                    padding-bottom: 10px;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 8px 0;
                    border-bottom: 1px solid #f5f5f5;
                }}
                .progress-bar {{
                    height: 20px;
                    background: #f0f0f0;
                    border-radius: 10px;
                    margin: 10px 0;
                    overflow: hidden;
                }}
                .progress-fill {{
                    height: 100%;
                    border-radius: 10px;
                    transition: width 2 s ease;
                }}
                .cpu-progress {{ background: linear-gradient(90deg, #4CAF50, #8BC34A); }}
                .ram-progress {{ background: linear-gradient(90deg, #2196F3, #03A9F4); }}
                .gpu-intel-progress {{ background: linear-gradient(90deg, #FF9800, #FFC107); }}
                .gpu-nvidia-progress {{ background: linear-gradient(90deg, #9C27B0, #E91E63); }}
                .timestamp {{
                    text-align: center;
                    color: white;
                    margin-top: 30px;
                    font-size: 0.9em;
                    opacity: 0.8;
                }}
                .value {{
                    font-weight: bold;
                    color: #667eea;
                }}
                .warning {{ color: #ff9800; }}
                .danger {{ color: #f44336; }}
            </style>
            <script>
                function updatePage() {{
                    fetch('/data')
                        .then(response => response.json())
                        .then(data => {{
                            // Обновляем значения
                            document.getElementById('cpu-usage').textContent = data.cpu_usage.toFixed(1) + '%';
                            document.getElementById('cpu-usage-bar').style.width = data.cpu_usage + '%';
                            document.getElementById('cpu-freq').textContent = data.cpu_freq.toFixed(0) + ' MHz';
                            
                            document.getElementById('ram-used').textContent = data.ram_used.toFixed(2) + ' GB';
                            document.getElementById('ram-total').textContent = data.ram_total.toFixed(2) + ' GB';
                            document.getElementById('ram-percent').textContent = data.ram_percent.toFixed(1) + '%';
                            document.getElementById('ram-bar').style.width = data.ram_percent + '%';
                            
                            document.getElementById('gpu-intel-usage').textContent = data.gpu_intel_usage.toFixed(1) + '%';
                            document.getElementById('gpu-intel-bar').style.width = data.gpu_intel_usage + '%';
                            
                            if (data.gpu_nvidia_usage > 0) {{
                                document.getElementById('gpu-nvidia-usage').textContent = data.gpu_nvidia_usage.toFixed(1) + '%';
                                document.getElementById('gpu-nvidia-bar').style.width = data.gpu_nvidia_usage + '%';
                                document.getElementById('gpu-nvidia-mem').textContent = 
                                    data.gpu_nvidia_mem_used.toFixed(2) + ' / ' + data.gpu_nvidia_mem_total.toFixed(2) + ' GB';
                                document.getElementById('gpu-nvidia-temp').textContent = data.gpu_nvidia_temp.toFixed(0) + '°C';
                            }}
                            
                            document.getElementById('timestamp').textContent = 'Последнее обновление: ' + new Date().toLocaleTimeString();
                        }})
                        .catch(error => console.error('Ошибка:', error));
                }}
                
                // Автообновление каждые 2 секунд
                setInterval(updatePage, 500);
                
                // Первоначальная загрузка
                document.addEventListener('DOMContentLoaded', updatePage);
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🖥️ Системный монитор Linux Mint</h1>
                    <p>Режим реального времени | Обновление каждые 2 секунд</p>
                </div>
                
                <div class="grid">
                    <!-- CPU -->
                    <div class="card">
                        <h3>💻 Процессор (Intel)</h3>
                        <div class="info-row">
                            <span>Модель:</span>
                            <span class="value">{self.system_info.cpu_name}</span>
                        </div>
                        <div class="info-row">
                            <span>Ядра/Потоки:</span>
                            <span class="value">{self.system_info.cpu_cores}/{self.system_info.cpu_threads}</span>
                        </div>
                        <div class="info-row">
                            <span>Использование:</span>
                            <span class="value" id="cpu-usage">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill cpu-progress" id="cpu-usage-bar" style="width: 0%"></div>
                        </div>
                        <div class="info-row">
                            <span>Частота:</span>
                            <span class="value" id="cpu-freq">0 MHz</span>
                        </div>
                    </div>
                    
                    <!-- RAM -->
                    <div class="card">
                        <h3>🧠 Оперативная память</h3>
                        <div class="info-row">
                            <span>Использовано:</span>
                            <span class="value" id="ram-used">0 GB</span>
                        </div>
                        <div class="info-row">
                            <span>Всего:</span>
                            <span class="value" id="ram-total">0 GB</span>
                        </div>
                        <div class="info-row">
                            <span>Загрузка:</span>
                            <span class="value" id="ram-percent">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill ram-progress" id="ram-bar" style="width: 0%"></div>
                        </div>
                    </div>
                    
                    <!-- Intel GPU -->
                    <div class="card">
                        <h3>🎨 Графика Intel</h3>
                        <div class="info-row">
                            <span>Модель:</span>
                            <span class="value">{self.system_info.gpu_intel_name or 'Не обнаружена'}</span>
                        </div>
                        <div class="info-row">
                            <span>Загрузка GPU:</span>
                            <span class="value" id="gpu-intel-usage">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill gpu-intel-progress" id="gpu-intel-bar" style="width: 0%"></div>
                        </div>
                    </div>
                    
                    <!-- NVIDIA GPU -->
        """
        
        # Добавляем секцию для NVIDIA GPU только если она обнаружена
        if self.system_info.gpu_nvidia_name:
            html += f"""
                    <div class="card">
                        <h3>🚀 Графика NVIDIA</h3>
                        <div class="info-row">
                            <span>Модель:</span>
                            <span class="value">{self.system_info.gpu_nvidia_name}</span>
                        </div>
                        <div class="info-row">
                            <span>Загрузка GPU:</span>
                            <span class="value" id="gpu-nvidia-usage">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill gpu-nvidia-progress" id="gpu-nvidia-bar" style="width: 0%"></div>
                        </div>
                        <div class="info-row">
                            <span>Память GPU:</span>
                            <span class="value" id="gpu-nvidia-mem">0 GB</span>
                        </div>
                        <div class="info-row">
                            <span>Температура:</span>
                            <span class="value" id="gpu-nvidia-temp">0°C</span>
                        </div>
                    </div>
            """
        
        html += """
                </div>
                
                <div class="timestamp" id="timestamp">
                    Последнее обновление: загрузка...
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

def main():
    """Основная функция мониторинга в терминале"""
    monitor = SystemMonitor()
    
    print("🖥️ Системный монитор Linux Mint")
    print("=" * 50)
    print(f"Процессор: {monitor.system_info.cpu_name}")
    print(f"Ядра/Потоки: {monitor.system_info.cpu_cores}/{monitor.system_info.cpu_threads}")
    
    if monitor.system_info.gpu_intel_name:
        print(f"Intel GPU: {monitor.system_info.gpu_intel_name}")
    
    if monitor.system_info.gpu_nvidia_name:
        print(f"NVIDIA GPU: {monitor.system_info.gpu_nvidia_name}")
    
    print("=" * 50)
    print("Нажмите Ctrl+C для выхода")
    print()
    
    try:
        while True:
            monitor.update_all()
            
            # Очищаем экран
            print("\033[2J\033[H")
            
            print(f"💻 CPU: {monitor.system_info.cpu_usage:5.1f}% | "
                  f"{monitor.system_info.cpu_freq:.0f} MHz")
            print(f"🧠 RAM: {monitor.system_info.ram_used:.2f} GB / "
                  f"{monitor.system_info.ram_total:.2f} GB ({monitor.system_info.ram_percent:.1f}%)")
            
            if monitor.system_info.gpu_intel_name:
                print(f"🎨 Intel GPU: {monitor.system_info.gpu_intel_usage:5.1f}%")
            
            if monitor.system_info.gpu_nvidia_name:
                print(f"🚀 NVIDIA GPU: {monitor.system_info.gpu_nvidia_usage:5.1f}% | "
                      f"Память: {monitor.system_info.gpu_nvidia_mem_used:.2f} GB | "
                      f"Температура: {monitor.system_info.gpu_nvidia_temp:.0f}°C")
            
            print("-" * 50)
            print("Обновление через 2 секунд...")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nЗавершение работы монитора...")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()