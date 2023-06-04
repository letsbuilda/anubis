<#
.SYNOPSIS
Testing using PowerShell to replace my Makefile

.DESCRIPTION
USAGE
    .\make.ps1 <command>

COMMANDS
    init              install Python build tools
    install           install local package in production mode
    install-dev       install local package in editable mode
    lint              run `isort` and `black`
    pylint            run `pylint`
    test              run `pytest`
    build-dist        run `python -m build`
    clean             delete generated content
    help, -?          show this help message
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet("init", "install", "install-dev", "update-deps", "lint", "pylint", "test", "build-dist", "clean", "help")]
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

function Invoke-Install
{
    python -m pip install --upgrade .
}

function Invoke-Install-Dev
{
    python -m pip install --upgrade --editable ".[dev, tests, docs]"
}

function Invoke-Update-Deps
{
    python -m pip install --upgrade pip-tools
    pip-compile --resolver=backtracking requirements.in --output-file requirements.txt
    pip-compile --resolver=backtracking requirements-dev.in --output-file requirements-dev.txt
    pip-compile --resolver=backtracking requirements-tests.in --output-file requirements-tests.txt
    pip-compile --resolver=backtracking requirements-docs.in --output-file requirements-docs.txt
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
    "install"  {
        Invoke-Install
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
