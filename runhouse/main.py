from typing import Optional

import pkg_resources
import typer
import webbrowser
from rich.console import Console

from runhouse import rh_config
from runhouse.rns import login as login_module  # Need to rename it because it conflicts with the login command

# create an explicit Typer application
app = typer.Typer(add_completion=False)
state = {"verbose": False}

# For printing with typer
console = Console()


@app.command()
def login(token: Optional[str] = typer.Argument(None, help="Your Runhouse API token")):
    """Login to Runhouse. Validates token provided, with options to upload or download stored secrets or config between
    local environment and Runhouse / Vault.
    """
    if not token:
        console.print(f'Retrieve your token :key: to use :person_running: :house: '
                      f'for secrets and artifact management: {rh_config.configs.get("api_server_url")}',
                      style='bold yellow')
        token = typer.prompt("Token", type=str)

    download_config = typer.confirm('Download config from Runhouse to your local .rh folder?')
    upload_config = typer.confirm('Upload your local config to Runhouse?')
    download_secrets = typer.confirm('Download secrets from Vault to your local Runhouse config?')
    upload_secrets = typer.confirm('Upload your enabled cloud provider secrets to Vault?')

    valid_token: str = login_module.login(token=token,
                                          download_config=download_config,
                                          upload_config=upload_config,
                                          upload_secrets=upload_secrets,
                                          download_secrets=download_secrets,
                                          ret_token=True)
    if valid_token:
        webbrowser.open(f"{rh_config.configs.get('api_server_url')}/dashboard?token={valid_token}")
        raise typer.Exit()
    else:
        raise typer.Exit(code=1)


@app.callback()
def main(verbose: bool = False):
    """
    Runhouse CLI app. Currently we support login, but more on the way :)
    """
    if verbose:
        name = 'runhouse'
        version = pkg_resources.get_distribution(name).version
        console.print(f"{name}=={version}", style="bold green")
        state["verbose"] = True