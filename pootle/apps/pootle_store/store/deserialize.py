# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import io

from translate.storage.factory import getclass

from django.utils.functional import cached_property

from pootle.core.delegate import deserializers


class StoreDeserializer(object):

    def __init__(self, store):
        self.store = store

    @property
    def project_deserializers(self):
        proj_deserializers = (
            self.store.translation_project.project.deserializers
            or "")
        return [
            s.strip()
            for s
            in proj_deserializers.split(",")
            if s]

    @cached_property
    def deserializers(self):
        available_deserializers = deserializers.gather(
            self.store.__class__, instance=self.store)
        found_deserializers = []
        for deserializer in self.project_deserializers:
            found_deserializers.append(available_deserializers[deserializer])
        return found_deserializers

    def pipeline(self, data):
        if not self.deserializers:
            return data
        for deserializer in self.deserializers:
            data = deserializer(self, data).output
        return data

    def fromstring(self, data):
        return getclass(io.StringIO(data))(data.encode("utf8"))

    def deserialize(self, data):
        return self.fromstring(self.pipeline(data.decode("utf8")))
