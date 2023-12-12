import threading
import redis
import os
import sys
import subprocess
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor

# Log dosyası konfigürasyonu
log_file = 'logfile.log'  # Log dosyasının yolu
logging.basicConfig(filename=log_file, level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')


def read_config(site_directory):
    config_path = os.path.join(site_directory, "watcher/image/product/config.json")
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            sizes = ' '.join(config['sizes'])
            image_dir = config['image_dir']
            max_workers = config.get('max_workers', 10)  # Varsayılan değer 10
            return sizes, max_workers, image_dir
    except Exception as e:
        print(f"Config dosyası okunurken hata oluştu: {e}")
        logging.error(f"Config dosyası okunurken hata oluştu: {e}")

        return None, None



if len(sys.argv) < 2:
    print("Kullanım: python process_events.py siteid")
    sys.exit(1)

siteid = sys.argv[1]
base_dirs = ["/home", "/home1", "/home2"]

# İlgili site dizinini bul
site_directory = None
for base_dir in base_dirs:
    potential_dir = os.path.join(base_dir, siteid)
    if os.path.isdir(potential_dir):
        site_directory = potential_dir
        break

if not site_directory:
    print(f"Site dizini '{siteid}' bulunamadı.")
    sys.exit(1)

# config.json dosyasından boyutları oku
config_path = os.path.join(site_directory, "watcher/image/product/config.json")
try:
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        sizes = ' '.join(config['sizes'])
except Exception as e:
    print(f"Config dosyası okunurken hata oluştu: {e}")
    sys.exit(1)


# İlk config okuması
sizes, max_workers, image_dir = read_config(site_directory)
if sizes is None or max_workers is None:
    sys.exit(1)



# Redis bağlantı ayarları
REDIS_QUEUE_KEY = f"{sys.argv[1]}_file_events"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Redis bağlantısını oluştur
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

# İş parçacığı fonksiyonu
def process_event(event):
    try:
        if event:
            event_data = event[1].decode('utf-8').split(' ')
            image_path = event_data[0]
            event_type = event_data[1]
            if event_type=="DELETE" or event_type=="DELETE,ISDIR"  or event_type=="CREATE,ISDIR":
                print("Delete atlandı:", image_path)
                return True


            print(f"İşleniyor: {image_path}, Event Type: {event_type}")


            # Burada gerekli işlem kodunuzu yerleştirin
            # Örneğin, optimize.py scriptini çalıştırmak için:
            optimize_command = [
                "python3",
                "/etc/WebP-Watch-N-Process/image-optimizer/optimize.py",
                "--site", sys.argv[1],
                "--image_dir", config['image_dir'],
                "--base_dirs", "/home", "/home1", "/home2",
                "--sizes", sizes,
                "--file_path", image_path
            ]
            try:
                subprocess.run(optimize_command, check=True)
            except Exception as err:
                print("Error:",err)
                #time.sleep(60)
    except Exception as err:
        print(f"Event işlenirken hata oluştu: {err}")
        logging.error(f"Event işlenirken hata oluştu: {err}")


# Config yenileme fonksiyonu
def refresh_config():
    global sizes, max_workers
    while True:
        time.sleep(300)  # Her 5 dakikada bir config'i yenile
        new_sizes, new_max_workers,new_image_dir = read_config(site_directory)
        if new_sizes is not None and new_max_workers is not None:
            sizes = new_sizes
            max_workers = new_max_workers
            image_dir = new_image_dir
            print(f"Config güncellendi: Sizes={sizes}, Max Workers={max_workers} , Max Workers={image_dir}")

try:
    # Config yenileme iş parçacığını başlat
    config_thread = threading.Thread(target=refresh_config, daemon=True)
    config_thread.start()
except Exception as e:
    logging.error(f"Config yenileme iş parçacığını başlatırken hata oluştu: {e}")

executor = ThreadPoolExecutor(max_workers=max_workers)
while True:
    try:
        event = redis_client.brpop(REDIS_QUEUE_KEY)
        if event:
            executor.submit(process_event, event)
        time.sleep(0.1)
    except Exception as e:
         time.sleep(0.5)
         logging.error(f"Redis'ten event okunurken hata oluştu: {e}")
