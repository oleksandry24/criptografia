#!/usr/bin/python
# -*- encoding: utf-8 -*-

import random
import string
from AES import aesEncrypt, aesDecrypt
import secrets
import os
import json
from datetime import datetime
import time


class DoubleShot:
    def __init__(self):
        # Crie o dicionário de substituição no construtor da classe
        self.encryption_dict = self.generate_encryption_dict()
        self.msgencrypt= []
        self.cipher_key= self.encryption_dict["%"]

    def getdic(self):
        return self.encryption_dict
    
    def storedic(self,Originaldict):
        self.encryption_dict=Originaldict
        self.cipher_key=self.encryption_dict["%"]
        return True

    def generate_encryption_dict(self):
        alphabet = list(string.ascii_uppercase)
        shuffled_alphabet = list(alphabet)
        random.shuffle(shuffled_alphabet)
        encryption_dict = {original: replacement for original, replacement in zip(alphabet, shuffled_alphabet)}
        encryption_dict["%"] = str(secrets.token_bytes(16))
        return encryption_dict
   
    def enigmaCry(self, text):
        encryption_dict = self.encryption_dict
        encrypted_text = ""
        for char in text.upper():
            if char in encryption_dict:
                encrypted_text += encryption_dict[char]
            else:
                encrypted_text += char          
        return encrypted_text
    
    def enigmaDecry(self, input):
        encryption_dict = self.encryption_dict
        input = input.upper()
        encrypted_text = ""
        for char in input:
            if char in encryption_dict.values():
                for key, value in encryption_dict.items():
                    if value == char:
                        encrypted_text += key
                        break
            else:
                encrypted_text += char
        return encrypted_text
    
    # Função para multiplicar cada caracter pelo valor multiplicador
    def multiplyChar(self,text):
        new_text = text.split() 
        multiplier = len(new_text[0]) + random.randint(1,10)
        multiplied_text = ""
        for char in text:
            multiplied_char = chr(ord(char) * multiplier)
            multiplied_text += multiplied_char

        self.encryption_dict["#"] = multiplier
        return multiplied_text

    # Função para desfazer a multiplicação
    def divideChar(self, text):
        divisor = self.encryption_dict["#"]
        divided_text = ""
        for char in text:
            divided_char = chr(ord(char) // divisor)
            divided_text += divided_char
        return divided_text
    
    # Função que incorpora todas as etapas de transformação e o AES
    def processAndEncrypt(self, plain_text):
        # Aplicar a transformação enigmaCry
        transformed_text = self.enigmaCry(plain_text)
        
        # Multiplicar cada caractere pelo valor multiplicador
        #multiplied_text = self.multiplyChar(transformed_text)
        
        # Aplicar a criptografia AES
        cipher_text = aesEncrypt(transformed_text, self.cipher_key)

        multiplied_text = self.multiplyChar(cipher_text)

        self.msgencrypt.append(multiplied_text)
        
        return multiplied_text

    # Função que incorpora todas as etapas de transformação e a descriptografia AES
    def processAndDecrypt(self,cipher_text):

        # Desfazer a multiplicação
        divided_text = self.divideChar(cipher_text)

        # Descriptografar com AES
        decrypted_text = aesDecrypt(divided_text, self.cipher_key)
       
        # Desfazer a transformação enigmaCry
        original_text = self.enigmaDecry(decrypted_text)
        
        
        return original_text
    
    def storemsg(self, folder_path='LogsMsg'):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        timestamp = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        timestamped_file_name = f"{timestamp}_MSGEncrypted.json"
        file_path = os.path.join(folder_path, timestamped_file_name)
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(cm.msgencrypt, file)
        

    def showmsg(self,folder_path ='./LogsMsg'):
        files = [filename for filename in os.listdir(folder_path) if filename.endswith('.json')]
        if not files:
            print("No JSON files found in the folder.")
            return None
        print("Available files in the folder:")
        for i, file in enumerate(files, start=1):
            print(f"{i}. {file}")

        while True:
            try:
                choice = int(input("Enter the number of the file you want to retrieve (0 to cancel): "))
                if choice == 0:
                    return None
                elif 1 <= choice <= len(files):
                    selected_file = files[choice - 1]
                    file_path = os.path.join(folder_path, selected_file)
                    with open(file_path, 'r') as file:
                        return json.load(file)
                else:
                    print("Invalid choice. Please enter a valid number.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")



def encdec(machine, plain_text):
    print("No encry",plain_text)
    cipher_text = machine.processAndEncrypt(plain_text)
    print("The encrypted text is : {}".format(cipher_text))
    decrypted_text = machine.processAndDecrypt(cipher_text)
    print("The decrypted text is : {}".format(decrypted_text))
    print("----------------------------------")

def savedict(dictionary, file_name,folder_path ='LogsFolder'):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    timestamp = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
    timestamped_file_name = f"{timestamp}_{file_name}.json"

    file_path = os.path.join(folder_path, timestamped_file_name)

    with open(file_path, 'w') as file:
        json.dump(dictionary, file)


def listfiles(folder_path='./LogsFolder'):
    files = [filename for filename in os.listdir(folder_path) if filename.endswith('.json')]
    return files


def retrievedict(folder_path ='./LogsFolder'):
    files = listfiles(folder_path)

    if not files:
        print("No JSON files found in the folder.")
        return None

    print("Available files in the folder:")
    for i, file in enumerate(files, start=1):
        print(f"{i}. {file}")

    while True:
        try:
            choice = int(input("Enter the number of the file you want to retrieve (0 to cancel): "))
            if choice == 0:
                return None
            elif 1 <= choice <= len(files):
                selected_file = files[choice - 1]
                file_path = os.path.join(folder_path, selected_file)
                with open(file_path, 'r') as file:
                    return json.load(file)
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")




if __name__ == "__main__":
    cm = DoubleShot()
    
    run = True
    

    while(run):
        
        plaintext =  input("""
        Enter one of the following options:
        - Type 'Exit' to exit the program.
        - Type 'Retrieve Dic' to retrieve an old dictionary to decrypt older messages.
        - Type 'Retrieve Msg' to retrieve older messages.
        - Type 'Decrypt' to decrypt a message.
        - Type 'Encrypt' to encrypt a message.
        - Type 'EncryptAndDecrypt' to encrypt and decrypt a message.

        Your choice: """)
        if(plaintext=="Exit"):
            run= False
            break
        elif(plaintext=="Retrieve Dic"):
            retrieved_dict = retrievedict()
            if retrieved_dict is not None:
                print("Retrieved dictionary:")
                if(cm.storedic(retrieved_dict)):
                    print("Sucess adding the dictionary")
        elif(plaintext=="Retrieve Msg"):
            msgs = cm.showmsg()
            if msgs is not None:
                print("Retrieved msgs:")
                if(msgs):
                    print("Sucess retriving MSGS")
                for index, item in enumerate(msgs):
                    print(f"{index + 1}. {item}")
        elif(plaintext=="Decrypt"):
            msg =  input("Insert message:")
            decrypted_text = cm.processAndDecrypt(msg)
            print("The decrypted text is : {}".format(decrypted_text))
        elif(plaintext=="Encrypt"):
            msg =  input("Insert message:")
            decrypted_text= cm.processAndEncrypt(msg)
            print("The Encrypted text is : {}".format(decrypted_text))
        elif(plaintext=="EncryptAndDecrypt"):
            msg =  input("Insert message:")
            encdec(cm, msg)  
        else:
            print("Command Not Recognized")
        time.sleep(2)


    savedict(cm.getdic(), "Encryption")
    cm.storemsg()