# src/core/db_connector.py
import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="localhost", user="root", password="...", database="Tubes3Stima"
    )
