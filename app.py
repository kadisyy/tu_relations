# app.py
from flask import Flask, request, jsonify, render_template
from py2neo import Graph

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


@app.route("/capabilities", methods=['GET'])
def get_capabilities():
    capabilities = {
        "描述": "人物关系图谱管理系统",
        "功能列表": [
            {
                "功能": "添加人物关系",
                "描述": "在两个人物之间创建一条带有关系类型的有向边",
                "接口": "POST /relationships",
                "参数": {"from_person": "起始人物名称", "to_person": "目标人物名称", "relationship_type": "关系类型"}
            },
            {
                "功能": "查询指定人物的关系",
                "描述": "查询某个人物与其他人物之间的所有关系",
                "接口": "GET /relationships/<person_name>",
                "参数": {"person_name": "要查询的人物名称"}
            },
            {
                "功能": "查询所有人物关系",
                "描述": "获取图数据库中所有人物及其关系",
                "接口": "GET /relationships_all",
                "参数": {}
            },
            {
                "功能": "删除人物关系",
                "描述": "删除两个人物之间指定类型的关系",
                "接口": "DELETE /relationships",
                "参数": {"from_person": "起始人物名称", "to_person": "目标人物名称", "relationship_type": "关系类型"}
            },
            {
                "功能": "查看系统功能",
                "描述": "返回系统支持的所有功能列表",
                "接口": "GET /capabilities",
                "参数": {}
            }
        ]
    }
    return jsonify(capabilities)


if __name__ == "__main__":
    app.run(debug=True)
