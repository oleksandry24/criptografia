from flask import Flask, render_template, request, jsonify
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

        cur.execute("SELECT * FROM AudioData")
        audios = cur.fetchall()

        processed = []
        for audio in audios:
            audio_id = audio[0]
            audio_blob = audio[1]
            upload_time = audio[2]

            audio_path = criar_arquivo_audio(audio_blob, audio_id)

            processed.append({
                'ID': audio_id,
                'AudioPath': audio_path,
                'UploadTime': upload_time
            })

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        processed = []

    finally:
        if conn is not None:
            cur.close()
            conn.close()

    return render_template("admin.html", audios = processed)

@app.route('/transform_audio')
def transform_audio():
    try:
        audio_id = request.args.get('audioID')

        whisper = WhisperProcessor()
        
        audio_path = os.path.join(audios_directory, f'audio_{audio_id}.ogg')

        # áudio para texto
        text_content, language = whisper.audio_to_text(audio_path)
        logger.info(f"\nAudio ID: {audio_id}")
        logger.info(f"Language: {language}")
        logger.info(f"Text from whisper: {text_content}\n")

    
    except Exception as e:
        print(f"Error processing audio: {e}")

    return jsonify({'text': text_content})

@app.route('/confirm_text')
def confirm():
    try:
        data = request.json
        
        audio_id = data.get('audioID')
        text_content = data.get('text')

        inserir_bd(audio_id, text_content)

        return jsonify({'success': True})           
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def inserir_bd(audio_id, text):
    try: 
        conn = get_db()
        cur = conn.cursor()

        doubleShot = DoubleShot()
        encrypted_text = doubleShot.processAndEncrypt(text)

        # Ver nos logs o texto decifrado
        logger.info(f'Encrypted Text: {encrypted_text}')
        decrypted_text = doubleShot.processAndDecrypt(encrypted_text)
        logger.info(f'Decrypted Text: {decrypted_text}\n')

        # inserir o resultado
        logger.info("Try Insert into TextData..")
        encrypted_text_bytes = encrypted_text.encode('utf-8')
        text_query = "INSERT INTO TextData (TextContent) VALUES (%s) RETURNING TextID;"
        cur.execute(text_query, (encrypted_text_bytes,))
        text_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"New TextID: {text_id}")

        logger.info("Try Insert into AudioTextAssociation...")
        association_query = "INSERT INTO AudioTextAssociation (AudioID, TextID, UploadTime, ConversionTime) VALUES (%s, %s, %s, %s);"
        cur.execute(association_query, (audio_id, text_id, datetime.now() - timedelta(hours=24), datetime.now()))
        conn.commit()
        logger.info(f"New insert Sucessfull")

        logger.info("Updating table AudioData...")
        update_query = "UPDATE AudioData SET AudioContent = NULL WHERE AudioID = %s;"
        cur.execute(update_query, (audio_id))
        conn.commit()
        logger.info("Update sucessfull!")

    except (Exception, psycopg2.DatabaseError, KeyError) as e:
        logger.error(f"Error DataBase: {e}")
        conn.rollback()

    finally:
        if conn is not None:
            cur.close()
            conn.close()

# @app.route('/detalhes_audio')
# def detalhes_audio():
#     audio_id = request.args.get('audioID')

#     try:
#         conn = get_db()
#         cur = conn.cursor()

#     except 
#     return jsonify()

@app.route("/upload_audio", methods = ["POST"])
def upload():
    error = ""
    try: 
        conn = get_db()
        cur = conn.cursor()

        logger.info("CONNECTION SUCCESSFULL TO DB")

        audio_blob = request.data
        audio_content = audio_blob

        query = "INSERT INTO AudioData (AudioContent, UploadTime) VALUES (%s, %s) RETURNING AudioID"
        values = (audio_content, datetime.utcnow())
        cur.execute(query, values)
        audio_id = cur.fetchone()[0]

        conn.commit()

        logger.info(f"New Insert! Audio ID: {audio_id}")

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


def process_audio():
    try:
        conn = get_db()
        cur = conn.cursor()

        query = "SELECT AudioID, AudioContent FROM AudioData WHERE UploadTime <= %s;"
        cur.execute(query, (datetime.now() - timedelta(hours=24),))
        rows = cur.fetchall()

        for row in rows:

            audio_id, audio_content = row

            if audio_content == None:
                logger.info("Ja foram todos convertidos em texto!!")
                break
            
            whisper = WhisperProcessor()
            
            audio_path = criar_arquivo_audio(audio_content, audio_id)

            # áudio para texto
            text_content, language = whisper.audio_to_text(audio_path)
            logger.info(f"\nAudio ID: {audio_id}")
            logger.info(f"Language: {language}")
            logger.info(f"Text from whisper: {text_content}\n")

            excluir_arquivo_audio(audio_path)
   
            # algoritmo de encriptação
            doubleShot = DoubleShot()
            encrypted_text = doubleShot.processAndEncrypt(text_content)

            # Ver nos logs o texto decifrado
            logger.info(f'Encrypted Text: {encrypted_text}')
            decrypted_text = doubleShot.processAndDecrypt(encrypted_text)
            logger.info(f'Decrypted Text: {decrypted_text}\n')

            # inserir o resultado
            logger.info("Try Insert into TextData..")
            encrypted_text_bytes = encrypted_text.encode('utf-8')
            text_query = "INSERT INTO TextData (TextContent) VALUES (%s) RETURNING TextID;"
            cur.execute(text_query, (encrypted_text_bytes,))
            text_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"New TextID: {text_id}")

            logger.info("Try Insert into AudioTextAssociation...")
            association_query = "INSERT INTO AudioTextAssociation (AudioID, TextID, UploadTime, ConversionTime) VALUES (%s, %s, %s, %s);"
            cur.execute(association_query, (audio_id, text_id, datetime.now() - timedelta(hours=24), datetime.now()))
            conn.commit()
            logger.info(f"New insert Sucessfull")
        
        logger.info("Updating table AudioData...")
        update_query = "UPDATE AudioData SET AudioContent = NULL WHERE UploadTime <= %s;"
        cur.execute(update_query, (datetime.now() - timedelta(hours=24),))
        conn.commit()
        logger.info("Update sucessfull!")

    except Exception as e:
        print(f"Error processing audio: {e}")

    finally:
        if conn is not None:
            cur.close()
            conn.close()

# Agendando a tarefa para ser executada a cada 24 horas
# scheduler.add_job(process_audio, trigger='interval', hours=24)


def criar_arquivo_audio(audio_blob, audio_id):
    audio_path = os.path.join(audios_directory, f'audio_{audio_id}.ogg')
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