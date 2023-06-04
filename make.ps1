<#
.SYNOPSIS
Testing using PowerShell to replace my Makefile

.DESCRIPTION
USAGE
    .\make.ps1 <command>

COMMANDS
    init              install Python build tools
    install-dev       install local package in editable mode
    update-deps       update the dependencies
    upgrade-deps      upgrade the dependencies
    lint              run `isort` and `black`
    pylint            run `pylint`
    test              run `pytest`
    build-dist        run `python -m build`
    clean             delete generated content
    help, -?          show this help message
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet("init", "install-dev", "update-deps", "upgrade-deps", "lint", "pylint", "test", "build-dist", "clean", "help")]
    [string]$Command
)

function Invoke-Help
{
    Get-Help $PSCommandPath
}

function Invoke-Init
{
    python -m pip install --upgrade pip wheel setuptools build
}

function Invoke-Install-Dev
{
    python -m pip install --upgrade --editable ".[dev, tests, docs]"
}

function Invoke-Update-Deps
{
    python -m pip install --upgrade pip-tools
    pip-compile --output-file requirements.txt --resolver=backtracking requirements.in
    pip-compile --output-file requirements-dev.txt --resolver=backtracking requirements-dev.in
    pip-compile --output-file requirements-tests.txt --resolver=backtracking requirements-tests.in
    pip-compile --output-file requirements-docs.txt --resolver=backtracking requirements-docs.in
}

function Invoke-Upgrade-Deps
{
    python -m pip install --upgrade pip-tools
    pip-compile --output-file requirements.txt --resolver=backtracking --upgrade requirements.in
    pip-compile --output-file requirements-dev.txt --resolver=backtracking --upgrade requirements-dev.in
    pip-compile --output-file requirements-tests.txt --resolver=backtracking --upgrade requirements-tests.in
    pip-compile --output-file requirements-docs.txt --resolver=backtracking --upgrade requirements-docs.in
}

function Invoke-Lint
{
    python -m isort src/
    python -m black src/
}

function Invoke-Pylint
{
    python -m pylint src/
}

function Invoke-Test
{
    python -m pytest
}

function Invoke-Build-Dist
{
    python -m pip install --upgrade build
    python -m build
}

function Invoke-Clean
{
    $folders = @("build", "dist")
    foreach ($folder in $folders)
    {
        if (Test-Path $folder)
        {

            Write-Verbose "Deleting $folder"
            Remove-Item $folder -Recurse -Force
        }
    }
}

switch ($Command)
{
    "init"    {
        Invoke-Init
    }
    "install-dev" {
        Invoke-Install-Dev
    }
    "lint"  {
        Invoke-Lint
    }
    "update-deps"  {
        Invoke-Update-Deps
    }
    "upgrade-deps"  {
        Invoke-Upgrade-Deps
    }
    "pylint"    {
        Invoke-Pylint
    }
    "test"    {
        Invoke-Test
    }
    "build-dist"    {
        Invoke-Build-Dist
    }
    "clean"    {
        Invoke-Clean
    }
    "help"  {
        Invoke-Help
    }
    default
    {
        Invoke-Init
        Invoke-Install-Dev
    }
}
