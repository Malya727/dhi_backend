from flask import Flask, jsonify,request
from flask_cors import CORS, cross_origin
import statement5db as st1db
from flask_pymongo import PyMongo
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt_claims

)
app = Flask(__name__)
CORS(app)


app.config["MONGO_URI"] = "mongodb://localhost:27017/dhi_analytics"


mongo = PyMongo(app)
# Setup the Flask-JWT-Extended extension

app.config['JWT_SECRET_KEY'] = 'super-secret' 
jwt = JWTManager(app)


class UserObject:
    def __init__(self, username, roles,emlpoyeeGivenId,usn):
        self.username = username
        self.roles = roles
        self.emlpoyeeGivenId = emlpoyeeGivenId
        self.usn = usn
 

@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return {'roles': user.roles,"emlpoyeeGivenId":user.emlpoyeeGivenId,"usn":user.usn}

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.username

# Provide a method to create access tokens. The create_access_token()
# function is used to actually generate the token, and you can return
# it to the caller however you choose.
@app.route('/login', methods=['POST'])
def login():
    emlpoyeeGivenId = ''
    usn = ''
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    username = request.json.get('username', None)
    if not username:
        return jsonify({"msg": "Missing username parameter"}), 400
    user = mongo.db.dhi_user.find_one({'email': username})
    if not user:
        return jsonify({"msg": "Bad username or password"}), 401
    roles = [ x['roleName'] for x in user['roles']]
    if 'employeeGivenId' in user:
        emlpoyeeGivenId = user["employeeGivenId"]
    if 'usn' in user:
        usn = user["usn"]
    user = UserObject(username=user["email"], roles=roles,emlpoyeeGivenId = emlpoyeeGivenId,usn = usn)
    # Identity can be any data that is json serializable
    access_token = create_access_token(identity=user,expires_delta=False)
    return jsonify(access_token=access_token), 200

@app.route('/message')
def message():
    return {"message":"Check you luck"}



# Protect a view with jwt_required, which requires a valid access token
# in the request to access.


@app.route('/user', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    ret = {
            'user': get_jwt_identity(),  
            'roles': get_jwt_claims()['roles'] ,
            'employeeGivenId':get_jwt_claims()['emlpoyeeGivenId'],
            'usn':get_jwt_claims()['usn']
          }
        
    return jsonify(ret), 200


@app.route('/academicyear')
def getacademicYear():
    year = st1db.getacademicYear()
    return jsonify({'acdemicYear':year})

@app.route('/termNumber')
def get_term_numbers():
    terms = st1db.get_term_numbers()
    return jsonify({'term_numbers':terms})


@app.route("/attendancedetails/<string:usn>/<string:academicYear>/<termNumber>")
# view all the documents present in db
def get_attendance_details(usn, academicYear, termNumber):
    termNumber = list(termNumber.split(','))
    attendance_percent = st1db.get_details(usn, academicYear, termNumber)
    return jsonify({"attendance_percent": attendance_percent})

@app.route('/get-placement/<term>/<usn>')
def getOffers(term,usn):
    offers = st1db.get_student_placment_offers(term,usn)
    return jsonify({"offers":offers})


@app.route('/get-attendence-for-course/<sub>/<usn>')
def get_attendence_for_sub(sub,usn):
    attendence = st1db.get_attendence_for_course(sub,usn)
    return jsonify({"res":attendence})

@app.route('/get-selected-fac-details/<empid>/<term>')
def get_fac_details(empid , term):
    res = st1db.get_fac_wise_details(empid,term)
    return jsonify({"fac":res})

@app.route('/get-faculty-by-dept/<dept>')
def get_faculties_by_dept(dept):
    faculty = st1db.get_faculties_by_dept(dept)
    return jsonify({"faculty" : faculty})

@app.route('/get-dept-name')
def get_dept_names():
    dept = st1db.get_all_depts()
    return jsonify({"dept" : dept})
    
@app.route('/get-single-course/<emp>/<term>')
def get_single_course(emp , term):
    course = st1db.get_single_course(emp , term)
    return jsonify({"course" : course})

@app.route('/get-placement-for-sub/<empid>/<sub>/<sem>')
def getSubPlacement(empid,sub,sem): 
    details = st1db.get_emp_sub_placement(empid,sub,sem)
    return jsonify({
        "courseCode":sub,
        "totalStudents" : details[0],
        "placedStudents": details[1],
        "totalPositions": details[2]
    })

@app.route('/getUserNameEmail/<email>')
def get_user_name_by_email(email):
    res = st1db.get_user_name_by_email(email)
    return jsonify({'name':res})


if __name__ == "__main__":
    app.run(debug=True)
