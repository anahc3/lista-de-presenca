from flask import Flask, request, jsonify
from datetime import datetime
from bson import ObjectId
import pymongo
import certifi
from pyzbar.pyzbar import decode
import base64
import io
import json

client = pymongo.MongoClient("mongodb+srv://presenca:adminadmin@cluster0.2rvon10.mongodb.net/", tlsCAFile=certifi.where())

app = Flask(__name__)

db = client["Banco"]
disciplina = db["Disciplina"]
listaP = db["ListaPresenca"]
professores = db["Professores"]
alunos = db["Alunos"]

@app.route('/login/professor/<username>', methods=['POST'])
def login_professor(username):
    professor = professores.find_one({'username': username})
    if professor:
        data = [f"Bem vindo(a) {username}!", True]
        return data, 200
    else:
        data = [f"Professor: ({username}) não está cadastrado na Base de Dados",False]
        return data, 400
    
@app.route('/login/aluno/<username>', methods=['POST'])
def login_aluno(username):
    aluno = alunos.find_one({'username': username})
    if aluno:
        data = [f"Bem vindo(a) {username}!", False]
        return data, 200
    else:
        data = [f"Aluno: ({username}) não está cadastrado na Base de Dados",False]
        return data, 400

@app.route('/professor/<username>', methods=['GET'])
def get_prof_info(username):
    professor = professores.find_one({'username': username})

    if professor:
        nome = professor["nome"]
        disciplinas = professor["disciplinas"]
        data = [nome, disciplinas]
        return jsonify(data), 200
    else:
        return jsonify({"message": "Professor não encontrado"}), 404
    
@app.route('/professor/<disciplina>', methods=['POST'])
def criar_lista_presenca(disciplina):
    professor = professores.find_one({'disciplinas': disciplina})
    if not professor:
        return jsonify({"message": "Disciplina não encontrada ou sem professor associado."}), 404

    alunos_da_disciplina = alunos.find({'disciplinas': disciplina})
    date = datetime.now()
    date = date.strftime("%d/%m/%Y")
    lista_presenca = {
        "disciplina": disciplina,
        "professor": professor['nome'],
        "date": date,
        "presenca": {aluno['username']: False for aluno in alunos_da_disciplina}
    }
    listaP.insert_one(lista_presenca)

    qr_data = {
        "disciplina": disciplina,
        "professor": professor['nome'],
        "date": date}    
    
    qr_data_json = json.dumps(qr_data)


    return jsonify({"message": "Lista de presença criada com sucesso.", "qr_code": qr_data_json}), 200

@app.route('/aluno/<professor>/<disciplina>/<username>', methods=['POST'])
def marcar_presenca(professor, disciplina, username):
    # Aqui você precisa garantir que está pegando a lista de presença correta (talvez usando a data também)
    lista = listaP.find_one({
        "disciplina": disciplina,
        "professor": professor,
        "date": datetime.now().strftime("%d/%m/%Y")
    })

    if lista and username in lista["presenca"]:
        listaP.update_one(
            {"_id": lista["_id"]},
            {"$set": {"presenca.{}".format(username): True}}
        )
        return jsonify({"message": "Presença marcada com sucesso"}), 200
    else:
        return jsonify({"message": "Erro ao marcar presença"}), 404



if __name__ == '__main__':
    app.run(debug=True, threaded=True)