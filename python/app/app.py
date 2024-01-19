from flask import Flask, render_template, request, jsonify,send_file
import logging, psycopg2
from datetime import datetime, timedelta
from crypto import DoubleShot
from whisper_audio import WhisperProcessor
import base64 
import os
import time


def json():
    doubleShot = DoubleShot()
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
    
    doubleShot.storedic(dic)
    return doubleShot

doubleShot = json()

app = Flask(__name__)
app.static_folder = './static'

audios_directory = os.path.abspath('Audios')

@app.route("/")
def home():
    return render_template("home.html")
@app.route("/admin")
def admin():
    try:
        conn = get_db()
        cur = conn.cursor()

        query = """
            SELECT ata.AudioID, ata.UploadTime, td.TextContent
            FROM AudioTextAssociation ata
            JOIN AudioData ad ON ata.AudioID = ad.AudioID
            JOIN TextData td ON ata.TextID = td.TextID;
        """

        cur.execute(query)
        audio_text_data = cur.fetchall()
        processed_data = []
        for row in audio_text_data:
            audio_id, upload_time, text_content = row
            if isinstance(text_content, memoryview):
                text_content = bytes(text_content)
            text_content = text_content.decode("utf-8")
            logger.info(text_content)
            text_content = doubleShot.processAndDecrypt(text_content)
            logger.info(text_content)

            processed_data.append((audio_id, upload_time, text_content))

        logger.info(processed_data)

        return render_template("admin.html", audio_text_data=processed_data)

    except Exception as e:
        logger.error(f"Error fetching data for admin page: {e}")
        return "Error fetching data for admin page"

    finally:
        if conn is not None:
            cur.close()
            conn.close()

@app.route("/details", methods=["GET", "POST"])
def details():
    audio_id = request.args.get("audio_id")

    try:
        conn = get_db()
        cur = conn.cursor()

        if request.method == "GET":
            query = """
                SELECT AudioData.AudioID, AudioData.UploadTime, TextData.TextContent
                FROM AudioData
                JOIN AudioTextAssociation ON AudioData.AudioID = AudioTextAssociation.AudioID
                JOIN TextData ON AudioTextAssociation.TextID = TextData.TextID
                WHERE AudioData.AudioID = %s;
            """
            cur.execute(query, (audio_id,))
            audio_data = cur.fetchone()
            logger.info(audio_data)

            text_content = audio_data[2].tobytes().decode("utf-8") if audio_data[2] else ""

            return render_template("retify.html", audio_data={"AudioID": audio_data[0], "UploadTime": audio_data[1], "TextContent": text_content})

        elif request.method == "POST":
            new_text_content = request.form.get("new_text_content")
            new_text_content =new_text_content.encode('utf-8')
            text_id_query = "SELECT TextID FROM AudioTextAssociation WHERE AudioID = %s;"
            cur.execute(text_id_query, (audio_id,))
            text_id = cur.fetchone()[0]

            update_query = "UPDATE TextData SET TextContent = %s WHERE TextID = %s;"
            cur.execute(update_query, (new_text_content, text_id))
            conn.commit()

            return render_template("admin.html")

    except Exception as e:
        logger.error(f"Error handling details for audio ID {audio_id}: {e}")
        return "Error handling details"

    finally:
        if conn is not None:
            cur.close()
            conn.close()

#------------
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
        process_audio(audio_content, audio_id)  
    
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
        return render_template("home.html")

@app.route('/get_audio/<int:audio_id>')
def get_audio(audio_id):
    try:
        conn = get_db()
        cur = conn.cursor()

        query = "SELECT AudioContent FROM AudioData WHERE AudioID = %s;"
        cur.execute(query, (audio_id,))
        audio_content = cur.fetchone()[0]

        return send_file(io.BytesIO(audio_content), mimetype='audio/ogg', as_attachment=True, download_name=f'audio_{audio_id}.ogg')

    except Exception as e:
        logger.error(f"Error fetching audio data: {e}")
        return "Error fetching audio data"

    finally:
        if conn is not None:
            cur.close()
            conn.close()

def process_audio(audio_content, audio_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        
        whisper = WhisperProcessor()
        
        audio_path = criar_arquivo_audio(audio_content, audio_id)

        # áudio para texto
        text_content, language = whisper.audio_to_text(audio_path)
        logger.info(f"\nAudio ID: {audio_id}")
        logger.info(f"Language: {language}")
        logger.info(f"Text from whisper: {text_content}\n")

        excluir_arquivo_audio(audio_path)

        # algoritmo de encriptação
        encrypted_text = doubleShot.processAndEncrypt(text_content)

        # Ver nos logs o texto decifrado
        logger.info(f'Encrypted Text: {encrypted_text}')

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
    

    except Exception as e:
        print(f"Error processing audio: {e}")

    finally:
        if conn is not None:
            cur.close()
            conn.close()

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