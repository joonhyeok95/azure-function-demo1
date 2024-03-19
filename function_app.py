import azure.functions as func
import logging
from azure.functions.decorators.core import DataType
import uuid, json
from jsonschema import validate

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

####################################################################################################################################
# GET default ?name={data}
####################################################################################################################################
@app.function_name(name="API_DEMO_01_GET")
@app.route(route="demo01")
def API_DEMO_01(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP trigger 함수')

    name = req.params.get('name')
    if name:
        return func.HttpResponse(f"[VERSION_1.0.0] Hello, {name}.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
    
####################################################################################################################################
# POST DB insert {"name":"1","url":"2"} 
# SQL Binding 방식
####################################################################################################################################
@app.function_name(name="API_DEMO_02_POST")
@app.route(route="navien", auth_level=func.AuthLevel.ANONYMOUS, methods=['POST'])
@app.generic_output_binding(arg_name="toDoItems", type="sql", CommandText="dbo.navien_demo", ConnectionStringSetting="SqlConnectionString", data_type=DataType.STRING) # DB 연결
def API_POST_01(req: func.HttpRequest, toDoItems: func.Out[func.SqlRow]) -> func.HttpResponse:
     logging.info("경동나비엔 Mssql DB insert")
     name = req.params.get('name')
     if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')
            url = req_body.get('url')

     if name:
        toDoItems.set(func.SqlRow({"id": str(uuid.uuid4()), "title": name, "completed": False, "url": url}))
        return func.HttpResponse(f"Hello {name}!")
     else:
        return func.HttpResponse(
                    "Please pass a name on the query string or in the request body",
                    status_code=400
                )

####################################################################################################################################
# POST DB insert 2 {"order":"1","title": "ohohoho","url":"http://127.0.0.1","completed": true}
####################################################################################################################################
@app.function_name(name="API_DEMO_02_POST_2")
@app.route(route="navien-2", auth_level=func.AuthLevel.ANONYMOUS, methods=['POST'])
@app.generic_output_binding(arg_name="toDoItems", 
                            type="sql", 
                            CommandText="dbo.navien_demo", 
                            ConnectionStringSetting="SqlConnectionString", 
                            data_type=DataType.STRING) # DB 연결
def API_POST_01_2(req: func.HttpRequest, toDoItems: func.Out[func.SqlRow]) -> func.HttpResponse:
    logging.info("경동나비엔 Mssql DB insert 2")
    body = json.loads(req.get_body())
    # id에 대한 값을 생성하고 추가합니다.
    body['id'] = str(uuid.uuid4())  # UUID4 생성
    row = func.SqlRow.from_dict(body)
    toDoItems.set(row)
    return func.HttpResponse(
        body=req.get_body(),
        status_code=201,
        mimetype="application/json"
    )
          
####################################################################################################################################
# JSON schema Validate Required
####################################################################################################################################
class CustomJSONResponse(func.HttpResponse):
    def __init__(self, body=None, status_code=200, headers=None, charset='utf-8', content_type='application/json', **kwargs):
        if headers is None:
            headers = {}
        headers['Content-Type'] = f'{content_type}; charset={charset}'
        super().__init__(body=json.dumps(body), status_code=status_code, headers=headers, **kwargs)

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "url": {"type": "string"}
    },
    "required": ["name"]
}

@app.function_name(name="API_DEMO_03_VALIDATION")
@app.route(route="validate", auth_level=func.AuthLevel.ANONYMOUS, methods=['POST'])
def API_POST_02(req: func.HttpRequest) -> CustomJSONResponse:
    logging.info("경동나비엔 validation API")
    try:
        # HTTP 요청으로부터 JSON 데이터 읽기
        req_body = req.get_json()
        # 데이터 유효성 검사
        validate(instance=req_body, schema=schema)
        data = {
            "message": "This is a custom JSON response",
            "status": "success"
        }
        return CustomJSONResponse(
            body=data,
            status_code=200
        )
    except Exception as e:
        # 유효성 검사 실패 또는 예외 발생 시 처리
        logging.exception('Error occurred during JSON validation:')
        return CustomJSONResponse(
            body={"error":str(e)},
            status_code=200
        )
    
####################################################################################################################################
# JSON schema test(Select)
####################################################################################################################################
@app.function_name(name="API_DEMO_05_SELECT_ONE")
@app.route(route="navien-test/{id}")
@app.sql_input(arg_name="products",
                        command_text="SELECT * FROM dbo.navien_demo WHERE id = @Id",
                        command_type="Text",
                        parameters="@Id={id}",
                        connection_string_setting="SqlConnectionString")
def get_products(req: func.HttpRequest, products: func.SqlRowList) -> func.HttpResponse:
    rows = list(map(lambda r: json.loads(r.to_json()), products))

    return CustomJSONResponse(
        body=rows,
        status_code=200
    )

####################################################################################################################################
# JSON schema test(Select)
####################################################################################################################################
@app.function_name(name="API_DEMO_06_SELECT_LIST")
@app.route(route="navien-test/{val1}/{val2}")
@app.sql_input(arg_name="products",
                        command_text="SELECT * FROM dbo.navien_demo WHERE title = @Title AND completed = @Complated",
                        command_type="Text",
                        parameters="@Title={val1},@Complated={val2}",
                        connection_string_setting="SqlConnectionString")
def get_products2(req: func.HttpRequest, products: func.SqlRowList) -> CustomJSONResponse:
    rows = list(map(lambda r: json.loads(r.to_json()), products))

    return CustomJSONResponse(
        body=rows,
        status_code=200
    )


####################################################################################################################################
# Delete all
####################################################################################################################################
# @app.function_name(name="DeleteNavien")
# @app.route(route="navien-test", methods=['DELETE'])
# # (sql_query="DELETE FROM dbo.navien_demo",
# #         connection_string_setting="SqlConnectionString")
# # def deleteNavienData(req: func.HttpRequest, item: func.Out) -> CustomJSONResponse:
    
# #     return CustomJSONResponse(
# #         body='',
# #         status_code=200
# #     )
# def main(req: func.HttpRequest, output: func.Out[func.SQL]):
#     # 쿼리를 지정하여 SQL 데이터베이스에서 데이터를 가져옵니다.
#     output.set("DELETE FROM dbo.navien_demo")
