from flask import Flask, jsonify, request, json
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask import send_file
import keras  # keras for deep learning
import numpy as np
import cv2
import os  # to manipulate with paths


app = Flask(__name__)
app.config["MONGO_DBNAME"] = "theseek"
app.config["MONGO_URI"] = 'mongodb://localhost:27017/theseek'
app.config["JWT_SECRET_KEY"] = 'secret'


mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


CORS(app)


@app.route("/users/register", methods=['POST'])
def register():
    users = mongo.db.users

    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    password = bcrypt.generate_password_hash(
        request.get_json()["password"].encode().decode('utf-8'))
    created = datetime.utcnow()

    response = users.find_one({"email": email})

    if response:
        result = jsonify({"error": "Email already exists"})
        return result
    else:
        user_id = users.insert({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "created": created
        })
        new_user = users.find_one({'_id': user_id})
        result = {"email": new_user['email'] + "\registered"}
        return jsonify({"result": result})


@app.route("/users/login", methods=['POST'])
def login():
    users = mongo.db.users
    email = request.get_json()['email']
    password = request.get_json()["password"]
    result = ""
    response = users.find_one({"email": email})

    if response:
        if bcrypt.check_password_hash(response["password"], password):
            access_token = create_access_token(identity={
                "first_name": response["first_name"],
                "last_name": response["last_name"],
                "email": response["email"]
            })
            result = jsonify({"token": access_token, "email": email})
        else:
            result = jsonify({"error": "Invalid username and password"})
    else:
        result = jsonify({"error": "No account found"})
    return result


@app.route("/contactus", methods=['POST'])
def contactus():
    contactQueries = mongo.db.contact
    email = request.get_json()['email']
    message = request.get_json()["message"]
    result = ""
    response = contactQueries.find_one({"email": email})

    if response:
        result = jsonify({"error": "Email already used"})
        return result
    else:
        contactForm = contactQueries.insert({
            "email": email,
            "message": message
        })
        result = {"email": "Query Submitted"}
        return jsonify({"email": result})


# Create a directory in a known location to save files to.
uploads_dir = 'static'
# os.makedirs(uploads_dir)


@app.route("/getSuspiciousActivity", methods=['POST'])
def getSuspiciousActivity():
    videos = mongo.db.videos
    model = keras.models.load_model('susp_act.model')  # to load crime model
    # cats_ contains categories i.e. burglary, firing, fighting
    cats_ = [i for i in os.listdir('Dataset/')]
    email = request.args['email']

    burgcount = 0
    fircount = 0
    figcount = 0

    video = request.files['video']
    filename = video.filename.replace(" ", "")
    video.save(os.path.join(uploads_dir, filename))
    vidstr = 'static/'+filename
    print(vidstr)
    cap = cv2.VideoCapture(vidstr)  # video

    result = ""

    if videos.find_one({"email": email, "videoName": filename}):
        result = jsonify({"error": "Video Name Against Account Exists"})
    else:
        try:
            while True:  # iterate each frame one by one
                ret, frame = cap.read()  # extract frame
                img = frame.copy()  # copy frame
                # convert frame from BGR to RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (224, 224))  # resize image by 224x224
                # find the class with highest probability 0 or 1 or 2
                actual = np.argmax(
                    list(model.predict([img.reshape(-1, 224, 224, 3)])))
                # print the probability for each of 3 classes and return the class
                print(list(model.predict([img.reshape(-1, 224, 224, 3)])),
                      'corresponding action : ', cats_[actual])

                if(cats_[actual] == "Firing"):
                    fircount += 1
                elif(cats_[actual] == "Burglary"):
                    burgcount += 1
                elif(cats_[actual] == "Fighting"):
                    figcount += 1

                # resize by 600x400 to show on screen
                frame = cv2.resize(frame, (600, 400))

                # put text on video frames
                cv2.putText(frame, str(cats_[actual]), (20, 20),
                            cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 255))
                cv2.imshow('iSecure', frame)  # show frames
                key = cv2.waitKey(33)  # show frame for 33 milli seconds
                if key == 27:  # escape
                    cv2.destroyAllWindows()  # destroy window if user presses escape
                    break
            cap.release()  # release the capture
            videoFiles = videos.insert_one({
                "email": email,
                "videoName": filename,
                "burglary": burgcount,
                "fighting": figcount,
                "firing": fircount,
                "filePath": vidstr
            })
        except:
            pass
        result = jsonify({"video": "Video has been saved"})
    return result


@app.route("/getSuspiciousActivityWebcam", methods=['POST'])
def getSuspiciousActivityWebcam():
    model = keras.models.load_model('susp_act.model')  # to load crime model
    # cats_ contains categories i.e. burglary, firing, fighting
    cats_ = [i for i in os.listdir('Dataset/')]

    cap = cv2.VideoCapture(0)  # video
    try:
        while True:  # iterate each frame one by one
            ret, frame = cap.read()  # extract frame
            img = frame.copy()  # copy frame
            # convert frame from BGR to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (224, 224))  # resize image by 224x224
            # find the class with highest probability 0 or 1 or 2
            actual = np.argmax(
                list(model.predict([img.reshape(-1, 224, 224, 3)])))
            # print the probability for each of 3 classes and return the class
            print(list(model.predict([img.reshape(-1, 224, 224, 3)])),
                  'corresponding action : ', cats_[actual])

            # resize by 600x400 to show on screen
            frame = cv2.resize(frame, (600, 400))
            # put text on video frames
            cv2.putText(frame, str(cats_[actual]), (20, 20),
                        cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 255))
            cv2.imshow('iSecure', frame)  # show frames
            key = cv2.waitKey(33)  # show frame for 33 milli seconds
            if key == 27:  # escape
                cv2.destroyAllWindows()  # destroy window if user presses escape
                break
        cap.release()  # release the capture
    except:
        pass
    result = jsonify({"webcam": "Webcam Successfull"})
    return result


@app.route("/getUserVideos", methods=['GET'])
def getUserVideos():
    videos = mongo.db.videos
    email = request.args['email']
    documents = videos.find({"email": email})
    userVideos = []
    filenames = []
    response = []
    files = {}
    for document in documents:
        document['_id'] = str(document['_id'])
        response.append(document)
    results = json.dumps(response)
    return results


if __name__ == "__main__":
    app.run(debug=True)
