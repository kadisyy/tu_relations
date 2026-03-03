# app.py
from flask import Flask, request, jsonify, render_template, send_file
from py2neo import Graph
import base64
import io

app = Flask(__name__)
graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/relationships", methods=['POST'])
def add_relationship():
    data = request.json
    query = """
    MERGE (p1:Person {name: $from_person})
    MERGE (p2:Person {name: $to_person})
    CREATE (p1)-[r:RELATES_TO {type: $relationship_type}]->(p2)
    RETURN type(r), p1.name, p2.name
    """
    result = graph.run(query, from_person=data['from_person'], to_person=data['to_person'],
                       relationship_type=data['relationship_type']).data()
    return jsonify(result), 201


@app.route("/relationships_all", methods=['GET'])
def get_relationshipsall():
    query = """
    MATCH (p:Person)-[r:RELATES_TO]-(related)
    RETURN p.name AS name, collect(related.name) AS related_persons, collect(r.type) AS relationships
    """
    # 这里的graph.run返回一个Neo4j结果对象，通过.data()将结果转化为列表
    result = graph.run(query).data()
    # 这将返回一个包含所有人物及其关系的列表
    return jsonify(result)


@app.route("/relationships/<string:person_name>", methods=['GET'])
def get_relationships(person_name):
    # 使用参数来过滤查询结果
    query = """
    MATCH (p:Person {name: $person_name})-[r:RELATES_TO]-(related)
    RETURN p.name AS name, collect(related.name) AS related_persons, collect(r.type) AS relationships
    """
    result = graph.run(query, person_name=person_name).data()  # 符号$用于引用参数
    return jsonify(result)


@app.route("/relationships", methods=['DELETE'])
def delete_relationship():
    data = request.json
    query = """
    MATCH (p1:Person {name: $from_person})-[r:RELATES_TO {type: $relationship_type}]->(p2:Person {name: $to_person})
    DELETE r
    """
    graph.run(query, from_person=data['from_person'], to_person=data['to_person'],
              relationship_type=data['relationship_type'])
    return jsonify('Relationship deleted'), 204


@app.route("/generate_image", methods=['POST'])
def generate_image():
    data = request.get_json(silent=True)
    if not data or 'image_data' not in data:
        return jsonify({'error': 'Invalid request: image_data is required'}), 400
    image_data = data.get('image_data', '')
    # Strip the data URL prefix (e.g. "data:image/png;base64,")
    if ',' in image_data:
        image_data = image_data.split(',', 1)[1]
    try:
        img_bytes = base64.b64decode(image_data)
    except Exception:
        return jsonify({'error': 'Invalid base64 image data'}), 400
    return send_file(
        io.BytesIO(img_bytes),
        mimetype='image/png',
        as_attachment=True,
        download_name='relationships_graph.png'
    )


if __name__ == "__main__":
    app.run(debug=True)
