import click
from applications_api import ApplicationsAPI
from worker import WorkerDaemon
from session import Session

API_BASE_URL = "http://localhost:8000/api"


@click.command()
@click.argument("yaml_file", type=click.Path(exists=True))
def run_worker(yaml_file):
    """Worker Daemon for Resource Management"""
    daemon = WorkerDaemon(yaml_file)
    daemon.run()


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
    api = ApplicationsAPI(session=Session.load_session())
    applications = api.get_applications()
    if applications:
        for app in applications:
            click.echo(f"Name: {app['name']}, Version: {app['version']}")
    else:
        click.echo("No applications found.")


@click.command()
@click.argument("application_name")
def deploy(application_name):
    """Deploy an application"""
    api = ApplicationsAPI(session=Session.load_session())
    applications = api.get_applications()
    app_id = next((app["id"] for app in applications if app["name"] == application_name), None)

    if app_id:
        response = api.get_application(app_id)
        if response:
            click.echo(f"Deploying application: {application_name} (ID: {app_id})")
            app_definition = response.get("definition")
            if app_definition:
                worker = WorkerDaemon(app_definition)
                worker.run()
        else:
            click.echo("Application not found.")
    else:
        click.echo("Application not found.")


applications.add_command(list)
applications.add_command(deploy)
cli.add_command(run_worker)
cli.add_command(login)
cli.add_command(applications)

if __name__ == "__main__":
    cli()
