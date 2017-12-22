# coding: utf-8
import logic
from flask import Flask,url_for,request
app = Flask(__name__)

@app.route('/')
def hello_world():
    logic.i = logic.i + 1
    return 'Τι θες ρε μαλακισμένο? Πάρε τον γαμιοαριθμό σου %d' % logic.i

@app.route('/register/<ipp>/<int:port>/<username>')
def registrate(ipp,port,username):
	return ipp + ' ' + str(port) + ' ' + username

@app.route('/list_groups/')
def groups():
	return "NA PARE TA GROUP SOY"

@app.route('/list_members/<group>')
def groupies(group):
	return u'Για ποιο group θες? Για το %s? ΑΝΤΕ ΓΕΙΑ' % group

@app.route('/join_group/<group>')
def joinare(group):
	return u'Μπράβο μαλάκα μου μπήκες στο %s' % group

@app.route('/exit_group/<group>')
def feuga(group):
	return u'Έλα ΠΑΡΕ ΠΟΥΛΟ ΑΠ\'ΤΟ %s' % group

@app.route('/quit')
def rage():
	return 'Καλό ψόφο. Μαλάκα. Με ip %s' % (request.remote_addr)