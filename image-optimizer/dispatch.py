import psutil
import subprocess
import sys

def check_if_process_is_running(script_name, site_parameter):
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = ' '.join(process.info['cmdline'])
        if script_name in cmdline and f'--site {site_parameter}' in cmdline:
            return True, process.info['pid']
    return False, None


def run_script(site):
    cmd = f"python3 /etc/WebP-Watch-N-Process/image-optimizer/optimize.py --site {site} --image_dir public_html/images/urunler --base_dirs /home /home1 /home2"
    try:
        subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Script hata ile sonuçlandı: {e.stderr.decode()}")
        return False


def main():
    script_to_check = "/etc/WebP-Watch-N-Process/image-optimizer/optimize.py"
    site_to_check = "modasahrecm"  # Örnek site adı, ihtiyaca göre değiştirilebilir

    is_running, pid = check_if_process_is_running(script_to_check, site_to_check)

    if is_running:
        print(f"Script zaten PID {pid} ile ve '--site {site_to_check}' parametresi ile çalışıyor.")
    else:
        print(f"Script '--site {site_to_check}' parametresi ile çalışmıyor.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        site = sys.argv[1]
    else:
        site = input("Lütfen site adını girin: ")
    run_script(site)
