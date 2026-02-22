import schemathesis
from app.main import app

schema = schemathesis.from_dict(app.openapi())


@schema.parametrize()
def test_api_contract(case):
    response = case.call_asgi(app)
    case.validate_response(response)
