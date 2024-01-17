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
        