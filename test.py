import subprocess
import os
import pickle

password = "admin123"     # Hardcoded password


def add(a,b):
    c = a+b
    return c


unused_variable = 100


subprocess.call(
    "ls -la",
    shell=True
)


user_input = input("Enter filename: ")

os.system(
    "cat " + user_input
)


data = input("Enter pickle file: ")

with open(data, "rb") as f:
    obj = pickle.load(f)


print(add(10,20))