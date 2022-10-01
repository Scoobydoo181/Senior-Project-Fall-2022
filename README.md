# Senior-Project-Fall-2022

**By Christopher Wilson, Zach Cowan, and Nalin Mehra**

## Overview

The goal of this project is to use machine learning and a webcam to make gaze tracking software that moves the mouse across the screen follwing the user's eyes. The user should also be able to click the mouse by blinking.

## Usage

### Local Development

#### Running the Program

> Note: we have opted to use peotry as our dependency manager for its simplicity and consistency. Poetry creates a virtual environment with all of the dependencies installed in that environment. To get IDE suggestions and autocomplete, you will have to point your editor to the poetry virtual environment created for the project. For more information about poetry, see their [website](https://python-poetry.org/).

1. Make sure you are on Python `v3.9.13`.
2. Make sure `pip` is up-to-date by running `pip install --upgrade pip`.
3. Install our dependency & virtual environment manager poetry by running `pip install poetry`.
4. To install project dependencies, run `poetry install` in the project's root directory.
5. To run the project with the installed dependencies, run `poetry run python IrisSoftware/main.py`.

#### Installing Dependencies

Installing dependencies with poetry works almost identically to pip. Instead of running `pip install package-name`, simply run `poetry add package-name`. This will install the dependency in the virtual environment created by pipenv and keep track of it in the `pyproject.toml` and `poetry.lock`. For more info on installing dependencies, see [their website](https://python-poetry.org/docs/cli/#add).
