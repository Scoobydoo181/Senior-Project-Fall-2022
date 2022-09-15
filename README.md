# Senior-Project-Fall-2022

**By Christopher Wilson, Zach Cowan, and Nalin Mehra**

## Overview

The goal of this project is to use machine learning and a webcam to make gaze tracking software that moves the mouse across the screen follwing the user's eyes. The user should also be able to click the mouse by blinking.

## Usage

### Local Development

#### Running the Program

> Note: we have opted to use pipenv for its simplicity and consistency. Pipenv creates a virtual environment with all of the dependencies installed in that environment. To get IDE suggestions and autocomplete, you will have to point your editor to the pipenv virtual environment created for the project. For more information about pipenv, see their [website](https://pipenv.pypa.io/en/latest/).

1. Make sure you are on Python `v3.7.13`.
2. Install our dependency & virtual environment manager by running `pip install pipenv` or `pip3 install pipenv`.
3. To install project dependencies, run `pipenv install` in the project's root directory.
4. To run the project with the installed dependencies, run `pipenv run python FILE_NAME.py`.

#### Installing Dependencies

Installing dependencies with pipenv works almost identically to pip. Instead of running `pip install package-name`, simply run `pipenv install package-name`. This will install the dependency in the virtual environment created by pipenv and keep track of it in the `Pipfile` and `Pipfile.lock`.
