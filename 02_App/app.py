from flask import Flask, render_template, request, make_response, session, redirect, url_for
from dynamoDB import DynamoDB
import pandas as pd
import uuid
import copy
import os

user_data_dict = {}
total_players = 0
db = DynamoDB() #connect to db
# df = pd.read_csv("model2.csv")[['qstn_id', "Abstract", "exp_label", "pred_exp", "sim_label", "pred_sim", "info_label", "pred_info"]]
# df = df.set_index('qstn_id')
df = db.extract_abstracts()
app = Flask(__name__)
app.secret_key = "\xe1\xcf\x05\xd5\xf4\x95H|\xab\x01'c*MOdD"
@app.route('/<restart>')
@app.route('/')
def index(restart='False'):
	global total_players
	global df

	if restart == True:
		df = db.extract_abstracts()

	user_data = {'total_players' : total_players, 'count' : -1, 'your_score' : 0.0, 'model_score' : 0.0, 'answers' : dict.fromkeys(list(df.index.values))}
	# df.index = df.sample(frac=1).index
	user_id = uuid.uuid4()
	session['user_id'] = user_id
	user_data_dict[str(user_id)] = copy.deepcopy(user_data) # adding the new user into dictionary

	if restart == 'False':	

		restart = 'True'	
		resp = make_response(render_template('home.html'))
	
	else:
		resp = redirect(url_for('qstn'))

	resp.set_cookie('user_id', str(user_id))
	total_players += 1
	print(user_data_dict)
	return resp

@app.route('/question.html', methods=['GET', 'POST'])
def qstn():

	user_id = request.cookies.get('user_id')
	count = user_data_dict[user_id]['count']
	count += 1
	if (count < 3):
		resp = make_response(render_template('question.html', count=count, df=df))
		user_data_dict[user_id]['count'] = count

	else:
		restart = True
		resp = redirect(url_for('game_over'))
	return resp

@app.route('/answer.html', methods=['GET', 'POST'])
def answer():
	user_id = request.cookies.get('user_id')
	count = user_data_dict[user_id]['count']   #count holds no.of qstns answered before the current question already
	your_tags = request.args.getlist('label')
	user_data_dict[str(user_id)]["answers"][df.index[count]] = your_tags

	yourtag_string = ""
	if (your_tags != []):
		yourtag_string = your_tags[0]
		for label in your_tags[1:]:
			yourtag_string += ", " + label 
	
	correct_tags = []
	# if df.Experiments[count]==1:
	# 	correct_tags.append("Experiment")
	# if df.Simulations[count]==1:
	# 	correct_tags.append("Simulation")
	# if df.Informatics[count]==1:
	# 	correct_tags.append("Informatics")
	print(df.index.values)

	if df.exp_label[count]=='1':
		correct_tags.append("Experiment")
	if df.sim_label[count]=='1':
		correct_tags.append("Simulation")
	if df.info_label[count]=='1':
		correct_tags.append("Informatics")


	correcttag_string = ""
	if (correct_tags != []):
		correcttag_string = correct_tags[0]
		for label in correct_tags[1:]:
			correcttag_string += ", " + label 

	model_tags = []
	if df.pred_exp[count]=='1':
		model_tags.append("Experiment")
	if df.pred_sim[count]=='1':
		model_tags.append("Simulation")
	if df.pred_info[count]=='1':
		model_tags.append("Informatics")

	modeltags_string = ""	# create list of tags in string format to present to user
	if (model_tags != []):
		modeltags_string = model_tags[0]
		for label in model_tags[1:]:
			modeltags_string += ", " + label 

	all_tags = set(['Experiment', 'Simulation', 'Informatics'])
	total_tags = len(all_tags)

	#Compute your new score
	your_score = user_data_dict[user_id]['your_score'] 
	your_score = round(your_score * count, 2) #multiply with count to take total score accumulated so far

	your_score += ((len(set(your_tags).intersection(set(correct_tags))) + len(all_tags.difference(set(your_tags)).intersection(all_tags.difference(set(correct_tags))))) / total_tags) * 100
	your_score /= (count + 1)
	your_score = round(your_score, 2)
	your_score_str = str(your_score) + "%"
	user_data_dict[user_id]['your_score'] = your_score
	#Compute model new score

	model_score = user_data_dict[user_id]['model_score'] 
	model_score = round(float(model_score) * count, 2)
	model_score += ((len(set(model_tags).intersection(set(correct_tags))) + len(all_tags.difference(set(model_tags)).intersection(all_tags.difference(set(correct_tags))))) / total_tags) * 100
	model_score /= (count + 1)
	model_score = round(model_score, 2)
	model_score_str = str(model_score) + "%"
	user_data_dict[user_id]['model_score'] = model_score
	if ((count + 1) >= 3):
		resp = make_response(render_template('answer.html', df=df, your_tags=yourtag_string, correct_tags=correcttag_string, model_tags=modeltags_string, your_score=your_score_str, model_score=model_score_str, done = True))			

	else:
		resp = make_response(render_template('answer.html', df=df, your_tags=yourtag_string, correct_tags=correcttag_string, model_tags=modeltags_string, your_score=your_score_str, model_score=model_score_str, done = False))			
	return resp

@app.route('/gameOver')
def game_over():
	user_id = request.cookies.get('user_id')
	your_score = user_data_dict[user_id]['your_score']
	model_score = user_data_dict[user_id]['model_score']
	ml_won = 2 #tells who won; 0 if you, 1 if model, 2 if tie

	if (your_score > model_score):
		db.insert_userdata(user_id, user_data_dict[user_id])
		ml_won = 0

	elif (your_score < model_score):
		del user_data_dict[user_id]			# deleting record of user with lesser scores
		ml_won = 1

	resp = make_response(render_template('game_over.html', ml_won = ml_won))
	return resp

if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')