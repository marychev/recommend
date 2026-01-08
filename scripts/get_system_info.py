#!/usr/bin/env python3
"""
Скрипт для получения информации о характеристиках системы
Работает без дополнительных зависимостей, используя стандартные библиотеки и системные команды
"""
import platform
import sys
import subprocess
import re


def format_bytes(bytes_value):
    """Форматирует байты в читаемый формат"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def run_command(cmd, timeout=10):
    """Выполняет системную команду и возвращает результат"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None

def parse_memory_line(line):
    """Парсит строку из /proc/meminfo"""
    parts = line.split()
    if len(parts) >= 2:
        value = int(parts[1])
        if len(parts) > 2 and parts[2] == 'kB':
            value *= 1024  # Конвертируем KB в байты
        return value
    return 0


def get_system_info():
    """Собирает информацию о системе"""
    info = {
        'platform': {},
        'cpu': {},
        'memory': {},
        'disk': {},
        'docker': {}
    }
    
    # Платформа
    info['platform'] = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'architecture': platform.architecture()[0]
    }
    
    # CPU - используем lscpu или /proc/cpuinfo
    cpu_info = {}
    
    # Попытка получить информацию через lscpu
    lscpu_output = run_command('lscpu')
    if lscpu_output:
        lines = lscpu_output.split('\n')
        for line in lines:
            if 'CPU(s):' in line and 'On-line' not in line and 'Off-line' not in line:
                match = re.search(r'(\d+)', line)
                if match:
                    cpu_info['logical_cores'] = int(match.group(1))
            elif 'Thread(s) per core:' in line:
                match = re.search(r'(\d+)', line)
                if match:
                    threads_per_core = int(match.group(1))
            elif 'Core(s) per socket:' in line:
                match = re.search(r'(\d+)', line)
                if match:
                    cores_per_socket = int(match.group(1))
            elif 'Socket(s):' in line:
                match = re.search(r'(\d+)', line)
                if match:
                    sockets = int(match.group(1))
            elif 'CPU max MHz:' in line or 'CPU MHz:' in line:
                match = re.search(r'(\d+\.?\d*)', line)
                if match:
                    cpu_info['frequency'] = {'current': f"{float(match.group(1)):.2f} MHz"}
        
        if 'logical_cores' in cpu_info and 'cores_per_socket' in locals():
            cpu_info['physical_cores'] = cores_per_socket * sockets if 'sockets' in locals() else cpu_info['logical_cores']
    
    # Если lscpu не сработал, используем /proc/cpuinfo
    if not cpu_info:
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                logical_cores = len([line for line in cpuinfo.split('\n') if 'processor' in line.lower()])
                physical_cores = len(set([line.split(':')[1].strip() 
                                         for line in cpuinfo.split('\n') 
                                         if 'physical id' in line.lower()]))
                if logical_cores:
                    cpu_info['logical_cores'] = logical_cores
                if physical_cores:
                    cpu_info['physical_cores'] = physical_cores
                else:
                    cpu_info['physical_cores'] = logical_cores
        except Exception:
            cpu_info['logical_cores'] = platform.processor() or "N/A"
            cpu_info['physical_cores'] = "N/A"
    
    info['cpu'] = cpu_info
    
    # Память - используем /proc/meminfo или free
    mem_info = {}
    free_output = run_command('free -b')  # -b для байтов
    if free_output:
        lines = free_output.split('\n')
        for line in lines:
            if 'Mem:' in line:
                parts = line.split()
                if len(parts) >= 4:
                    mem_info['total'] = format_bytes(int(parts[1]))
                    mem_info['used'] = format_bytes(int(parts[2]))
                    mem_info['available'] = format_bytes(int(parts[6]) if len(parts) > 6 else int(parts[3]))
                    if int(parts[1]) > 0:
                        mem_info['percent'] = f"{(int(parts[2]) / int(parts[1])) * 100:.1f}%"
            elif 'Swap:' in line:
                parts = line.split()
                if len(parts) >= 3:
                    mem_info['swap_total'] = format_bytes(int(parts[1]))
                    mem_info['swap_used'] = format_bytes(int(parts[2]))
                    if int(parts[1]) > 0:
                        mem_info['swap_percent'] = f"{(int(parts[2]) / int(parts[1])) * 100:.1f}%"
    
    # Если free не сработал, используем /proc/meminfo
    if not mem_info:
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_total = 0
                mem_available = 0
                mem_free = 0
                swap_total = 0
                swap_free = 0
                
                for line in meminfo.split('\n'):
                    if 'MemTotal:' in line:
                        mem_total = parse_memory_line(line)
                    elif 'MemAvailable:' in line:
                        mem_available = parse_memory_line(line)
                    elif 'MemFree:' in line:
                        mem_free = parse_memory_line(line)
                    elif 'SwapTotal:' in line:
                        swap_total = parse_memory_line(line)
                    elif 'SwapFree:' in line:
                        swap_free = parse_memory_line(line)
                
                if mem_total > 0:
                    mem_info['total'] = format_bytes(mem_total)
                    mem_info['used'] = format_bytes(mem_total - (mem_available if mem_available > 0 else mem_free))
                    mem_info['available'] = format_bytes(mem_available if mem_available > 0 else mem_free)
                    mem_info['percent'] = f"{((mem_total - (mem_available if mem_available > 0 else mem_free)) / mem_total) * 100:.1f}%"
                
                if swap_total > 0:
                    mem_info['swap_total'] = format_bytes(swap_total)
                    mem_info['swap_used'] = format_bytes(swap_total - swap_free)
                    mem_info['swap_percent'] = f"{((swap_total - swap_free) / swap_total) * 100:.1f}%"
        except Exception:
            pass
    
    info['memory'] = mem_info
    
    # Диск - используем df
    disk_info = {}
    df_output = run_command('df -B1 /')
    if df_output:
        lines = df_output.split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 4:
                disk_info['total'] = format_bytes(int(parts[1]))
                disk_info['used'] = format_bytes(int(parts[2]))
                disk_info['free'] = format_bytes(int(parts[3]))
                if int(parts[1]) > 0:
                    disk_info['percent'] = f"{(int(parts[2]) / int(parts[1])) * 100:.1f}%"
    
    info['disk'] = disk_info
    
    # Docker (если доступен)
    docker_version = run_command('docker --version', timeout=5)
    if docker_version:
        info['docker']['version'] = docker_version
        
        # Статистика контейнеров
        docker_stats = run_command('docker stats --no-stream --format "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}"', timeout=10)
        if docker_stats:
            containers = []
            for line in docker_stats.split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 4:
                        containers.append({
                            'name': parts[0],
                            'cpu_percent': parts[1],
                            'memory_usage': parts[2],
                            'memory_percent': parts[3]
                        })
            if containers:
                info['docker']['containers'] = containers
    
    return info


def print_system_info(info):
    """Выводит информацию о системе в читаемом формате"""
    print("=" * 80)
    print("ХАРАКТЕРИСТИКИ СИСТЕМЫ ДЛЯ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    print()
    
    # Платформа
    print("🖥️  ПЛАТФОРМА:")
    print(f"   Система:          {info['platform']['system']}")
    print(f"   Версия:           {info['platform']['release']} {info['platform']['version']}")
    print(f"   Архитектура:      {info['platform']['architecture']}")
    print(f"   Процессор:        {info['platform']['processor']}")
    print()
    
    # CPU
    print("⚙️  ПРОЦЕССОР:")
    print(f"   Физических ядер:  {info['cpu']['physical_cores']}")
    print(f"   Логических ядер:  {info['cpu']['logical_cores']}")
    if info['cpu'].get('frequency'):
        print(f"   Частота:          {info['cpu']['frequency'].get('current', 'N/A')}")
        print(f"   Диапазон:         {info['cpu']['frequency'].get('min', 'N/A')} - {info['cpu']['frequency'].get('max', 'N/A')}")
    if info['cpu'].get('usage_percent'):
        avg_usage = sum(info['cpu']['usage_percent']) / len(info['cpu']['usage_percent'])
        print(f"   Загрузка CPU:     {avg_usage:.1f}%")
    print()
    
    # Память
    print("💾 ПАМЯТЬ:")
    print(f"   Всего RAM:        {info['memory']['total']}")
    print(f"   Использовано:     {info['memory']['used']} ({info['memory']['percent']})")
    print(f"   Доступно:         {info['memory']['available']}")
    print(f"   Swap всего:       {info['memory']['swap_total']}")
    print(f"   Swap использовано: {info['memory']['swap_used']} ({info['memory']['swap_percent']})")
    print()
    
    # Диск
    print("💿 ДИСК:")
    print(f"   Всего места:      {info['disk']['total']}")
    print(f"   Использовано:     {info['disk']['used']} ({info['disk']['percent']})")
    print(f"   Свободно:         {info['disk']['free']}")
    print()
    
    # Docker
    if 'version' in info['docker']:
        print("🐳 DOCKER:")
        print(f"   Версия:           {info['docker']['version']}")
        if 'containers' in info['docker'] and info['docker']['containers']:
            print("   Контейнеры:")
            for container in info['docker']['containers']:
                print(f"      • {container['name']}")
                print(f"        CPU: {container['cpu_percent']}, Memory: {container['memory_usage']} ({container['memory_percent']})")
        print()
    
    # Рекомендации из документации
    print("=" * 80)
    print("📋 РЕКОМЕНДУЕМЫЕ НАСТРОЙКИ (из документации):")
    print("=" * 80)
    print()
    print("Docker Desktop Settings:")
    print("   • Memory:          минимум 8GB (рекомендуется 12GB)")
    print("   • CPUs:             минимум 4 ядра (рекомендуется 6-8)")
    print("   • Swap:            2GB")
    print("   • Disk image size: 50GB+")
    print()
    print("Лимиты контейнеров:")
    print("   • ClickHouse:      CPU 1-2 ядра, RAM 2-4GB")
    print("   • Kafka:           CPU 0.5-1 ядро, RAM 512MB-1GB")
    print("   • Redis:           CPU 0.25-0.5 ядра, RAM 256MB-512MB")
    print()

if __name__ == '__main__':
    try:
        info = get_system_info()
        print_system_info(info)
    except Exception as e:
        print(f"Ошибка при получении информации о системе: {e}", file=sys.stderr)
        sys.exit(1)
