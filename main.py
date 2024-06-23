from flask import Flask, request, jsonify
import os
import json
import requests
import logging
import random

app = Flask(__name__)
data_dir = 'data/'
users_dir = os.path.join(data_dir, 'users')

if not os.path.exists(users_dir):
    os.makedirs(users_dir)

msg_count = 0

def send_webhook():
    url = 'https://discord.com/api/webhooks/124894254547514544/abcdefghijnqdsjohqjkdhqsdfqsdf'
    total_file = os.path.join(data_dir, 'total.json')

    try:
        with open(total_file, 'r') as f:
            data = json.load(f)
            msg_count = data.get('total_messages', 0)
            payload = {
                'content': f'Total messages: {msg_count}'
            }

            response = requests.post(url, json=payload)

            if response.status_code == 204:
                print('Webhook sent successfully')
            else:
                print(f'Failed to send webhook: {response.status_code}')
                print(response.text)

    except Exception as e:
        print(f'Exception occurred while sending webhook: {str(e)}')

total_path = os.path.join(data_dir, 'total.json')
if os.path.exists(total_path):
    with open(total_path, 'r') as f:
        msg_count = json.load(f).get('total_messages', 0)

def save_total():
    with open(total_path, 'w') as f:
        json.dump({'total_messages': msg_count}, f)

def save_user_msg(username, pfp, msg):
    user_file = os.path.join(users_dir, f'{username}.json')
    user_data = {
        'user_pfp': pfp,
        'messages': [],
        'total_messages': 0
    }

    if os.path.exists(user_file):
        with open(user_file, 'r') as f:
            user_data = json.load(f)

    if user_data['user_pfp'] != pfp:
        user_data['user_pfp'] = pfp

    user_data['messages'].append(msg)
    user_data['total_messages'] += 1

    if len(user_data['messages']) > 50:
        user_data['messages'] = user_data['messages'][-50:]

    with open(user_file, 'w') as f:
        json.dump(user_data, f)

@app.route('/api/save/bulk', methods=['POST'])
def save_bulk():
    global msg_count

    try:
        data = request.get_json()
        app.logger.info(f'Received data: {data}')

        msgs = data.get('messages', [])
        app.logger.info(f'Number of messages received: {len(msgs)}')

        msg_count += len(msgs)
        save_total()
        send_webhook()

        for m in msgs:
            username = m.get('user_name')
            pfp = m.get('user_pfp')
            msg = m.get('message')
            if username and pfp and msg:
                save_user_msg(username, pfp, msg)

        return jsonify({'success': True}), 200

    except Exception as e:
        app.logger.error(f'Error processing save_bulk request: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/total', methods=['GET'])
def get_total():
    try:
        user_files = [f for f in os.listdir(users_dir) if f.endswith('.json')]
        user_count = len(user_files)
        return jsonify({'total_messages': msg_count, 'total_users': user_count}), 200
    except Exception as e:
        app.logger.error(f'Error getting total: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<username>', methods=['GET'])
def get_user(username):
    user_file = os.path.join(users_dir, f'{username}.json')

    if not os.path.exists(user_file):
        return jsonify({'error': 'User not found'}), 404

    with open(user_file, 'r') as f:
        user_data = json.load(f)

    return jsonify(user_data), 200

@app.route('/api/random', methods=['GET'])
def get_random_user():
    try:
        user_files = [f for f in os.listdir(users_dir) if f.endswith('.json')]
        if not user_files:
            return jsonify({'error': 'No users found'}), 404

        random_user_file = random.choice(user_files)
        user_path = os.path.join(users_dir, random_user_file)

        with open(user_path, 'r') as f:
            user_data = json.load(f)

        return jsonify(user_data), 200

    except Exception as e:
        app.logger.error(f'Error getting random user: {str(e)}')
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
