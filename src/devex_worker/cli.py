import click
from services.application_service import ApplicationService
from worker_daemon import WorkerDaemon
from session import Session

API_BASE_URL = "http://localhost:8000/api"


@click.command()
def run_as_daemon():
    """Worker Daemon for Resource Management"""
    WorkerDaemon.start()


@click.command()
@click.option("-u", "--username", required=False, type=str)
@click.option("-e", "--url", default=API_BASE_URL, required=True, type=str)
def login(username, url):
    """Login to the API and save token"""

    if username is None:
        username = click.prompt("Username", type=str)

    password = click.prompt("Password", type=str, hide_input=True)
    session = Session(url)
    session.login(username, password)
    session.save_token()


@click.command()
@click.option("-a", "--application", type=click.Path(exists=True), required=True)
@click.option("-c", "--configuration", type=click.Path(exists=True), required=True)
@click.option("--plan", is_flag=True, default=False)
def deploy(application, configuration, plan):
    """Deploy an application"""
    worker = WorkerDaemon(
        application_file=application,
        configuration_file=configuration,
    )
    worker.run(plan_only=plan)


@click.group()
def cli():
    pass


@click.group()
def applications():
    """Manage applications"""
    pass


@click.command()
def list():
    """List all applications"""
    api = ApplicationService(session=Session.load_session())
    applications = api.get_applications()
    if applications:
        for app in applications:
            click.echo(f"Name: {app['name']}, Version: {app['version']}")
    else:
        click.echo("No applications found.")


applications.add_command(list)
cli.add_command(run_as_daemon)
cli.add_command(login)
cli.add_command(deploy)
cli.add_command(applications)


if __name__ == "__main__":
    cli()
