import boto3
import json
import copy
import pandas as pd
import random

class DynamoDB():
    def __init__(self):
        self.db = boto3.resource('dynamodb')
        self.users = self.db.Table('users')
        self.labeled_data = self.db.Table('labeled_data')

    def insert_userdata(self, user_id, user_data):
        ans_dict = copy.deepcopy(user_data['answers'] )
        # qstns = list(ans_dict.keys())
        #Converting keys of the answer_data (qstns) to string 
        # for key in qstns:
        #     ans_dict[str(key)] = ans_dict[key]
        #     del ans_dict[key]
        ans_str = json.dumps(ans_dict)
        your_score_str = str(user_data['your_score'])
        model_score_str = str(user_data['model_score'])
        tot_users = user_data['total_players']
        item = {'user_id' : user_id, 'answers' : ans_str, 'your_score' : your_score_str, 'model_score' : model_score_str, 'total_players' : tot_users}
        table = self.users
        table.put_item(Item=item)

    def extract_abstracts(self, n=10):
        df = pd.DataFrame(columns=["qstn_id", "Abstract", "exp_label", "sim_label", "info_label", "pred_exp", "pred_sim", "pred_info"])
        table = self.labeled_data
        all_ids = table.scan(Select='SPECIFIC_ATTRIBUTES', ProjectionExpression='qstn_id')['Items']
        indices = []
        for id in all_ids:
            indices.append(id['qstn_id'])
        
        indices = random.sample(indices, n) #get n random qstn_ids
        # now get the records corresponding to these indices 
        for q_id in indices:
            record = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('qstn_id')
                                   .eq(q_id))['Items'][0]
            df = df.append(record, ignore_index=True)
        df = df.set_index('qstn_id')
        return df