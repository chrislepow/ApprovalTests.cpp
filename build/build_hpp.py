#! /usr/bin/env python3

# Constants
import os
import subprocess
import shutil

UNSET_VERSION="v.X.X.X"

LAST_VERSION="v.7.0.0"
VERSION=UNSET_VERSION

PUSH_TO_PRODUCTION=True
# Note that we won't push if the version number is unset

OLD_SINGLE_HEADER=F"ApprovalTests.{LAST_VERSION}.hpp"
NEW_SINGLE_HEADER=F"ApprovalTests.{VERSION}.hpp"
NEW_SINGLE_HEADER_TEMP=F"{NEW_SINGLE_HEADER}.tmp"

RELEASE_DIR=F"../build/releases"
RELEASE_NEW_SINGLE_HEADER=F"{RELEASE_DIR}/{NEW_SINGLE_HEADER}"
RELEASE_NEW_SINGLE_HEADER_TEMP=F"{RELEASE_DIR}/{NEW_SINGLE_HEADER_TEMP}"

STARTER_PROJECT_DIR=F"../../ApprovalTests.Cpp.StarterProject"
STARTER_PATH_OLD_SINGLE_HEADER=F"{STARTER_PROJECT_DIR}/lib/{OLD_SINGLE_HEADER}"
STARTER_PATH_NEW_SINGLE_HEADER=F"{STARTER_PROJECT_DIR}/lib/{NEW_SINGLE_HEADER}"

# TODO copy in checks from https://github.com/pages-themes/minimal/blob/master/script/release


def create_single_header_file():
    # TODO Rework to not write tmp file
    os.chdir("../ApprovalTests")
    subprocess.call(["java", "-jar", "../build/SingleHpp.v.0.0.2.jar", RELEASE_NEW_SINGLE_HEADER_TEMP], shell=True)
    text = read_file(RELEASE_NEW_SINGLE_HEADER_TEMP)
    text = F"""
// Approval Tests version {VERSION}
// More information at: https://github.com/approvals/ApprovalTests.cpp

{text}
"""
    write_file(RELEASE_NEW_SINGLE_HEADER, text)


def write_file(file_name, text):
    with open(file_name, 'w') as output:
        output.write(text)


def read_file(file_name):
    with open(file_name) as input:
        text = input.read()
    return text


# ------------------------------------------------------------------------------------------------
# Update Starter Project

# https://stackoverflow.com/a/10528259/104370
# initialise a directory stack
pushstack = list()

def pushdir(dirname):
  global pushstack
  pushstack.append(os.getcwd())
  os.chdir(dirname)

def popdir():
  global pushstack
  os.chdir(pushstack.pop())

def update_starter_project():

    # Make sure starter project folder is clean
    pushdir(STARTER_PROJECT_DIR)
    subprocess.call(["git", "clean", "-fx"], shell=True)
    subprocess.call(["git", "reset", "--hard"], shell=True)
    popdir()

    shutil.copyfile(RELEASE_NEW_SINGLE_HEADER, STARTER_PATH_NEW_SINGLE_HEADER)

    # Delete the last release:
    if os.path.exists(STARTER_PATH_OLD_SINGLE_HEADER):
        os.remove(STARTER_PATH_OLD_SINGLE_HEADER)

    # Update the version in the "redirect" header:
    replace_text_in_file(F"{STARTER_PROJECT_DIR}/lib/ApprovalTests.hpp", VERSION, LAST_VERSION)

    # Update the version number in the Visual Studio project:
    replace_text_in_file(F"{STARTER_PROJECT_DIR}/visual-studio-2017/StarterProject.vcxproj", OLD_SINGLE_HEADER, NEW_SINGLE_HEADER)


def replace_text_in_file(file_name, new_text, old_text):
    text = read_file(file_name)
    text.replace(old_text, new_text)
    write_file(file_name, text)


def check_starter_project_builds():
    pushdir(F"{STARTER_PROJECT_DIR}/cmake-build-debug")
    subprocess.call(["cmake", "--build", "."], shell=True)
    popdir()

    if VERSION == UNSET_VERSION:
        print("Everything worked - version number not set, so didn't commit or push")
        exit(0)

    if not PUSH_TO_PRODUCTION:
        # Don't push to production if we haven't set the version number
        print("Everything worked - didn't commit or push")
        exit(0)


def commit_and_push_starter_project():
    pushdir(STARTER_PROJECT_DIR)
    subprocess.call(["git", "add", "."], shell=True)
    subprocess.call(["git", "commit", "-m", "Update to Approvals " + str(VERSION.val)], shell=True)
    subprocess.call(["git", "push", "origin", "master"], shell=True)
    popdir()


def update_readme_and_docs():
    pushdir("..")
    replace_text_in_file("mdsource/README.source.md", LAST_VERSION, VERSION)
    subprocess.call(["./run_markdown_templates.sh"],shell=True)
    popdir()


def publish():
    # Draft the tweet
    tweet_text = F"https://twitter.com/intent/tweet?text=%23ApprovalTests.cpp+{VERSION}+released%2C+now+with+___%21%0D%0Ahttps%3A%2F%2Fgithub.com%2Fapprovals%2FApprovalTests.cpp%2Freleases%2Ftag%2F{VERSION}+%0D%0Aor+try+the+starter+project%3A+https%3A%2F%2Fgithub.com%2Fapprovals%2FApprovalTests.cpp.StarterProject%0D%0AThanks+%40LlewellynFalco+%40ClareMacraeUK+%21"
    subprocess.call(["open", tweet_text], shell=True)

    # Draft the upload to github - do this last, so this tab appears on top
    github_url = F"https://github.com/approvals/ApprovalTests.cpp/releases/new?tag={VERSION}&title=Single%20Hpp%20File%20-%20{VERSION}"
    subprocess.call(["open", github_url], shell=True)

    subprocess.call(["open", RELEASE_DIR], shell=True)


def build_hpp():
    create_single_header_file()
    update_starter_project()
    check_starter_project_builds()
    commit_and_push_starter_project()
    update_readme_and_docs()
    publish()


if __name__ == '__main__':
    build_hpp()