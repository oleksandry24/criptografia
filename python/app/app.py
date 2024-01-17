from flask import Flask, render_template, request
import logging, psycopg2
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from crypto import DoubleShot
from whisper_audio import WhisperProcessor
import base64 
import os
import time

app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()
app.static_folder = './static'

audios_directory = os.path.abspath('Audios')

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/admin")
def admin():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM AudioTextAssociation")
        audio_text_associations = cur.fetchall()

        cur.execute("SELECT * FROM TextData")
        texts = cur.fetchall()

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        audio_text_associations = []
        texts = []

    finally:
        if conn is not None:
            cur.close()
            conn.close()

    return render_template("admin.html", audio_text_associations=audio_text_associations, texts=texts)


@app.route("/rectify_audio/<int:audio_id>/<int:text_id>")
def rectify_audio(audio_id, text_id):


    return render_template("rectify.html", audio_id=audio_id, text_content="text")


@app.route("/verify_audio/<int:audio_id>", methods=["POST"])
def verify_audio(audio_id):
    action = request.form.get("action")

    try:
        conn = get_db()
        cur = conn.cursor()

        if action == "verify":
            cur.execute("UPDATE AudioData SET AudioContent = NULL WHERE AudioID = %s", (audio_id,))
            conn.commit()

    except Exception as e:
        logger.error(f"Error verifying audio: {e}")
        conn.rollback()

    finally:
        if conn is not None:
            cur.close()
            conn.close()

    return render_template("admin.html")


# @app.route('/upload_audio', methods=['POST'])
# def upload_audio():
#     try:
#         audio_blob = request.data
#         with open('Audios/audio_received.ogg', 'wb') as f:
#             f.write(audio_blob)
#         return 'Áudio recebido com sucesso!'
#     except KeyError:
#         return 'Erro: Chave "audio" não encontrada nos dados da requisição.'



@app.route("/upload_audio", methods = ["POST"])
def upload():
    error = ""
    try: 
        conn = get_db()
        cur = conn.cursor()

        logger.info("CONNECTION SUCCESSFULL TO DB")

        audio_blob = request.data
        audio_content = base64.b64decode(audio_blob)

        query = "INSERT INTO AudioData (AudioContent, UploadTime) VALUES (%s, %s) RETURNING AudioID"
        values = (audio_content, datetime.utcnow())
        cur.execute(query, values)
        audio_id = cur.fetchone()[0]

        conn.commit()

        logger.info(f"New Insert. Audio ID: {audio_id}")
        

        ## PROCESS AUDIO

        query = "SELECT AudioID, AudioContent FROM AudioData WHERE UploadTime <= %s;"
        cur.execute(query, (datetime.now() - timedelta(minutes=1),))
        rows = cur.fetchall()

        for row in rows:
            audio_id, audio_content = row

            audio_path = criar_arquivo_audio(audio_content)

            # áudio para texto
            whisper = WhisperProcessor()

            text_content, language = whisper.audio_to_text(audio_path)
            logger.info(f"\nAudio ID: {audio_id}")
            logger.info(f"Language: {language}")
            logger.info(f"Text from whisper: {text_content}\n")

            # Excluir o arquivo de áudio após o processamento
            excluir_arquivo_audio(audio_path)
   
            # algoritmo de encriptação

            doubleShot = DoubleShot()
            encrypted_text = doubleShot.processAndEncrypt(text_content)

            # Ver nos logs o texto decifrado
            logger.info(f'Encrypted Text: {encrypted_text}')
            decrypted_text = doubleShot.processAndDecrypt(encrypted_text)
            logger.info(f'Decrypted Text: {decrypted_text}\n')

            # inserir o resultado
            text_query = "INSERT INTO TextData (TextContent) VALUES (%s) RETURNING TextID;"
            cur.execute(text_query, (encrypted_text))
            text_id = cur.fetchone()[0]

            association_query = "INSERT INTO AudioTextAssociation (AudioID, TextID, UploadTime, ConversionTime) VALUES (%s, %s);"
            cur.execute(association_query, (audio_id, text_id, datetime.now() - timedelta(hours=48), datetime.now()))

        update_query = "UPDATE AudioData SET AudioContent = NULL WHERE UploadTime <= %s;"
        cur.execute(update_query, (datetime.now() - timedelta(hours=48),))


    except (Exception, psycopg2.DatabaseError, KeyError) as e:
        logger.error(f"ERROR: {e}")
        error = str(e)
        conn.rollback()

    finally:
        if conn is not None:
            cur.close()
            conn.close()

    if error == "":
        return render_template("home.html")
    else: 
        return render_template("home.html", error = error)


def process_audio(connection, cursor):
    try:

        query = "SELECT AudioID, AudioContent FROM AudioData WHERE UploadTime <= %s;"
        cursor.execute(query, (datetime.now() - timedelta(hours=48),))
        rows = cursor.fetchall()

        for row in rows:
            audio_id, audio_content = row

            # áudio para texto
            whisper = WhisperProcessor()

            text_content, language = whisper.audio_to_text(audio_content)
            logger.info(f"\nAudio ID: {audio_id}")
            logger.info(f"Language: {language}")
            logger.info(f"Text from whisper: {text_content}\n")
           
            # algoritmo de encriptação

            doubleShot = DoubleShot()
            encrypted_text = doubleShot.processAndEncrypt(text_content)

            # Ver nos logs o texto decifrado
            logger.info(f'Encrypted Text: {encrypted_text}')
            decrypted_text = doubleShot.processAndDecrypt(encrypted_text)
            logger.info(f'Decrypted Text: {decrypted_text}\n')

            # inserir o resultado
            text_query = "INSERT INTO TextData (TextContent) VALUES (%s) RETURNING TextID;"
            cursor.execute(text_query, (encrypted_text))
            text_id = cursor.fetchone()[0]

            association_query = "INSERT INTO AudioTextAssociation (AudioID, TextID, UploadTime, ConversionTime) VALUES (%s, %s);"
            cursor.execute(association_query, (audio_id, text_id, datetime.now() - timedelta(hours=48), datetime.now()))

        update_query = "UPDATE AudioData SET AudioContent = NULL WHERE UploadTime <= %s;"
        cursor.execute(update_query, (datetime.now() - timedelta(hours=48),))

        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"Error processing audio: {e}")

    finally:
        if connection is not None:
            cursor.close()
            connection.close()

# Agendando a tarefa para ser executada a cada 24 horas
# scheduler.add_job(process_audio, trigger='interval', hours=24)


def criar_arquivo_audio(audio_blob):
    timestamp = str(int(time.time()))
    audio_path = os.path.join(audios_directory, f'audio_{timestamp}.mpeg')
    with open(audio_path, 'wb') as f:
        f.write(audio_blob)

    return audio_path

def excluir_arquivo_audio(audio_path):
    os.remove(audio_path)


def get_db():
    db = psycopg2.connect(user = "cry_cry",
                password = "cry_pass",
                host = "db",
                port = "5432",
                database = "cry_assignment")
    return db

##########################################################
## MAIN
##########################################################
if __name__ == "__main__":
    logging.basicConfig(filename="./Logs/log_file.log")

    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:  %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info("\n---------------------\n\n")

    app.run(host="0.0.0.0", debug=True, threaded=True)

