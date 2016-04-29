.. _serializers:

Serializers
===========

You can customize the serialization to and from Stores in Pootle.

This allows you to make formatting or other changes before saving to disk, and
conversely you can make changes to files before importing into Pootle.

Serializers and deserializers defined in plugins can be configured projects. See the
`django-admin`:"project_serializers" command for more information on configuring project
serializers.

This document explains how to write custom serializers and deserializers in a Pootle
plugin application.


.. _serializers#custom-serializer:

Adding a custom serializer
--------------------------

Lets add a `CustomSerializer` in a file called `serializers.py`.

The serializer class will be called with 2 arguments, `store`, and
`original_data`.

The original data is a bare representation of the Store according to the `Project`'s
`localfiletype`, unless the data has already been through another serialization filter
already.

The serializer class should implement a property called `output`, which should
return the modified data. Out from a serializer class should be parseable
by ttk.

In this example, we strip whitespace from the original data, but only if the
Store being serialized has an odd-numbered id.

Serializers can make minor formatting changes, or they can change the structure
of the document. If the content is changed in such a way that ttk will parse
the result differently, then a matching deserializer will likely be required.

.. code-block:: python

   from pootle_store.store.serialize import StoreSerializer


   class CustomSerializer(StoreSerializer):

       @property
       def output(self):
           if self.store.id % 2:
               return self.original_data.strip()
           return self.original_data


.. _serializers#custom-deserializer:

Adding a custom deserializer
----------------------------

Lets add a `CustomDeserializer` in a file called `deserializers.py`.

The deserializer class will be called with 2 arguments, `store`, and
`original_data`.

The deserializer class should implement a property called `output`, which should
return the modified data. Output from a deserializer class should be parseable
by ttk.

In this example, we add whitespace to the original data, but only if the
Store being serialized has an odd-numbered id.

Deserializers can make minor formatting changes, or they can change the structure
of the document. If the content is changed in such a way that ttk will parse
the result differently, then a matching serializer will likely be required.

.. code-block:: python

   from pootle_store.store.serialize import StoreSerializer


   class CustomSerializer(StoreSerializer):

       @property
       def output(self):
           if self.store.id % 2:
               return " %s " % self.original_data
           return self.original_data



.. _serializers#serializer-providers:

Add a provider file to enable your serializers
----------------------------------------------

To enable serializers you will need to add a provider function
for `pootle.core.delegate.serializers`.

If necessary, add a file called `providers.py`. To enable our CustomSerializer
we will need something like the following in the providers file

Serializers are named, and the provider function should return
a dictionary of serializer classes, using the serializer names
as the dictionary keys.


.. code-block:: python

   from pootle.core.delegate import serializers
   from pootle.core.plugin import provider

   from pootle_custom.serializers import CustomSerializer

   
   @provider(serializers, sender=Store)
   def provide_serializers(**kwargs):
       return dict(custom_serializer=CustomSerializer)

See here for further information about 


.. _serializers#deserializer-providers:

Enabling your deserializers
---------------------------

To enable deserializers you will need to add a provider function
for `pootle.core.delegate.deserializers`.

Deserializers are named, and the provider function should return
a dictionary of deserializer classes, using the deserializer names
as the dictionary keys.

If necessary, add a file called `providers.py`. To enable our CustomSerializer
we will need something like the following in the providers file


.. code-block:: python

   from pootle.core.delegate import serializers
   from pootle.core.plugin import provider

   from pootle_custom.serializers import CustomDeserializer

   
   @provider(serializers, sender=Store)
   def provide_serializers(**kwargs):
       return dict(custom_deserializer=CustomDeserializer)
