from alembic import context
from app.core.config import Settings
from app.db.models import Base
from app.db.session import Database

config = context.config
target_metadata = Base.metadata


def run():
    supplied = config.attributes.get("connection")
    if supplied is not None:
        context.configure(connection=supplied, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    db = Database(Settings().resolved_database_url)
    with db.engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
    db.engine.dispose()


run()
