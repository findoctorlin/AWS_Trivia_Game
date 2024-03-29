# readme

## Structure of the game App

![Untitled](readme%204476895914e04dccbd7e8d27e23c2cca/Untitled.png)

![Untitled](readme%204476895914e04dccbd7e8d27e23c2cca/Untitled%201.png)

- Amazon S3: Web Server

![Untitled](readme%204476895914e04dccbd7e8d27e23c2cca/Untitled%202.png)

- **API Gateway**: Service, hosts all the APP’s API API
    - **Websocket API**: communication between user browser and server
    - Clicking ”start Game”，a Websocket message: browser → **Websocket API**
- Lambda function : create, join, start the game, send questions to players, accept the answers, calculate scores
- APP data : **DynamoDB Table**
- Step function: update to the next question
    - lambda(Question): send Question to player
    - lambda(Accept Answer): update the DynamoDB item
    - lambda(Calculate Score): loops over Answers in DynamoDB Table, update & send Scores back to players
    

![Untitled](readme%204476895914e04dccbd7e8d27e23c2cca/Untitled%203.png)

- services and Tools：
    - Python for Backend
    - React for Fronted
    - AWS service, API Gateway, S3, lambda function, Step function, DynamoDB
    
    ![Untitled](readme%204476895914e04dccbd7e8d27e23c2cca/Untitled%204.png)
    

## APP Build

[https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/DEV-AWS-MO-DevOps-C1/exercise-1.html](https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/DEV-AWS-MO-DevOps-C1/exercise-1.html)

[https://sst.dev/chapters/create-an-iam-user.html](https://sst.dev/chapters/create-an-iam-user.html)

### **Task 2: Creating the backend infrastructure**

In this task, you deploy the application stack by using the AWS SAM and the AWS CLI. You also make a few minor configuration changes.

1. In the AWS Cloud9 terminal, change the directory to the `trivia-app` folder and use AWS SAM to build the `template.yaml` file.
    
    ```bash
    cd trivia-app
    sam build # prepares an application for subsequent steps in the developer workflow, such as local testing or deploying to the AWS Cloud
    sam deploy --guided # deploys an application to the AWS Cloud, --guided: Specify this option to have the AWS SAM CLI use prompts to guide you through the deployment
    ```
    
    ![https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/DEV-AWS-MO-DevOps-C1/images/clipboard.svg](https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/DEV-AWS-MO-DevOps-C1/images/clipboard.svg)
    
    **AWS SAM settings:** For the **Stack Name**, make sure to copy `trivia-app` and paste it. However, for the other entries, accept the default selections by pressing Enter or Return.
    
    ```
    Stack Name [sam-app]: trivia-app
    AWS Region [us-west-2]: <Press Enter or Return>
    #Shows you resources changes to be deployed and require a 'Y' to initiate deploy
    Confirm changes before deploy [y/N]: <Press Enter or Return>
    #SAM needs permission to be able to create roles to connect to the resources in your template
    Allow SAM CLI IAM role creation [Y/n]: <Press Enter or Return>
    Save arguments to configuration file [Y/n]: <Press Enter or Return>
    SAM configuration file [samconfig.toml]: <Press Enter or Return>
    SAM configuration environment [default]: <Press Enter or Return>
    ```
    
    You should get confirmation that the stack was created successfully.
    
    ```
    Successfully created/updated stack - trivia-app in us-west-2
    ```
    
2. From the **Outputs** table in the terminal output, copy the Websocket **Value**. It should look similar to the following example:
    
    ```
    wss://xxxxxxxxxx.execute-api.us-west-2.amazonaws.com/Prod
    ```
    

---

## CloudFormation outputs from deployed stack

## Outputs

## Key TriviaWebSocketApi
Description API Gateway websockets endpoint
Value wss://qyb8smgla1.execute-api.us-west-2.amazonaws.com/Prod

Successfully created/updated stack - trivia-app in us-west-2

![Untitled](readme%204476895914e04dccbd7e8d27e23c2cca/Untitled%205.png)

```jsx
const config = require('./config.js');
console.log(config.WebsocketEndpoint); // output WebSocket endpoint URL
```

### Testing the frontend on cloud9

```bash
cd front-end-react/
npm install # 用于安装一个 Node.js 项目的所有依赖项。当执行此命令时，npm (Node Package Manager) 会查看项目根目录下的 package.json 文件
npm run start # 此命令实际执行的具体操作是在 package.json 文件的 scripts 部分中定义的 start 脚本。对于许多基于 create-react-app 的项目，npm run start 会启动一个本地开发服务器，默认情况下在浏览器中打开 http://localhost:3000
```

![Untitled](readme%204476895914e04dccbd7e8d27e23c2cca/Untitled%206.png)

### pytest Setting

```markdown
shift-ctrl-P -> python configure test, settings.json：
{
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestEnabled": true
}
```

### /Users/yuhanlin/Documents/Tutorial/AWS/trivia-app/back-end-python/gameactions/app.py

![Untitled](readme%204476895914e04dccbd7e8d27e23c2cca/Untitled%207.png)

- Let's say you have a Lambda function that is triggered through the API Gateway to process a POST request containing user information. If the body of the request is a JSON string like this：
    
    {
    "name": "John Doe",
    "age": 30
    }
    
    ```python
    name = get_body_param(event, "name") # event is what API Gateway pass to Lambda function
    ```
    

![Untitled](readme%204476895914e04dccbd7e8d27e23c2cca/Untitled%208.png)

```python
# 假设这是从 DynamoDB 表中获取的当前游戏中所有玩家的连接 ID 列表
player_connections = ["conn_id_1", "conn_id_2", "conn_id_3"]

# 准备要广播的数据
data = {
    "action": "gamestarted",
    "message": "The game has started!"
}

# 调用 send_broadcast 函数，向所有玩家广播游戏开始的消息
send_broadcast(player_connections, data)
```

```python
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
```

1. 在一个实时的多玩家在线游戏中，当一个玩家想要创建一个新的游戏实例时，客户端应用会通过 WebSocket 向后端发送一个请求。
2. 这个请求被 API Gateway 捕获并触发 **`trivia_newgame`** Lambda 函数。
3. 函数执行上述逻辑，创建游戏实例，并通过 WebSocket 通知客户端游戏已创建，准备玩家加入。

```python
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
```

- step function是引擎，state machine代表其工作流
- machine_input 中的key的名字不是关键字，可以自己定义
    
    ```python
    def lambda_handler(event, context):
        game_id = event['gameid']
        questions = event['questions']
        current_question_pos = event['iterator']['questionpos']
        ...
    ```
    
    在这个例子中，**`event`** 参数就是传递给 Lambda 函数的 **`machine_input`** 字典，Lambda 函数通过与 **`machine_input`** 中定义的相同的键名来访问数据
