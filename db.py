import mysql.connector

class Database:

    def __init__(self):
        self.connection =  mysql.connector.connect(host = "localhost", user = "root",passwd = "root", database = "face_recognition2", auth_plugin="mysql_native_password")
        print("connection established")


    def query(self, q, arg=()):
        cursor = self.connection.cursor(buffered=True)
        cursor.execute(q, arg)
        results = cursor.fetchall()
        cursor.close()
        return results

    def insert(self, q, arg=()):
        cursor = self.connection.cursor(buffered=True)
        cursor.execute(q, arg)
        self.connection.commit()
        result = cursor.lastrowid
        cursor.close()
        return result

    def select(self, q, arg=()):
        cursor = self.connection.cursor(buffered=True)
        cursor.execute(q, arg)
        results = cursor.fetchall()
        cursor.close()
        return results

    def delete(self, q, arg=()):
        cursor = self.connection.cursor(buffered=True)
        result = cursor.execute(q, arg)
        self.connection.commit()
        return result