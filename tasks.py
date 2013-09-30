# -*- coding: utf-8 -*-
from invoke import task, run

@task
def test():
    run('py.test --cov-report term --cov spdypy test/', pty=True)
