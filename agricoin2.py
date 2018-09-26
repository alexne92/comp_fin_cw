# -*- coding: utf-8 -*-
"""
Created on Fri Apr 27 17:58:54 2018

@author: vneze
"""

# Import the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Build the Blockchain

class Blockchain:

    def __init__(self):
        self.chain = []
        self.trans = []
        self.create_block(nonce = 1, prev_hash = '0')
        self.nodes = set()
    
    def create_block(self, nonce, prev_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'nonce': nonce,
                 'previous hash': prev_hash,
                 'transactions': self.trans}
        self.trans = []
        self.chain.append(block)
        return block
    
    
    def proof_of_work(self, prev_nonce):
        nonce = 1
        check_nonce = False
        while check_nonce is False:
            hash_operation = hashlib.sha256(str((2 *nonce**2) - (3 * prev_nonce**2)).encode()).hexdigest()
            if hash_operation[:5] == '00000':
                check_nonce = True
            else:
                nonce += 1
        return nonce
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def chain_valid(self, chain):
        prev_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous hash'] != self.hash(prev_block):
                return False
            prev_nonce = prev_block['nonce']
            nonce = block['nonce']
            hash_operation = hashlib.sha256(str((2 *nonce**2) - (3 * prev_nonce**2)).encode()).hexdigest()
            if hash_operation[:5] != '00000':
                return False
            prev_block = block
            block_index += 1
        return True
    
    def add_transaction(self, sender, receiver, amount):
        self.trans.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        prev_block = self.chain[-1]
        return prev_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on Port 5001
node_address = str(uuid4()).replace('-', '')

# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    prev_block = blockchain.chain[-1]
    prev_nonce = prev_block['nonce']
    nonce = blockchain.proof_of_work(prev_nonce)
    prev_hash = blockchain.hash(prev_block)
    #blockchain.add_transaction(sender = '0', receiver = node_address, amount = 1)
    block = blockchain.create_block(nonce, prev_hash)
    response = {'result': 'Block has been successfully mined.',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'nonce': block['nonce'],
                'previous hash': block['previous hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/validation', methods = ['GET'])
def validation():
    validation = blockchain.chain_valid(blockchain.chain)
    if validation:
        response = {'result': 'Valid Blockchain.'}
    else:
        response = {'result': 'Invalid Blockchain.'}
    return jsonify(response), 200

# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Error, there are some missing elements at the transaction.', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'result': f'The transactions is now on Block {index}'}
    return jsonify(response), 201

# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "Error, no node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'result': 'Connection successfully established. The nodes of the Blockchain are the following:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'result': 'The chain was succefully updated.',
                    'new_chain': blockchain.chain}
    else:
        response = {'result': 'This is the largest chain.',
                    'chain': blockchain.chain}
    return jsonify(response), 200

# Running the app on the node of Port 5000
app.run(host = '0.0.0.0', port = 5001)