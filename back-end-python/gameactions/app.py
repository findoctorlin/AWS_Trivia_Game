"Backend for the trivia game"
import json
import os
import random
import uuid

import boto3 # AWS SDK for Python
import yaml
from botocore.exceptions import ClientError

DYNAMODB = boto3.resource('dynamodb')
TABLE = DYNAMODB.Table(os.getenv('TABLE_NAME'))
# MANAGEMENT 对象是你与 AWS API Gateway Management API 交互的接口，你可以把它视为一个代表 API Gateway 的客户端对象，它封装了与 API Gateway 进行通信所需的方法和认证信息
MANAGEMENT = boto3.client('apigatewaymanagementapi', endpoint_url=os.getenv('APIGW_ENDPOINT')) # Create a low-level service client obj by name using the default session. APIGW_ENDPOINT in template.yaml
STEPFUNCTIONS = boto3.client('stepfunctions')
COLORS = ("AliceBlue,AntiqueWhite,Aqua,Aquamarine,Azure,Beige,Bisque,Black,BlanchedAlmond,Blue,"
"BlueViolet,Brown,BurlyWood,CadetBlue,Chartreuse,Chocolate,Coral,CornflowerBlue,Cornsilk,Crimson,"
"Cyan,DarkBlue,DarkCyan,DarkGoldenrod,DarkGray,DarkGreen,DarkKhaki,DarkMagenta,DarkOliveGreen,"
"DarkOrange,DarkOrchid,DarkRed,DarkSalmon,DarkSeaGreen,DarkSlateBlue,DarkrcSlateGray,DarkTurquoise,"
"DarkViolet,DeepPink,DeepSkyBlue,DimGray,DodgerBlue,FireBrick,FloralWhite,ForestGreen,Fuchsia,"
"Gainsboro,GhostWhite,Gold,Goldenrod,Gray,Green,GreenYellow,Honeydew,HotPink,IndianRed,Indigo,"
"Ivory,Khaki,Lavender,LavenderBlush,LawnGreen,LemonChiffon,LightBlue,LightCora,LightCyan,"
"LightGoldenrodYellow,LightGreen,LightGrey,LightPink,LightSalmon,LightSeaGreen,LightSkyBlue,"
"LightSlateGray,LightSteelBlu,LightYellow,Lime,LimeGreen,Linen,Magenta,Maroon,MediumAquamarine,"
"MediumBlue,MediumOrchid,MediumPurple,MediumSeaGreen,MediumSlateBlue,MediumSpringGreen,"
"MediumTurquoise,MediumVioletRed,MidnightBlue,MintCream,MistyRose,Moccasin,NavajoWhite,Navy,"
"OldLace,Olive,OliveDrab,Orange,OrangeRed,Orchid,PaleGoldenrod,PaleGreen,PaleTurquoise,"
"PaleVioletRed,PapayaWhip,PeachPuff,Peru,Pink,Plum,PowderBlue,Purple,Red,RosyBrown,RoyalBlue,"
"SaddleBrown,Salmon,SandyBrown,SeaGreen,Seashell,Sienna,Silver,SkyBlue,SlateBlue,SlateGray,Snow,"
"SpringGreen,SteelBlue,Tan,Teal,Thistle,Tomato,Turquoise,Violet,Wheat,White,WhiteSmoke,Yellow,"
"YellowGreen").split(",")
WAIT_SECONDS = 20

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__)) # __file__ 是一个特殊的变量，它包含了当前执行脚本的绝对路径
with open(os.path.join(SCRIPT_PATH, "all-questions.yaml"), 'r', encoding="utf-8") as stream:
    QUESTIONS = yaml.safe_load(stream)

def get_random_player_name():
    "Generate a random player name"
    return random.choice(COLORS) # Choose a random element from a non-empty sequence

def get_body_param(event, param):
    "Load JSON body content and get the value of a property"
    "从一个 HTTP 请求的正文(body)中提取特定参数值"
    body = json.loads(event["body"]) # json.loads 函数将event对象中的body字符串解析为dict。event["body"] 包含了 HTTP 请求的正文，这通常是一个 JSON 字符串
    value = body[param]
    return value

def get_players(game_id):
    "Query dynamo for a list of game players"
    "从 DynamoDB 表中查询和获取特定游戏 ID 下所有玩家的信息"
    connections = TABLE.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("gameId").eq(game_id)
    )
    return [{
        "connectionId" : p["connectionId"], # trivia_newgame.connection中定义这些key
        "playerName": p["playerName"],
        "score": int(p["score"])
        } for p in connections["Items"]]

def send_broadcast(connections, data): # connections参数的具体值: 即具体的连接ID列表
    "Post out websocket messages to a list of connection ids"
    for connection in connections:
        try:
            if "action" in data and data["action"] == "playerlist":
                # we need to insert "currentPlayer" into player list broadcasts
                for player in data["players"]:
                    player["currentPlayer"] = (connection==player["connectionId"]) #True/False 判定是否为当前玩家

            MANAGEMENT.post_to_connection(
                Data=json.dumps(data),
                ConnectionId=connection
            )
        except ClientError as error:
            if error.response['Error']['Code'] == 'GoneException':
                print("Missing connection ", connection)

def trivia_newgame(event, _): # _: 占位符，表示此函数不使用其第二个位置参数
    # event: 包含触发 Lambda 函数的事件信息的字典。对于由 API Gateway 触发的 Lambda 函数，这个字典包含了 HTTP 请求的详细信息
    "Lambda function to intitate a new game"
    game_id = uuid.uuid4().hex

    # write the connection and game id into the dynamo table
    connection_id = event["requestContext"]["connectionId"]
    player_name = get_random_player_name()
    connection = {
        "gameId": game_id,
        "connectionId": connection_id,
        "playerName": player_name,
        "score": 0
    } # 创建一个包含游戏 ID、连接 ID、玩家名和初始分数的字典（connection），并将这个字典作为一个新item保存到DynamoDB表中
    TABLE.put_item(Item=connection)

    # send game created
    MANAGEMENT.post_to_connection(
        Data=json.dumps({"action": "gamecreated", "gameId": game_id}),
        ConnectionId=connection_id
    )

    # send player list of single player，初始化客户端界面上的玩家列表
    MANAGEMENT.post_to_connection(
        Data=json.dumps({"action": "playerlist", "players": [
            {
                "connectionId" : connection_id,
                "currentPlayer" : True,
                "playerName": player_name,
                "score": 0
            }
        ]}),
        ConnectionId=connection_id
    )

    return {
        "statusCode": 200,
        "body": 'Game created.'
    } # 返回值表明新游戏创建过程成功完成，并将通过 API Gateway 返回给客户端

def trivia_joingame(event, _):
    "Lambda function to join a game"
    connection_id = event["requestContext"]["connectionId"]
    game_id = get_body_param(event, "gameid")

    # write the new connection into the dynamo table
    connection = {
        "gameId": game_id,
        "connectionId": connection_id,
        "playerName": get_random_player_name(),
        "score": 0
    }
    TABLE.put_item(Item=connection) # 新加入的玩家信息就被记录下来

    players = get_players(game_id)
    send_broadcast(
        [p["connectionId"] for p in players],
        {"action": "playerlist", "players": players}
    )

    return {
        "statusCode": 200,
        "body": 'Joined game.'
    }


def trivia_startgame(event, _):
    "Lambda function to start a game"
    game_id = get_body_param(event, "gameid")
    state_machine = os.getenv("STATE_MACHINE")

    questions = QUESTIONS.copy()
    random.shuffle(questions)
    questions = questions[:10] # 选取列表中的前10个问题作为这场游戏的题目

    machine_input = { # STEPFUNCTIONS在执行时候的input，key是自定义的
        "gameid": game_id,
        "questions": questions,
        "waitseconds": WAIT_SECONDS,
        "iterator": {
            "questionpos": 0, # 在trivia_calculate_scores函数定义其叠加
            "IsGameOver": False
        }
    }
    # Starts a state machine execution.
    STEPFUNCTIONS.start_execution(
        stateMachineArn=state_machine, # Amazon Resource Name (ARN)。ARN 是 AWS 资源的唯一标识符
        name=f"game-{game_id}",
        input=json.dumps(machine_input)
    )

    players = get_players(game_id)
    send_broadcast([p["connectionId"] for p in players], {"action": "gamestarted"})

    return {
        "statusCode": 200,
        "body": 'Joined game.' # 在 HTTP 响应中，body 通常用于携带服务器返回的数据
    }


def trivia_answer(event, _): # event 包含了触发该 Lambda 函数的事件信息，通常是通过 API Gateway 传递的 WebSocket 请求
    "Lambda function for a player to post an answer"
    game_id = get_body_param(event, "gameid")
    questionid = get_body_param(event, "questionid")
    answer = get_body_param(event, "answer")
    connection_id = event["requestContext"]["connectionId"] # requestContext是一个固定字段(API gateway触发Lambda函数时)；connectionId是Websocket API的字段

    TABLE.update_item(
        Key={"gameId": game_id, "connectionId": connection_id}, # The primary key of the item to be updated
        AttributeUpdates={
            "lastQuestionId": {'Value': questionid, "Action": "PUT"}, # 将"lastQuestionId"和"lastAnswer"字段更新为玩家最近提交的问题ID和答案
            "lastAnswer": {'Value': answer, "Action": "PUT"} # "Action": "PUT" 表示如果这些字段不存在，则创建它们
        }
    )

    return {
        "statusCode": 200,
        "body": 'Recieved answer.'
    }

def trivia_question(event, _):
    "Send a question - called from statemachine"
    game_id = event["gameid"] # event 这些key在状态机内被定义(trivia_startgame.machine_input)
    question_pos = event["iterator"]["questionpos"]
    questions = event["questions"]
    question = event["questions"][question_pos]
    del question["answer"]
    question["question"] += f" {question_pos+1}/{len(questions)}" # 修改问题文本以包含当前问题的编号和总问题数，例如，“问题 3/10”

    players = get_players(game_id)
    send_broadcast([
        p["connectionId"] for p in players],
        {"action": "question", "question": question}
    )

    return True

def trivia_calculate_scores(event, _):
    "Calc scores for a game - called from statemachine"
    game_id = event["gameid"]
    question_pos = event["iterator"]["questionpos"]
    questions = event["questions"]
    question = event["questions"][question_pos]
    # 使用 DynamoDB 客户端查询与当前 game_id 相关的所有玩家的连接信息。这可能包括玩家的答案和其他相关数据
    connections = TABLE.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("gameId").eq(game_id)
    )

    # spin thru the connections and check their answers
    players = [] # 初始化一个空列表 players，遍历查询结果中的每个连接（即每个玩家）, 提取每个玩家的连接ID、名称和当前分数
    for connection in connections["Items"]:
        connection_id = connection["connectionId"]
        player_name = connection["playerName"]
        score = int(connection["score"])
        last_question_id = connection["lastQuestionId"] if "lastQuestionId" in connection else ""
        last_answer = connection["lastAnswer"] if "lastAnswer" in connection else ""

        if last_question_id == question["id"] and last_answer == question["answer"]:
            score += 10
            TABLE.update_item(
                Key={"gameId": game_id, "connectionId": connection_id},
                AttributeUpdates={"score": {'Value': score, "Action": "PUT"}}
            )

        players.append({
            "connectionId" : connection_id,
            "playerName" : player_name,
            "score": score
        })

    # notify everyone the scores
    send_broadcast(
        [c["connectionId"] for c in connections["Items"]],
        {"action": "playerlist", "players": players}
    )

    question_pos += 1
    game_over = question_pos >= len(questions)
    if game_over:
        send_broadcast(
             [c["connectionId"] for c in connections["Items"]],
             {"action": "gameover"}
        )

    return {
                "questionpos": question_pos,
                "IsGameOver": game_over
            }
