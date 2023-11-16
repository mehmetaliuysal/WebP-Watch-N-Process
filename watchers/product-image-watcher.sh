#!/bin/bash

siteid=$1

# Eğer siteid argümanı geçirilmezse script durdurulur.
if [ -z "$siteid" ]; then
    echo "Site ID argümanı eksik."
    exit 1
fi


# Aranacak ana dizinler
directories=("/home" "/home1" "/home2")

# Her bir ana dizinde siteid için klasörü ara
for dir in "${directories[@]}"; do
    if [[ -d "$dir/$siteid" ]]; then
        DIRECTORY="$dir/$siteid/public_html/images/urunler"
        DB_FILE="db/product/${siteid}_events.db"
        break
    fi
done

# Eğer DIRECTORY ve DB_FILE değişkenleri boşsa, site bulunamadı
if [ -z "$DIRECTORY" ] || [ -z "$DB_FILE" ]; then
    echo "Site $siteid bulunamadı."
    exit 1
fi


REDIS_QUEUE_KEY="${siteid}_file_events"
REDIS_HOST="localhost"
REDIS_PORT=6379
#DELAY=2 # Olayları biriktirmek için gecikme süresi (saniye)


# Son işlenen dosya ve zamanı saklamak için değişkenler
last_file=""
last_time=0

# inotifywait komutunu çalıştır ve olayları dinle
#events=$()
inotifywait -m "$DIRECTORY" --format '%w%f %e' -e create -e modify -e delete -e close_write |
while read file event; do
    #current_time=$(date +%s)

    # Eğer son işlenen dosya ile şu anki dosya aynıysa ve belirlenen gecikme süresi içindeyse, bu olayı atla
    #if [[ "$file" == "$last_file" ]] && [[ $((current_time - last_time)) -lt $DELAY ]]; then
        #continue
    #fi

    # Dosya ve olay bilgisini veritabanına kaydet
    #sqlite3 $DB_FILE "BEGIN EXCLUSIVE TRANSACTION" || { echo "Transaction başlatılamadı";}
    if [[ "$event" == "CLOSE_WRITE,CLOSE" ]]; then
        redis-cli -h $REDIS_HOST -p $REDIS_PORT LPUSH $REDIS_QUEUE_KEY "$file $event"
        echo "Dosya $event: $file"
    fi

    #sqlite3 $DB_FILE "COMMIT TRANSACTION"


    #last_file=$file
    #last_time=$current_time
done
