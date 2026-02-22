import schemathesis
from app.main import app
from app.db.base import Base
from app.db.session import engine
Base.metadata.create_all(bind=engine)

schema = schemathesis.from_dict(app.openapi())


@schema.parametrize()
def test_api_contract(case):
    response = case.call_asgi(app)
    case.validate_response(response)
