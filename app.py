from flask import Flask, json, Response, request, render_template
from werkzeug.utils import secure_filename
from os import path, getcwd
from db import Database
from face import Face
import time
from datetime import date
import datetime

app = Flask(__name__)

app.config['file_allowed'] = ['image/png', 'image/jpeg']
app.config['storage'] = path.join(getcwd(), 'storage')
app.db = Database()
app.face = Face(app)


def success_handle(output, status=200, mimetype='application/json'):
    return Response(output, status=status, mimetype=mimetype)


def error_handle(error_message, status=500, mimetype='application/json'):
    return Response(json.dumps({"error": {"message": error_message}}), status=status, mimetype=mimetype)


def get_user_by_id(user_id):
    print("user id is :")
    print(user_id)
    user = {}
    results = app.db.select(
        "SELECT users.id, users.name, users.created, faces.id, faces.user_id, faces.filename,faces.created FROM users LEFT JOIN faces ON faces.user_id = users.id WHERE users.id = %s",
        [user_id])

    index = 0
    for row in results:
        face = {
            "id": row[3],
            "user_id": row[4],
            "filename": row[5],
            "created": row[6],
        }
        if index == 0:
            user = {
                "id": row[0],
                "name": row[1],
                "created": row[2],
                "faces": [],
            }
        if row[3]:
            user["faces"].append(face)
        index = index + 1

    if 'id' in user:
        return user
    return None


def delete_user_by_id(user_id):
    app.db.delete('DELETE FROM users WHERE users.id = ?', [user_id])
    # also delete all faces with user id
    app.db.delete('DELETE FROM faces WHERE faces.user_id = ?', [user_id])

#   Route for Hompage
@app.route('/', methods=['GET'])
def page_home():

    return render_template('index.html')

@app.route('/api', methods=['GET'])
def homepage():
    output = json.dumps({"api": '1.0'})
    return success_handle(output)


@app.route('/api/train', methods=['POST'])
def train():
    output = json.dumps({"success": True})

    if 'file' not in request.files:

        print ("Face image is required")
        return error_handle("Face image is required.")
    else:

        print("File request", request.files)
        file = request.files['file']

        if file.mimetype not in app.config['file_allowed']:

            print("File extension is not allowed")

            return error_handle("We are only allow upload file with *.png , *.jpg")
        else:

            # get name in form data
            name = request.form['name']

            print("Information of that face", name)

            print("File is allowed and will be saved in ", app.config['storage'])
            filename = secure_filename(file.filename)
            trained_storage = path.join(app.config['storage'], 'trained')
            file.save(path.join(trained_storage, filename))
            # let start save file to our storage

            # save to our sqlite database.db
            created = int(time.time())
            print("name is :"+name)
            print("created is ")
            print(created)
            user_id = app.db.insert('INSERT INTO users(name, created) values(%s,%s)', [name, created])

            if user_id:

                print("User saved in data", name, user_id)
                # user has been save with user_id and now we need save faces table as well

                face_id = app.db.insert('INSERT INTO faces(user_id, filename, created) values(%s,%s,%s)',
                                        [user_id, filename, created])

                if face_id:

                    print("cool face has been saved")
                    face_data = {"id": face_id, "filename": filename, "created": created}
                    return_output = json.dumps({"id": user_id, "name": name, "face": [face_data]})
                    app.face = Face(app)
                    return success_handle(return_output)
                else:

                    print("An error saving face image.")

                    return error_handle("n error saving face image.")

            else:
                print("Something happend")
                return error_handle("An error inserting new user")

        print("Request is contain image")
    return success_handle(output)


# route for user profile
@app.route('/api/users/<int:user_id>', methods=['GET', 'DELETE'])
def user_profile(user_id):
    if request.method == 'GET':
        user = get_user_by_id(user_id)
        if user:
            return success_handle(json.dumps(user), 200)
        else:
            return error_handle("User not found", 404)
    if request.method == 'DELETE':
        delete_user_by_id(user_id)
        return success_handle(json.dumps({"deleted": True}))

def slot():
    """Return true if x is in the range [start, end]"""
    lunchhourstart = 12
    lunchminutestart = 30
    lunchhourend = 14
    lunchminuteend = 30

    bkfsthourstart = 7
    bkfstminutestart = 30
    bkfsthourend = 10
    bkfstminuteend = 0

    hteahourstart = 16
    hteaminutestart = 30
    hteahourend = 17
    hteaminuteend = 30

    dinnerhourstart = 19
    dinnerminutestart = 30
    dinnerhourend = 21
    dinnerminuteend = 30

    now = datetime.datetime.now()
    nowhour = now.hour
    nowminute = now.minute

    if((nowhour>=lunchhourstart and nowhour<=lunchhourend)):
        if(((nowhour == lunchhourstart and nowminute>=lunchminutestart) and (nowhour == lunchhourend and nowminute<=lunchminuteend)) or
                (nowhour>lunchhourstart and nowhour<lunchminuteend)):
            return "lunch"

    if ((nowhour >= bkfsthourstart and nowhour <= bkfsthourend)):
        if (((nowhour == bkfsthourstart and nowminute >= bkfstminutestart) and (
                nowhour == bkfsthourend and nowminute <= bkfstminuteend)) or
                (nowhour > bkfsthourstart and nowhour < bkfstminuteend)):
            return "breakfast"

    if ((nowhour >= hteahourstart and nowhour <= hteahourend)):
        if (((nowhour == hteahourstart and nowminute >= hteaminutestart) and (
                nowhour == hteahourend and nowminute <= hteaminuteend)) or
                (nowhour > hteahourstart and nowhour < hteaminuteend)):
            return "hi-tea"

    if ((nowhour >= dinnerhourstart and nowhour <= dinnerhourend)):
        if (((nowhour == dinnerhourstart and nowminute >= dinnerminutestart) and (
                nowhour == dinnerhourend and nowminute <= dinnerminuteend)) or
                (nowhour > dinnerhourstart and nowhour < dinnerminuteend)):
            return "dinner"

    return "not a valid time"

# router for recognize a unknown face
@app.route('/api/recognize', methods=['POST'])
def recognize():
    if 'file' not in request.files:
        return error_handle("Image is required")
    else:
        file = request.files['file']
        # file extension valiate
        if file.mimetype not in app.config['file_allowed']:
            return error_handle("File extension is not allowed")
        else:

            filename = secure_filename(file.filename)
            unknown_storage = path.join(app.config["storage"], 'unknown')
            file_path = path.join(unknown_storage, filename)
            file.save(file_path)

            user_id = app.face.recognize(filename)
            today = date.today()
            # dd/mm/YY
            d1 = today.strftime("%d/%m/%Y")
            print("d1 =", d1)

            if user_id:
                user = get_user_by_id(user_id)
                att_id = app.db.insert('INSERT INTO attendance1(std_id,std_name,type,created) values(%s,%s,%s,%s)', [user_id,user["name"],slot(),str(d1)])
                print("attendance id is :")
                print (att_id)
                results = app.db.select(
                    "SELECT id, std_name, std_id, type, created FROM attendance1 WHERE std_id = %s and created = %s and type = %s",
                    [user_id, str(d1), slot()])
                print(results)

                message = {"message": "Hey we found {0} matched with your face image".format(user["name"]),
                           "user": user}
                return success_handle(json.dumps(message))
            else:

                return error_handle("Sorry we can not found any people matched with your face image, try another image")


# Run the app
app.run()