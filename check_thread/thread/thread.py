from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2, logging
from crypto import DoubleShot
from datetime import datetime, timedelta

def guardar_json(ds):
    json = ds.getdic
    try: 
        conn = get_db()
        cur = conn.cursor()

        delete_query = "DELETE FROM CryptoData;"
        cur.execute(delete_query)

        query = "INSERT INTO CryptoData (EncryptionAlgorithm) VALUES (%s)"
        cur.execute(query, (json,))
        conn.commit()
    except (Exception, psycopg2.DatabaseError, KeyError) as e:
        logger.error(f"ERROR json: {e}")
        conn.rollback()

    finally:
        if conn is not None:
            cur.close()
            conn.close()

def json():
    dS = DoubleShot()
    try: 
        conn = get_db()
        cur = conn.cursor()

        query = "SELECT * FROM CryptoData"
        cur.execute(query)
        dic = cur.fetchone()[0]

    except (Exception, psycopg2.DatabaseError, KeyError) as e:
        logger.error(f"ERROR json: {e}")
        conn.rollback()

    finally:
        if conn is not None:
            cur.close()
            conn.close()
    
    dS.storedic(dic)
    return dS

scheduler = BackgroundScheduler()
scheduler.start()

logging.basicConfig(filename="./Logs/log_file.log")

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:  %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("\n---------------------\n\n")


def process_audio():

    try:
        conn = get_db()
        cur = conn.cursor()

        check_query = "SELECT COUNT(*) FROM CryptoData;"
        cur.execute(check_query)
        count = cur.fetchone()[0]

        if count == 0:
            logger.info("Nenhum registro na tabela CryptoData. A função process_audio não será executada.")
            ds = DoubleShot()
            guardar_json(ds)
            return

        data_limite = datetime.now() - timedelta(hours=24)

        # Consulta SQL para obter áudios adicionados há mais de 24 horas
        query = "SELECT AudioID FROM AudioData WHERE UploadTime < %s;"
        cur.execute(query, (data_limite,))
        rows = cur.fetchall()

        logger.info("Verificando os audios...")
        logger.info(f"Audios encontrados: {rows}")

        for row in rows:
            audio_id = row

            logger.info(f"Updating id {audio_id} in table AudioData...")
            update_query = "UPDATE AudioData SET AudioContent = NULL WHERE AudioID = %s;"
            cur.execute(update_query, (audio_id))
            conn.commit()
        
    except (Exception, psycopg2.DatabaseError, KeyError) as e:
        logger.error(f"ERROR: {e}")
        conn.rollback()

    finally:
        if conn is not None:
            cur.close()
            conn.close()
    
    logger.info("Todos os audios apagados! Verificação finalizada.\n")

    logger.info("Inicialização da atualização do dicionario do algortimo...")
    new_encryption()

    logger.info("Done... Até daqui 24 horas!\n")


def new_encryption():
    dS = json()
    doubleShot = DoubleShot()
    try: 
        conn = get_db()
        cur = conn.cursor()

        query = "SELECT * FROM TextData"
        cur.execute(query)
        rows = cur.fetchall()

        for row in rows:
            text_id, text_content = row
            if isinstance(text_content, memoryview):
                text_content = bytes(text_content)
            text_content.decode("utf-8")
            text_content = dS.processAndDecrypt(text_content)

            new_text = doubleShot.processAndEncrypt(text_content)
            encrypted_text_bytes = new_text.encode('utf-8')

            query = "UPDATE TextData SET TextContent = %s WHERE TextID = %s"
            values = (encrypted_text_bytes, text_id)
            cur.execute(query, values)
            conn.commit()
            logger.info(f"TextID {text_id} Updated!")
        
    except (Exception, psycopg2.DatabaseError, KeyError) as e:
        logger.error(f"ERROR: {e}")
        conn.rollback()

    finally:
        if conn is not None:
            cur.close()
            conn.close()
    
    guardar_json(doubleShot)
    logger.info("Novo dicionario guardado!")


scheduler.add_job(process_audio, trigger='interval', hours=24)

def get_db():
    db = psycopg2.connect(user = "cry_cry",
                password = "cry_pass",
                host = "db",
                port = "5432",
                database = "cry_assignment")
    return db
