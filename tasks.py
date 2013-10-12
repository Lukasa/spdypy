# -*- coding: utf-8 -*-
from invoke import task, run

@task
def test():
    run('py.test --cov-report term-missing --cov spdypy test/', pty=True)
