
from sqlalchemy import text
from database import get_engine

with get_engine().connect() as connection:
    result = connection.execute(
        text("SELECT COUNT(*) FROM tickets")
    )
    print("Total tickets:", result.scalar())
