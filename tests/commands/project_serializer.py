# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError

from pootle.core.delegate import serializers, deserializers
from pootle.core.plugin import provider
from pootle_project.models import Project
from pootle_store.models import Store


class EGSerializer1(object):
    pass


class EGSerializer2(object):
    pass


class EGDeserializer1(object):
    pass


class EGDeserializer2(object):
    pass


def serializer_provider_factory():

    @provider(serializers)
    def serializer_provider(**kwargs):
        return OrderedDict(
            (("serializer1", EGSerializer1),
             ("serializer2", EGSerializer2)))
    return serializer_provider


def deserializer_provider_factory():

    @provider(deserializers)
    def deserializer_provider(**kwargs):
        return OrderedDict(
            (("deserializer1", EGDeserializer1),
             ("deserializer2", EGDeserializer2)))
    return deserializer_provider


def _test_serializer_list(out, err):
    NO_SERIALS = "There are no serializers set up on your system"
    NO_DESERIALS = "There are no deserializers set up on your system"

    serials = serializers.gather(Store)
    deserials = deserializers.gather(Store)

    expected = []

    if not serials.keys():
        expected.append(NO_SERIALS)
    if not deserials.keys():
        expected.append(NO_DESERIALS)

    if serials.keys():
        heading = "Serializers"
        expected.append("\n%s" % heading)
        expected.append("-" * len(heading))
        for name, klass in serials.items():
            expected.append("{: <30} {: <25} ".format(name, klass))

    if deserials.keys():
        heading = "Deserializers"
        expected.append("\n%s" % heading)
        expected.append("-" * len(heading))
        for name, klass in deserials.items():
            expected.append("{: <30} {: <25} ".format(name, klass))

    assert out == "%s\n" % ("\n".join(expected))


def _test_all_project_serializers(out, err):
    project_values = Project.objects.exclude(disabled=True).values(
        "fullname", "code", "localfiletype",
        "serializers", "deserializers")
    expected = []
    for project in project_values:
        expected.append("Project: %s(%s)" % (project['fullname'], project['code']))
        expected.append("  local filetype: %s" % project["localfiletype"])
        expected.append("  serializers: %s" % (project["serializers"] or ""))
        expected.append("  deserializers: %s" % (project["deserializers"] or ""))
    assert out == "%s\n" % ("\n".join(expected))


def _test_project_serializers(project, out, err):
    expected = []
    expected.append("Project: %s(%s)" % (project.fullname, project.code))
    expected.append("  local filetype: %s" % project.localfiletype)
    expected.append("  serializers: %s" % (project.serializers or ""))
    expected.append("  deserializers: %s" % (project.deserializers or ""))
    assert out == "%s\n" % ("\n".join(expected))


def _test_clear_project_deserializers(project, out, err):
    assert project.deserializers in (None, "")
    assert not err
    expected = (
        'Project deserializers cleared: %s\n'
        % project.code)
    assert out == expected


def _test_clear_project_serializers(project, out, err):
    assert project.serializers in (None, "")
    assert not err
    expected = (
        'Project serializers cleared: %s\n'
        % project.code)
    assert out == expected


def _test_set_project_deserializers(project, deserialstr, out, err):
    assert project.deserializers == deserialstr
    assert not err
    expected = (
        'Project deserializers set: %s %s\n'
        % (project.code, project.deserializers))
    assert out == expected


def _test_set_project_serializers(project, serialstr, out, err):
    assert project.serializers == serialstr
    assert not err
    expected = (
        'Project serializers set: %s %s\n'
        % (project.code, project.serializers))
    assert out == expected


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_all_project_serializers(capfd):
    call_command("project_serializers")
    out, err = capfd.readouterr()
    _test_all_project_serializers(out, err)

    # setup some de/serializers, but dont add to any projects
    serial_provider = serializer_provider_factory()
    deserial_provider = deserializer_provider_factory()
    call_command("project_serializers")
    out, err = capfd.readouterr()
    _test_all_project_serializers(out, err)

    # add de/serializers to a project
    project0 = Project.objects.get(code="project0")
    project0.serializers = "serializer1,serializer2"
    project0.deserializers = "deserializer1,deserializer2"
    project0.save()
    call_command("project_serializers")
    out, err = capfd.readouterr()
    _test_all_project_serializers(out, err)

    # disconnect deserializers
    serializers.disconnect(serial_provider)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers(capfd):
    project0 = Project.objects.get(code="project0")

    call_command("project_serializers", project0.code)
    out, err = capfd.readouterr()
    _test_project_serializers(project0, out, err)

    # setup some de/serializers, but dont add to any projects
    serial_provider = serializer_provider_factory()
    deserial_provider = deserializer_provider_factory()
    call_command("project_serializers", project0.code)
    out, err = capfd.readouterr()
    _test_project_serializers(project0, out, err)

    # add de/serializers to a project
    project0.serializers = "serializer1,serializer2"
    project0.deserializers = "deserializer1,deserializer2"
    project0.save()
    call_command("project_serializers", project0.code)
    out, err = capfd.readouterr()
    _test_project_serializers(project0, out, err)

    # disconnect deserializers
    serializers.disconnect(serial_provider)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers_list(capsys):

    # tests with no de/serializers set up
    call_command("project_serializers", "--list")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    # set up some serializers
    serial_provider = serializer_provider_factory()
    call_command("project_serializers", "--list")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    serializers.disconnect(serial_provider)

    # set up some deserializers
    deserial_provider = deserializer_provider_factory()
    call_command("project_serializers", "--list")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    # empty again
    deserializers.disconnect(deserial_provider)
    call_command("project_serializers", "--list")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)

    # with both set up
    deserial_provider = deserializer_provider_factory()
    serial_provider = serializer_provider_factory()
    call_command("project_serializers", "--list")
    out, err = capsys.readouterr()
    _test_serializer_list(out, err)
    serializers.disconnect(serial_provider)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers_bad_no_project(capsys):
    serial_provider = serializer_provider_factory()
    deserial_provider = deserializer_provider_factory()

    # must set a project with --set --clear commands
    for command in ("--clear-serializers", "--clear-deserializers"):
        with pytest.raises(CommandError):
            call_command("project_serializers", command)

    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            "--set-serializers",
            "serializer1,serializer2")

    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            "--set-deserializers",
            "deserializer1,deserializer2")
    serializers.disconnect(serial_provider)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers_bad_project(capsys):
    serial_provider = serializer_provider_factory()
    deserial_provider = deserializer_provider_factory()

    bad_project = "PROJECT_DOES_NOT_EXIST"

    # must set a project with --set --clear commands
    for command in ("--clear-serializers", "--clear-deserializers"):
        with pytest.raises(CommandError):
            call_command(
                "project_serializers",
                bad_project,
                command)

    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            bad_project,
            "--set-serializers",
            "serializer1,serializer2")

    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            bad_project,
            "--set-deserializers",
            "deserializer1,deserializer2")
    serializers.disconnect(serial_provider)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers_bad_set_serializers(capsys):
    project0 = Project.objects.get(code="project0")

    # set-serializers needs an argument
    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            project0.code,
            "--set-serializers")

    # unrecognised serializers
    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            project0.code,
            "--set-serializers",
            "foo,bar")

    serial_provider = serializer_provider_factory()
    # unrecognised serializers, with some good
    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            project0.code,
            "--set-serializers",
            "serializer1,serializer2,foo,bar")
    serializers.disconnect(serial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers_bad_set_deserializers(capsys):
    project0 = Project.objects.get(code="project0")

    # set-deserializers needs an argument
    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            project0.code,
            "--set-deserializers")

    # unrecognised deserializers
    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            project0.code,
            "--set-deserializers",
            "foo,bar")

    deserial_provider = deserializer_provider_factory()
    # unrecognised deserializers, with some good
    with pytest.raises(CommandError):
        call_command(
            "project_serializers",
            project0.code,
            "--set-deserializers",
            "deserializer1,deserializer2,foo,bar")
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers_set_serializers(capsys):
    project0 = Project.objects.get(code="project0")

    serial_provider = serializer_provider_factory()
    serialstr = "serializer1,serializer2"
    call_command(
        "project_serializers",
        project0.code,
        "--set-serializers",
        serialstr)
    out, err = capsys.readouterr()
    project0 = Project.objects.get(code="project0")
    _test_set_project_serializers(
        project0, serialstr, out, err)

    # swap the pipeline around
    serialstr = "serializer2,serializer1"
    call_command(
        "project_serializers",
        project0.code,
        "--set-serializers",
        serialstr)
    out, err = capsys.readouterr()
    project0 = Project.objects.get(code="project0")
    _test_set_project_serializers(
        project0, serialstr, out, err)
    serializers.disconnect(serial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers_set_deserializers(capsys):
    project0 = Project.objects.get(code="project0")

    deserial_provider = deserializer_provider_factory()
    deserialstr = "deserializer1,deserializer2"
    call_command(
        "project_serializers",
        project0.code,
        "--set-deserializers",
        deserialstr)
    out, err = capsys.readouterr()
    project0 = Project.objects.get(code="project0")
    _test_set_project_deserializers(
        project0, deserialstr, out, err)

    # swap the pipeline around
    deserialstr = "deserializer2,deserializer1"
    call_command(
        "project_serializers",
        project0.code,
        "--set-deserializers",
        deserialstr)
    out, err = capsys.readouterr()
    project0 = Project.objects.get(code="project0")
    _test_set_project_deserializers(
        project0, deserialstr, out, err)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers_clear_deserializers(capsys):
    project0 = Project.objects.get(code="project0")

    # no deserializers set up, but thats ok
    call_command(
        "project_serializers",
        project0.code,
        "--clear-deserializers")
    out, err = capsys.readouterr()
    project0 = Project.objects.get(code="project0")
    _test_clear_project_deserializers(
        project0, out, err)

    deserial_provider = deserializer_provider_factory()
    project0.deserializers = "deserializer1,deserializer2"
    project0.save()
    call_command(
        "project_serializers",
        project0.code,
        "--clear-deserializers")
    out, err = capsys.readouterr()
    project0 = Project.objects.get(code="project0")
    _test_clear_project_deserializers(
        project0, out, err)
    deserializers.disconnect(deserial_provider)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_project_serializers_clear_serializers(capsys):
    project0 = Project.objects.get(code="project0")

    # no serializers set up, but thats ok
    call_command(
        "project_serializers",
        project0.code,
        "--clear-serializers")
    out, err = capsys.readouterr()
    project0 = Project.objects.get(code="project0")
    _test_clear_project_serializers(
        project0, out, err)

    serial_provider = serializer_provider_factory()
    project0.serializers = "serializer1,serializer2"
    project0.save()
    call_command(
        "project_serializers",
        project0.code,
        "--clear-serializers")
    out, err = capsys.readouterr()
    project0 = Project.objects.get(code="project0")
    _test_clear_project_serializers(
        project0, out, err)
    serializers.disconnect(serial_provider)
