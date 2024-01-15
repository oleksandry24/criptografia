from flask import Flask, render_template, request
import logging, psycopg2
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from crypto import DoubleShot
from whisper_audio import WhisperProcessor

app = Flask(__name__)
scheduler = BackgroundScheduler()
whisper = WhisperProcessor()
scheduler.start()
app.static_folder = './static'

@app.route("/")
def home():
    return render_template("home.html")


@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    print(request.files)  # Imprime as chaves disponíveis
    
    try:
        audio_blob = request.files['audio'].read()
        with open('audio_received.ogg', 'wb') as f:
            f.write(audio_blob)
        return 'Áudio recebido com sucesso!'
    except KeyError:
        return 'Erro: Chave "audio" não encontrada nos dados da requisição.'



# @app.route("/upload", methods = ["POST"])
# def upload():
#     error = ""
#     try: 
#         conn = get_db()
#         cur = conn.cursor()

#         audio_data = request.json['audio']
#         audio_content = base64.b64decode(audio_data)

#         query = "INSERT INTO AudioData (AudioContent, UploadTime) VALUES (%s, %s)"
#         values = (audio_content, datetime.utcnow())
#         cur.execute(query, values)
        
#         conn.commit()

#         output_message = "Your report has been successfully registered and will be transmitted to the authorities"
        
#     except (Exception, psycopg2.DatabaseError) as e:
#         logger.error(f"SOME PROBLEMS ON CONNECT TO DATABASE: {e}")
#         error = str(e)
#         conn.rollback()

#     finally:
#         if conn is not None:
#             cur.close()
#             conn.close()

#     if error == "":
#         return render_template("home.html", output_message= output_message)
#     else: 
#         return render_template("home.html", error = error)


def process_audio():
    try:
        connection = get_db()
        cursor = connection.cursor()

        query = "SELECT AudioID, AudioContent FROM AudioData WHERE UploadTime <= %s;"
        cursor.execute(query, (datetime.now() - timedelta(hours=48),))
        rows = cursor.fetchall()

        for row in rows:
            audio_id, audio_content = row

            # áudio para texto
            text_content, language = whisper(audio_content)
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
            text_query = "INSERT INTO TextData (TextContent) VALUES (%s) RETURNING text_id;"
            cursor.execute(text_query, (encrypted_text))
            text_id = cursor.fetchone()[0]

            association_query = "INSERT INTO AudioTextAssociation (AudioID, TextID, UploadTime, ConversionTime) VALUES (%s, %s);"
            cursor.execute(association_query, (audio_id, text_id, datetime.now() - timedelta(hours=48), datetime.now()))

        update_query = "UPDATE AudioData SET AudioContent = NULL WHEREUploadTime <= %s;"
        cursor.execute(update_query, (datetime.now() - timedelta(hours=48),))

        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"Error processing audio: {e}")

# Agendando a tarefa para ser executada a cada 24 horas
# scheduler.add_job(process_audio, trigger='interval', hours=24)


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

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:  %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    logger.info("\n---------------------\n\n")

    app.run(host="0.0.0.0", debug=True, threaded=True)

