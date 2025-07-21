import click
import app.models
from app.db.session import engine, Base

@click.group()
def cli():
    """Database management commands."""
    pass

@cli.command()
def create():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    click.echo("Created database tables.")

@cli.command()
def drop():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)
    click.echo("Dropped database tables.")

if __name__ == '__main__':
    cli()