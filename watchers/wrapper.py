import os
import subprocess
import signal

# Servis konfigürasyonları
directories = ["/home", "/home1", "/home2"]
base_watcher_path = '/etc/WebP-Watch-N-Process/watchers/product-image-watcher.sh'
base_processor_path = '/etc/WebP-Watch-N-Process/watchers/product-image-processor.py'

# E-ticaret sitelerini bulmak için kullanılacak fonksiyon
def find_ecommerce_sites(directories):
    ecommerce_sites = []
    for directory in directories:
        if os.path.exists(directory):
            for subdir in next(os.walk(directory))[1]:
                index_path = os.path.join(directory, subdir, "public_html", "index.php")
                if os.path.isfile(index_path):
                    ecommerce_sites.append(os.path.join(directory, subdir))
    return ecommerce_sites

# E-ticaret sitelerini bul
ecommerce_sites = find_ecommerce_sites(directories)

# Bulunan siteleri ekrana yazdır
print("Bulunan E-ticaret Siteleri:")
for site in ecommerce_sites:
    print(f"Site: {site}")

# Alt işlem listesi
processes = []

# Her bir site için watcher ve processor başlat
for site in ecommerce_sites:
    site_id = os.path.basename(site)

    # Watcher script'ini başlat
    watcher_cmd = ["/bin/bash", base_watcher_path, site_id]
    watcher_proc = subprocess.Popen(watcher_cmd)
    processes.append(watcher_proc)
    print(f"Watcher başlatıldı: {site_id}")

    # Processor script'ini başlat
    processor_cmd = ["python3", base_processor_path, site_id]
    processor_proc = subprocess.Popen(processor_cmd)
    processes.append(processor_proc)
    print(f"Processor başlatıldı: {site_id}")

# Çıkış sinyali geldiğinde tüm alt işlemleri sonlandır
def terminate_processes(signum, frame):
    for proc in processes:
        proc.terminate()
    print("Tüm işlemler sonlandırıldı.")

# Sinyal yakalayıcıyı ayarla
signal.signal(signal.SIGINT, terminate_processes)
signal.signal(signal.SIGTERM, terminate_processes)

# Tüm alt işlemlerin bitmesini bekle
try:
    for proc in processes:
        proc.wait()
except KeyboardInterrupt:
    terminate_processes(None, None)
