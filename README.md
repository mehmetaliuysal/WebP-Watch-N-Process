# WebP Watch and Process Service

The WebP Watch and Process Service is an automation tool designed to optimize images for web delivery by converting them to the WebP format using ImageMagick and optimizing them with cwebp. It listens to image directories for changes using `inotifywait` and processes new or updated images accordingly.

## Installation on Debian System

### Prerequisites

Before installing the WebP Watch and Process Service, you need to ensure that the following dependencies are installed on your system:

- ImageMagick
- cwebp
- inotify-tools
- redis server

You can install these dependencies on a Debian-based system using the following commands:

```bash
sudo apt-get update
sudo apt-get install imagemagick webp inotify-tools redis
```
For other Linux distributions or operating systems, please use the corresponding package manager or download the software from the official websites.

### Cloning the Project from GitHub

To install the WebP Watch and Process Service, you first need to clone the repository from GitHub to your local system. Ideally, this should be done in the `/etc` directory.

1. Open a terminal and navigate to the `/etc` directory:

   ```bash
   cd /etc
   ```
   
2. Clone the repository using the following command:
   
   ```bash
   sudo git clone https://github.com/mehmetaliuysal/WebP-Watch-N-Process
   ```
   
4. Navigate to the cloned directory:
   
   ```bash
   cd WebP-Watch-N-Process
   ```

### Site Directory Structure and Configuration

The WebP Watch and Process Service is designed to work with sites that follow a specific directory structure. Each site should have an `index.php` file in its `public_html` directory. The script uses this structure to identify active websites for image processing.

#### Directory Structure

- The service expects to find sites in directories matching the pattern `home*/{site_name}/public_html/index.php`.
- You can modify this path in the `wrapper.py` script (line 16) if your sites follow a different directory structure.

#### Configuration File

Each site must have a configuration file named `config.json` located in `home*/{site_name}/watcher/image/product/`. This file specifies the image processing parameters for each site.

##### Example `config.json`:

```json
{
    "sizes": [
        "100-150",
        "400-600",
        "600-900",
        "1000-1500"
    ],
    "image_dir": "public_html/images/urunler",
    "max_workers": 2
}
```
##### Config Parameters:
* `sizes`: An array of size ranges for the images to be generated.
* `image_dir`: The directory where the source images are located.
* `max_workers`: The number of worker threads the processor will use. Keeping this number low (1 or 2) is beneficial for resource consumption on servers hosting multiple sites.

### Setting Up the Service
To set up the image processing service on a Debian-based system, follow these steps:

1. Copy the service file `image_wrapper.service` to the `/etc/systemd/system/` directory.

  ```bash
  sudo cp image_wrapper.service /etc/systemd/system/
  ```
2. Reload the systemd daemon to recognize the new service.

  ```bash
  sudo systemctl daemon-reload
  ```

3. Start the service.

  ```bash
  sudo systemctl start image_wrapper.service
  ```

4. To ensure the service starts on boot, enable it.

  ```bash
  sudo systemctl start image_wrapper.service
  ```

5. You can check the status of the service using:

  ```bash
  sudo systemctl status image_wrapper.service
  ```


## wrapper.py

The `wrapper.py` script serves as the main controller for the WebP Watch and Process Service. It orchestrates the operation of both the `product-image-watcher.sh` and `product-image-processor.py` scripts for multiple e-commerce sites.

### How it Works

- The script searches through specified directories to find e-commerce sites based on the presence of `index.php` in their `public_html` directories.
- For each identified e-commerce site, it launches two subprocesses:
- The watcher script (`product-image-watcher.sh`) to monitor for image file changes.
- The processor script (`product-image-processor.py`) to process and convert the images to WebP format.
- It maintains a list of these subprocesses and ensures they terminate gracefully when the main script receives a termination signal.

### Configuration

- `directories`: An array of root directories where the script searches for e-commerce sites.
- `base_watcher_path`: The path to the `product-image-watcher.sh` script.
- `base_processor_path`: The path to the `product-image-processor.py` script.

### Usage

Run the script directly from the command line:

```bash
python wrapper.py
```

### Dependencies
* Python 3.x environment.
* Access to `product-image-watcher.sh` and `product-image-processor.py` scripts.
* The script assumes that e-commerce sites are structured in a specific way, with a public_html/index.php file.

Ensure that the specified directories in the script accurately reflect the locations of your e-commerce sites and that both the watcher and processor scripts are correctly located and accessible.

Notes
The script dynamically identifies e-commerce sites and manages multiple instances of watcher and processor scripts.
It's designed to be robust and handle multiple sites concurrently.
Upon receiving a termination signal (SIGINT or SIGTERM), the script will attempt to terminate all subprocesses cleanly.

## product-image-watcher.sh

This shell script is designed to monitor specific directories for changes in image files and then push these changes to a Redis queue for further processing. It uses `inotifywait` to watch for filesystem events like creation, modification, or deletion of files.

### How it Works

- The script takes a `siteid` as an argument, which is used to determine the directories to monitor and the Redis queue key.
- It searches for a directory path that matches the provided `siteid` in the specified root directories.
- If a matching directory is found, it sets up `inotifywait` to monitor this directory for file events.
- When an event occurs (specifically, `CLOSE_WRITE,CLOSE` events), the script pushes the file path and event type to the Redis queue.

### Configuration

- `directories`: An array of root directories to search for the `siteid` specific folder.
- `REDIS_QUEUE_KEY`: A key to identify the Redis queue. It's constructed using the `siteid`.
- `REDIS_HOST` and `REDIS_PORT`: Configuration for connecting to the Redis server.

### Usage

Run the script by passing the `siteid` as an argument:

```bash
./product-image-watcher.sh <site_id>
```

### Dependencies
* `inotify-tools`: For monitoring directory changes.
* `redis-server`: Must be running and accessible for pushing events to the queue.
* `bash` : The script is intended to be run in a bash environment.

Ensure that the Redis server is properly configured and running before executing this script.

## product-image-processor.py

The `product-image-processor.py` script is designed to process image files by taking image paths from a Redis queue, converting them to WebP format, and optimizing them. It works in conjunction with the `product-image-watcher.sh` script.

### How it Works

- The script pulls image file paths from the Redis queue, where they are placed by the `product-image-watcher.sh` script.
- For each image path, it processes the image by converting it to the WebP format.
- Utilizes `optimize.py` for the actual image conversion and optimization.

### Configuration

- `REDIS_QUEUE_KEY`: The Redis queue key from which image paths are read.
- Image directories and sizes are read from a `config.json` file, which should be placed in the site directory.

### Usage

Run the script with the site ID as an argument:

```bash
python product-image-processor.py <site_id>
```
### Dependencies
* `redis-py` : To interact with the Redis queue.
* Python 3.x environment.
* Access to the `optimize.py` script for image processing.

Ensure that the Redis server is properly configured and running, and the optimize.py script is accessible from this script.

### Notes
* The script continuously monitors the Redis queue for new image paths and processes them as they arrive.
* It is capable of handling multiple image files concurrently, depending on the configuration specified in config.json. `{site_directory}/watcher/image/product/config.json`
* The script should be run in an environment where all its dependencies are satisfied.

## optimize.py

The `optimize.py` script is a crucial component of the WebP Watch and Process Service. It is responsible for the actual conversion and optimization of images to the WebP format.

### How it Works

- The script processes images by resizing, cropping, and converting them to the WebP format.
- It utilizes ImageMagick for image manipulation and Google's cwebp for optimization.
- Supports processing individual files or batches of files within a directory.
- Allows specification of different sizes for the output images.

### Usage

Run the script with the required arguments:

```bash
python optimize.py --site <site_id> --image_dir <image_directory> --base_dirs <base_directories> [--sizes <sizes>] [--specific_files <file1 file2 ...>] [--file_path <specific_file_path>] [--threads <number_of_threads>]
```

### Arguments
* `--site`: The site user name, used to identify the site-specific directory.
* `--image_dir`: The directory where the images are located.
* `--base_dirs`: The base directories to search for the site directory.
* `--sizes`: Optional. Specifies the target sizes for the images (e.g., "400-600 600-900").
* `--specific_files`: Optional. A list of specific files to process.
* `--file_path`: Optional. A specific file path to process a single file.
* `--threads`: Optional. The number of threads to use for processing (default is 1).


### Dependencies
* Python 3.x environment.
* `ImageMagick` and `cwebp` installed and accessible in the script's environment.
* Ensure that the script is run in an environment where ImageMagick and cwebp are installed and properly configured.

### Notes
The script can handle multiple image files concurrently if the `--threads` argument is set to a value greater than 1.
It's designed to be flexible and efficient in processing large numbers of images.


