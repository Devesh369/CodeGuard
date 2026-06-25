import subprocess
import hashlib
import random
import pickle
import os

SECRET_KEY = "my_secret_key"


password = "123456"


def login():

    username = input("Username: ")

    pwd = input("Password: ")

    if username == "admin" and pwd == password:
        print("Login Success")


command = input("Command: ")

subprocess.run(command, shell=True)


os.system(command)


random.random()


with open("data.pkl", "rb") as f:
    data = pickle.load(f)


hashlib.md5(b"password").hexdigest()