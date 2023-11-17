import os
import subprocess
import argparse
import time
import threading
import json

def print_colored(message, color):
    """ Belirtilen renkte mesaj yazdır. """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "end": "\033[0m",
    }
    print(f"{colors.get(color, colors['end'])}{message}{colors['end']}")

def process_images(source_dir, target_sizes, user_group, specific_files=None, file_path=None):
    """
    Resize, crop, and optimize images using ImageMagick and jpegoptim.
    If file_path is provided, only process that file. Otherwise, process specific_files or all files in the directory.
    """
    if file_path:
        process_single_image(file_path, source_dir, target_sizes, user_group)
        return

    if specific_files:
        for filename in specific_files:
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif','.webp')):
                continue
            file_path = os.path.join(source_dir, filename)
            process_single_image(file_path, source_dir, target_sizes, user_group)
    else:
        for filename in os.listdir(source_dir):
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif','.webp')):
                continue
            file_path = os.path.join(source_dir, filename)
            process_single_image(file_path, source_dir, target_sizes, user_group)

def process_single_image(file_path, source_dir, target_sizes, user_group):
    """
    Process a single image file.
    """
    filename = os.path.basename(file_path)
    file_mod_time = os.path.getmtime(file_path)
    process_required = False

    for width, height in target_sizes:
        start_time = time.time()
        target_dir = os.path.join(source_dir, f"{width}-{height}")

        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            print_colored(f"Klasör oluşturuldu: {target_dir}", "blue")

        output_path = os.path.join(target_dir, os.path.splitext(filename)[0] + '.webp')

        if not os.path.exists(output_path):
            process_required = True
        else:
            output_mod_time = os.path.getmtime(output_path)
            if output_mod_time < file_mod_time:
                process_required = True

        if not process_required:
            print_colored(f"İşlem gereksiz: {output_path}", "yellow")
            continue

        # Resim boyutlandırma ve kırpma için ImageMagick kullanımı
        result = subprocess.run([
            'convert', file_path,
            '-resize', f'{width}x{height}^',
            '-gravity', 'center',
            '-extent', f'{width}x{height}',
            output_path
        ])

        if result.returncode == 0:
            print_colored(f"ImageMagick işlemi başarılı: {output_path}", "green")
        else:
            print_colored(f"ImageMagick işlemi başarısız: {output_path}", "red")

        # jpegoptim kullanarak optimize etme
        result = subprocess.run(['cwebp', '-q', '80', output_path, '-o', output_path])

        if result.returncode == 0:
            print_colored(f"Google cwebp işlemi başarılı: {output_path}", "green")
        else:
            print_colored(f"Google cwebp işlemi başarısız: {output_path}", "red")

        subprocess.run(['chown', user_group, target_dir])
        subprocess.run(['chown', user_group, output_path])

        elapsed_time = time.time() - start_time
        print_colored(f"İşlem {elapsed_time:.2f} saniyede tamamlandı", "yellow")

def parse_dimensions(dimensions_str):
    """Verilen boyut string'ini çözümle ve tuple listesi olarak dönüştür."""
    parsed_dimensions = []
    for dim in dimensions_str.split():
        try:
            width, height = map(int, dim.split('-'))
            parsed_dimensions.append((width, height))
        except ValueError:
            raise argparse.ArgumentTypeError(f"Geçersiz boyut formatı: '{dim}'")
    return parsed_dimensions

def find_site_directory(base_dirs, site_folder):
    """
    Verilen ana dizinler içinde bir site klasörünün dizinini bulun.

    :param base_dirs: Aranacak ana dizinlerin listesi.
    :param site_folder: Bulunacak site klasörünün adı.
    :return: Site klasörünün yolunu döndürün veya bulunamazsa None döndürün.
    """
    for base_dir in base_dirs:
        potential_site_path = os.path.join(base_dir, site_folder)
        if os.path.isdir(potential_site_path):
            return potential_site_path
    return None

def load_sizes_from_json(json_path):
    """ JSON dosyasından boyutları yükle ve döndür. """
    with open(json_path, 'r') as file:
        data = json.load(file)
        return data.get('sizes', [])


# Argümanları tanımla ve ayrıştır
parser = argparse.ArgumentParser(description='Resim optimizasyonu')
parser.add_argument('--site', type=str, required=True, help='Site kullanıcı adı')
parser.add_argument('--image_dir', type=str, default='public_html/images/urunler', help='Resimlerin bulunduğu dizin')
parser.add_argument('--base_dirs', type=str, required=True, nargs='+', help='Aranacak dizinler')
parser.add_argument('--sizes', type=parse_dimensions, help='Boyutlar (örn: 400-600 600-900)')
parser.add_argument('--specific_files', type=str, nargs='+', help='Özel işlenecek dosyaların listesi')
parser.add_argument('--file_path', type=str, help='Özel bir dosyanın yolu')
parser.add_argument('--threads', type=int, default=1, help='Thread sayısını belirtir (varsayılan: 1)')


args = parser.parse_args()

base_directories = args.base_dirs
site_folder_name = args.site
site_path = find_site_directory(base_directories, site_folder_name)
source_directory = os.path.join(site_path, args.image_dir)

if args.sizes is None:
    json_path = os.path.join(site_path, 'watcher/image/product/config.json')
    if os.path.exists(json_path):
        args.sizes = load_sizes_from_json(json_path)
        args.sizes = parse_dimensions(' '.join(args.sizes))
    else:
        print_colored("Boyutlar JSON dosyası bulunamadı. Lütfen --sizes argümanını kullanın.", "red")
        exit(1)

target_sizes = args.sizes

thread_count = args.threads

if thread_count > 1:
    print_colored(f"Started with: {thread_count} threads", "red")
    time.sleep(3)
    # Bir dosya grubunu işleyecek fonksiyon
    def process_image_subset(images_subset):
        for image in images_subset:
            process_images(source_directory, target_sizes, site_folder_name + ":" + site_folder_name, specific_files=[image])

    # Dosya listesini thread sayısına göre böl
    image_list = [file for file in os.listdir(source_directory) if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
    sublists = [image_list[i::thread_count] for i in range(thread_count)]

    # Thread'leri oluştur ve başlat
    threads = []
    for sublist in sublists:
        thread = threading.Thread(target=process_image_subset, args=(sublist,))
        threads.append(thread)
        thread.start()

    # Tüm thread'lerin tamamlanmasını bekle
    for thread in threads:
        thread.join()

    exit(1)

# script --file_path argumentı varsa, sadece belirtilen dosyayı işle
if args.file_path:
    process_images(source_directory, target_sizes, site_folder_name + ":" + site_folder_name, file_path=args.file_path)
elif args.specific_files:
    # script --specific_files argumentı varsa, bu dosyaları işle
    process_images(source_directory, target_sizes, site_folder_name + ":" + site_folder_name, specific_files=args.specific_files)
else:
    # Ne --file_path ne de --specific_files verilmediyse, tüm dosyaları işle
    process_images(source_directory, target_sizes, site_folder_name + ":" + site_folder_name)



