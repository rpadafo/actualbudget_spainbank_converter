import os
import re
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Bank module >>
import bankinter 
import sabadell
import caixa
import santander
import traderepublic
import sumup

IN_FOLDER = "/input"
OUT_FOLDER = "/output"
RETENTION_HOUR = int(os.environ.get("RETENTION_HOUR", 12))

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

ERROR_RED = "\033[1;31m"
RESET_COLOR = "\033[0m"

def clean_old_csv():
    # Delete all files in OUT_FOLDER when RETENTION_HOUR is over
    now = time.time()
    # Hours to seconds (RETENTION_HOUR * 60 * 60 = x seconds)
    limit_seconds = RETENTION_HOUR * 3600
    
    logger.info(f"🧹 Running automatic cleanup of files older than {RETENTION_HOUR} hours")
    
    try:
        for file_name in os.listdir(OUT_FOLDER):
            full_path_file = os.path.join(OUT_FOLDER, file_name)
            
            if os.path.isfile(full_path_file) and file_name.endswith('.csv'):
                modification_date = os.path.getmtime(full_path_file)
                if (now - modification_date) > limit_seconds:
                    os.remove(full_path_file)
                    logger.info(f"🗑️ Deleted {file_name} file")
    except Exception as e:
        logger.info(f"{ERROR_RED}⚠️ Error while deleting files: {e}{RESET_COLOR}")

class FilesMonitor(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or os.path.basename(event.src_path).startswith("~$"):
            return

        # Cleaning
        clean_old_csv()
            
        file_name = os.path.basename(event.src_path)
        file_name_lower = file_name.lower()

        if file_name_lower.endswith(('.xlsx', '.xls', '.txt', '.csv', '.pdf')):
            logger.info(f"⚡ Find: {file_name}")
            time.sleep(2) # Wait for complete copy
            
            try:
                # 1. SUMUP
                if file_name_lower.startswith("sumup") and file_name_lower.endswith(".pdf"):
                    logger.info("-> Using [SumUp] module")
                    sumup.process(event.src_path, OUT_FOLDER, file_name)

                # 2. TRADE REPUBLIC
                elif file_name_lower == "exportación de transacción.csv":
                    logger.info("-> Using [Trade Republic] module")
                    traderepublic.process(event.src_path, OUT_FOLDER, file_name)

                # 3. SANTANDER (Files starts with transactions)
                elif file_name_lower.startswith("transactions"):
                    logger.info("-> Using [Santander] module")
                    santander.process(event.src_path,OUT_FOLDER,file_name)

                # 4. LA CAIXA
                elif file_name_lower.startswith("movimientos_cuenta"):
                    logger.info("-> Using [Caixa] module")
                    caixa.process(event.src_path,OUT_FOLDER,file_name)

                # 5. BANKINTER
                elif file_name_lower.startswith("movimientos"):
                    logger.info("-> Using [Bankinter] module")
                    bankinter.process(event.src_path,OUT_FOLDER,file_name)

                # 6. CASO SABADELL
                elif file_name_lower.endswith('.txt') or re.match(r'^[\d_]+\.[a-zA-Z0-9]+$', file_name_lower):
                    logger.info("-> Using [Sabadell] module")
                    sabadell.process(event.src_path, OUT_FOLDER, file_name)
                
                else:
                    logger.info(f"{ERROR_RED}❌ This file is not asociated to any bank: {file_name}{RESET_COLOR}")
                    return

                # Delete the original file from /input
                os.remove(event.src_path)

            except Exception as e:
                logger.info(f"{ERROR_RED}💥 Error processing {file_name}: {e}{RESET_COLOR}")

if __name__ == "__main__":
    os.makedirs(IN_FOLDER, exist_ok=True)
    os.makedirs(OUT_FOLDER, exist_ok=True)
    
    observer = Observer()
    observer.schedule(FilesMonitor(), path=IN_FOLDER, recursive=False)
    observer.start()
    logger.info("Starting the app")
    logger.info(f"🤖 Watching {IN_FOLDER} (Excel/TXT), exporting to {OUT_FOLDER}...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()